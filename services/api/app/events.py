import logging
from typing import Any

from .kafka_client import kafka_producer
from .metrics import (
    CHAT_KAFKA_EVENTS_PUBLISHED_TOTAL,
    CHAT_KAFKA_PUBLISH_ERRORS_TOTAL,
)
from .schemas import ChatEvent

logger = logging.getLogger(__name__)


async def publish_chat_event(
    event_type: str,
    username: str,
    payload: dict[str, Any] | None = None,
) -> tuple[ChatEvent, bool]:
    event = ChatEvent(
        event_type=event_type,
        username=username,
        payload=payload or {},
    )

    published = await kafka_producer.publish(event.model_dump())
    if published:
        CHAT_KAFKA_EVENTS_PUBLISHED_TOTAL.labels(event_type=event.event_type).inc()
    else:
        CHAT_KAFKA_PUBLISH_ERRORS_TOTAL.labels(event_type=event.event_type).inc()

    logger.info(
        "event=%s username=%s published=%s",
        event.event_type,
        event.username,
        published,
    )
    return event, published
