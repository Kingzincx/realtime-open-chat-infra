import asyncio
import json
import logging

from aiokafka import AIOKafkaConsumer, TopicPartition
from pydantic import ValidationError

from .config import settings
from .database import persist_chat_event
from .metrics import (
    CHAT_EVENT_CONSUMER_DB_WRITES_TOTAL,
    CHAT_EVENT_CONSUMER_DUPLICATES_TOTAL,
    CHAT_EVENT_CONSUMER_ERRORS_TOTAL,
    CHAT_EVENT_CONSUMER_INVALID_EVENTS_TOTAL,
    CHAT_EVENT_CONSUMER_KAFKA_LAG,
    CHAT_EVENTS_CONSUMED_TOTAL,
)
from .schemas import ChatEvent

logger = logging.getLogger(__name__)


class EventAuditConsumer:
    def __init__(self) -> None:
        self._consumer: AIOKafkaConsumer | None = None
        self._task: asyncio.Task | None = None

    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def start(self) -> None:
        self._consumer = AIOKafkaConsumer(
            settings.kafka_topic,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id=settings.consumer_group,
            enable_auto_commit=False,
            auto_offset_reset="earliest",
        )
        await self._consumer.start()
        self._task = asyncio.create_task(self._consume_loop())
        logger.info(
            "Started event audit consumer topic=%s group=%s",
            settings.kafka_topic,
            settings.consumer_group,
        )

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        if self._consumer is not None:
            await self._consumer.stop()
            self._consumer = None

        logger.info("Stopped event audit consumer")

    async def _consume_loop(self) -> None:
        if self._consumer is None:
            raise RuntimeError("Kafka consumer is not initialized")

        async for message in self._consumer:
            event = self._parse_event(message.value)
            if event is None:
                CHAT_EVENT_CONSUMER_INVALID_EVENTS_TOTAL.inc()
                logger.warning("Skipping invalid Kafka message")
                await self._commit()
                continue

            try:
                await self._store_event(event)
                self._record_lag(message.topic, message.partition, message.offset)
                await self._commit()
            except Exception:
                CHAT_EVENT_CONSUMER_ERRORS_TOTAL.inc()
                logger.exception(
                    "Failed to process event_id=%s event_type=%s",
                    event.event_id,
                    event.event_type,
                )
                await asyncio.sleep(2)

    def _parse_event(self, value: bytes) -> ChatEvent | None:
        try:
            raw_event = json.loads(value.decode("utf-8"))
            return ChatEvent.model_validate(raw_event)
        except (UnicodeDecodeError, json.JSONDecodeError, ValidationError):
            return None

    async def _store_event(self, event: ChatEvent) -> None:
        inserted = await persist_chat_event(event)
        CHAT_EVENTS_CONSUMED_TOTAL.labels(event_type=event.event_type).inc()

        if inserted:
            CHAT_EVENT_CONSUMER_DB_WRITES_TOTAL.labels(
                event_type=event.event_type,
            ).inc()
            return

        CHAT_EVENT_CONSUMER_DUPLICATES_TOTAL.labels(
            event_type=event.event_type,
        ).inc()

    async def _commit(self) -> None:
        if self._consumer is not None:
            await self._consumer.commit()

    def _record_lag(self, topic: str, partition: int, offset: int) -> None:
        if self._consumer is None:
            return

        topic_partition = TopicPartition(topic, partition)
        highwater = self._consumer.highwater(topic_partition)
        if highwater is None:
            return

        lag = max(highwater - offset - 1, 0)
        CHAT_EVENT_CONSUMER_KAFKA_LAG.labels(
            topic=topic,
            partition=str(partition),
        ).set(lag)


event_consumer = EventAuditConsumer()
