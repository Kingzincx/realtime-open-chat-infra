import json
import logging

import asyncpg

from .config import settings
from .schemas import ChatEvent, DetectedAlert, MessageSentPayload

logger = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None


async def connect_db() -> None:
    global _pool
    _pool = await asyncpg.create_pool(settings.database_url, min_size=1, max_size=5)
    logger.info("Connected moderation consumer to PostgreSQL")


async def close_db() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("Closed moderation consumer PostgreSQL pool")


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("PostgreSQL pool is not initialized")
    return _pool


async def persist_alerts(
    event: ChatEvent,
    payload: MessageSentPayload,
    alerts: list[DetectedAlert],
) -> set[str]:
    query = """
        INSERT INTO moderation_alerts (
            event_id,
            message_id,
            username,
            reason,
            severity,
            content_preview,
            payload,
            created_at
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8)
        ON CONFLICT (event_id, reason) DO NOTHING
        RETURNING id;
    """
    inserted_reasons: set[str] = set()
    content_preview = payload.content[:200]

    async with get_pool().acquire() as connection:
        for alert in alerts:
            record = await connection.fetchrow(
                query,
                event.event_id,
                payload.message_id,
                event.username,
                alert.reason,
                alert.severity,
                content_preview,
                json.dumps(alert.details),
                event.timestamp,
            )
            if record is not None:
                inserted_reasons.add(alert.reason)

    return inserted_reasons
