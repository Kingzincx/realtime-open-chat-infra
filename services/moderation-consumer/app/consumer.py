import asyncio
import json
import logging

from aiokafka import AIOKafkaConsumer, TopicPartition
from pydantic import ValidationError

from .config import settings
from .database import persist_alerts
from .metrics import (
    MODERATION_ALERTS_CREATED_TOTAL,
    MODERATION_CONSUMER_ERRORS_TOTAL,
    MODERATION_CONSUMER_KAFKA_LAG,
    MODERATION_DUPLICATE_ALERTS_TOTAL,
    MODERATION_EVENTS_CONSUMED_TOTAL,
    MODERATION_EVENTS_SKIPPED_TOTAL,
    MODERATION_INVALID_EVENTS_TOTAL,
    MODERATION_MESSAGES_FLAGGED_TOTAL,
)
from .moderation import ModerationRules, ModerationState
from .schemas import ChatEvent, MessageSentPayload

logger = logging.getLogger(__name__)


def build_moderation_state() -> ModerationState:
    return ModerationState(
        ModerationRules(
            blocked_words=settings.blocked_words,
            max_message_length=settings.max_message_length,
            duplicate_window_seconds=settings.duplicate_window_seconds,
            flood_window_seconds=settings.flood_window_seconds,
            flood_message_threshold=settings.flood_message_threshold,
        )
    )


class ModerationConsumer:
    def __init__(self) -> None:
        self._consumer: AIOKafkaConsumer | None = None
        self._task: asyncio.Task | None = None
        self._state = build_moderation_state()

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
            "Started moderation consumer topic=%s group=%s",
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

        logger.info("Stopped moderation consumer")

    async def _consume_loop(self) -> None:
        if self._consumer is None:
            raise RuntimeError("Kafka consumer is not initialized")

        async for message in self._consumer:
            event = self._parse_event(message.value)
            if event is None:
                MODERATION_INVALID_EVENTS_TOTAL.inc()
                logger.warning("Skipping invalid Kafka message")
                await self._commit()
                continue

            try:
                await self._handle_event(event)
                self._record_lag(message.topic, message.partition, message.offset)
                await self._commit()
            except ValidationError:
                MODERATION_INVALID_EVENTS_TOTAL.inc()
                logger.warning(
                    "Skipping invalid message.sent payload event_id=%s",
                    event.event_id,
                )
                await self._commit()
            except Exception:
                MODERATION_CONSUMER_ERRORS_TOTAL.inc()
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

    async def _handle_event(self, event: ChatEvent) -> None:
        if event.event_type != "message.sent":
            MODERATION_EVENTS_SKIPPED_TOTAL.labels(
                event_type=event.event_type,
            ).inc()
            return

        payload = MessageSentPayload.model_validate(event.payload)
        alerts = self._state.evaluate(event.username, payload, event.timestamp)
        MODERATION_EVENTS_CONSUMED_TOTAL.inc()

        if not alerts:
            return

        inserted_reasons = await persist_alerts(event, payload, alerts)
        if inserted_reasons:
            MODERATION_MESSAGES_FLAGGED_TOTAL.inc()

        for alert in alerts:
            if alert.reason in inserted_reasons:
                MODERATION_ALERTS_CREATED_TOTAL.labels(
                    reason=alert.reason,
                    severity=alert.severity,
                ).inc()
            else:
                MODERATION_DUPLICATE_ALERTS_TOTAL.labels(
                    reason=alert.reason,
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
        MODERATION_CONSUMER_KAFKA_LAG.labels(
            topic=topic,
            partition=str(partition),
        ).set(lag)


moderation_consumer = ModerationConsumer()
