import json
import logging

import asyncpg

from .config import settings
from .schemas import ChatEvent

logger = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None


async def connect_db() -> None:
    global _pool
    _pool = await asyncpg.create_pool(settings.database_url, min_size=1, max_size=5)
    logger.info("Connected event consumer to PostgreSQL")


async def close_db() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("Closed event consumer PostgreSQL pool")


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("PostgreSQL pool is not initialized")
    return _pool


async def persist_chat_event(event: ChatEvent) -> bool:
    query = """
        INSERT INTO chat_events (event_id, event_type, username, payload, created_at)
        VALUES ($1, $2, $3, $4::jsonb, $5)
        ON CONFLICT (event_id) DO NOTHING
        RETURNING id;
    """
    async with get_pool().acquire() as connection:
        record = await connection.fetchrow(
            query,
            event.event_id,
            event.event_type,
            event.username,
            json.dumps(event.payload),
            event.timestamp,
        )
    return record is not None
