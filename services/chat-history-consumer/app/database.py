import logging

import asyncpg

from .config import settings
from .schemas import ChatEvent, MessageSentPayload

logger = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None


async def connect_db() -> None:
    global _pool
    _pool = await asyncpg.create_pool(settings.database_url, min_size=1, max_size=5)
    logger.info("Connected chat history consumer to PostgreSQL")


async def close_db() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("Closed chat history consumer PostgreSQL pool")


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("PostgreSQL pool is not initialized")
    return _pool


async def persist_message(event: ChatEvent, payload: MessageSentPayload) -> bool:
    query = """
        INSERT INTO messages (message_id, username, content, created_at)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (message_id) DO NOTHING
        RETURNING id;
    """
    async with get_pool().acquire() as connection:
        record = await connection.fetchrow(
            query,
            payload.message_id,
            event.username,
            payload.content,
            event.timestamp,
        )
    return record is not None
