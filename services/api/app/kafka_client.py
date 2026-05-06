from typing import Any
import asyncio
import json
import logging

from aiokafka import AIOKafkaProducer

from .config import settings

logger = logging.getLogger(__name__)


class ChatKafkaProducer:
    def __init__(self) -> None:
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        for attempt in range(1, 6):
            try:
                producer = AIOKafkaProducer(
                    bootstrap_servers=settings.kafka_bootstrap_servers,
                    value_serializer=lambda value: json.dumps(value).encode("utf-8"),
                    key_serializer=lambda value: value.encode("utf-8") if value else None,
                )
                await producer.start()
                self._producer = producer
                logger.info("Connected Kafka producer to %s", settings.kafka_bootstrap_servers)
                return
            except Exception:
                logger.exception("Kafka producer startup failed on attempt %s", attempt)
                await asyncio.sleep(min(attempt * 2, 10))

        logger.error("Kafka producer is disabled after repeated startup failures")

    async def stop(self) -> None:
        if self._producer is not None:
            await self._producer.stop()
            self._producer = None
            logger.info("Stopped Kafka producer")

    async def publish(self, event: dict[str, Any]) -> bool:
        if self._producer is None:
            logger.warning("Kafka producer is not available; event was not published")
            return False

        try:
            await self._producer.send_and_wait(
                settings.kafka_topic,
                event,
                key=event.get("event_type"),
            )
            return True
        except Exception:
            logger.exception("Failed to publish Kafka event %s", event.get("event_type"))
            return False


kafka_producer = ChatKafkaProducer()
