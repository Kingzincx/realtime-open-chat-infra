import asyncio
import json
import logging

from aiokafka import AIOKafkaConsumer, TopicPartition
from pydantic import ValidationError

from .config import settings
from .database import persist_message
from .metrics import (
    CHAT_HISTORY_CONSUMER_ERRORS_TOTAL,
    CHAT_HISTORY_CONSUMER_KAFKA_LAG,
    CHAT_HISTORY_DUPLICATE_MESSAGES_TOTAL,
    CHAT_HISTORY_EVENTS_CONSUMED_TOTAL,
    CHAT_HISTORY_EVENTS_SKIPPED_TOTAL,
    CHAT_HISTORY_INVALID_EVENTS_TOTAL,
    CHAT_HISTORY_MESSAGES_PERSISTED_TOTAL,
)
from .schemas import ChatEvent, MessageSentPayload

logger = logging.getLogger(__name__)


class ChatHistoryConsumer:
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
            "Started chat history consumer topic=%s group=%s",
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

        logger.info("Stopped chat history consumer")

    async def _consume_loop(self) -> None:
        if self._consumer is None:
            raise RuntimeError("Kafka consumer is not initialized")

        async for message in self._consumer:
            event = self._parse_event(message.value)
            if event is None:
                CHAT_HISTORY_INVALID_EVENTS_TOTAL.inc()
                logger.warning("Skipping invalid Kafka message")
                await self._commit()
                continue

            try:
                handled = await self._handle_event(event)
                if handled:
                    self._record_lag(message.topic, message.partition, message.offset)
                await self._commit()
            except ValidationError:
                CHAT_HISTORY_INVALID_EVENTS_TOTAL.inc()
                logger.warning(
                    "Skipping invalid message.sent payload event_id=%s",
                    event.event_id,
                )
                await self._commit()
            except Exception:
                CHAT_HISTORY_CONSUMER_ERRORS_TOTAL.inc()
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

    async def _handle_event(self, event: ChatEvent) -> bool:
        if event.event_type != "message.sent":
            CHAT_HISTORY_EVENTS_SKIPPED_TOTAL.labels(
                event_type=event.event_type,
            ).inc()
            return True

        payload = MessageSentPayload.model_validate(event.payload)
        inserted = await persist_message(event, payload)
        CHAT_HISTORY_EVENTS_CONSUMED_TOTAL.inc()

        if inserted:
            CHAT_HISTORY_MESSAGES_PERSISTED_TOTAL.inc()
        else:
            CHAT_HISTORY_DUPLICATE_MESSAGES_TOTAL.inc()

        return True

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
        CHAT_HISTORY_CONSUMER_KAFKA_LAG.labels(
            topic=topic,
            partition=str(partition),
        ).set(lag)


chat_history_consumer = ChatHistoryConsumer()
