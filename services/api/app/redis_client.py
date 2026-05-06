import logging

from redis.asyncio import Redis

from .config import settings

logger = logging.getLogger(__name__)

ONLINE_USERS_KEY = "chat:online_users"
ONLINE_USER_SESSIONS_KEY = "chat:online_user_sessions"

_redis: Redis | None = None


async def connect_redis() -> None:
    global _redis
    _redis = Redis.from_url(settings.redis_url, decode_responses=True)
    await _redis.ping()
    logger.info("Connected to Redis")


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None
        logger.info("Closed Redis connection")


def get_redis() -> Redis | None:
    return _redis


async def increment_user_session(username: str) -> None:
    if _redis is None:
        return
    try:
        await _redis.hincrby(ONLINE_USER_SESSIONS_KEY, username, 1)
        await _redis.sadd(ONLINE_USERS_KEY, username)
    except Exception:
        logger.exception("Failed to increment Redis online session for %s", username)


async def decrement_user_session(username: str) -> None:
    if _redis is None:
        return
    try:
        count = await _redis.hincrby(ONLINE_USER_SESSIONS_KEY, username, -1)
        if int(count) <= 0:
            await _redis.hdel(ONLINE_USER_SESSIONS_KEY, username)
            await _redis.srem(ONLINE_USERS_KEY, username)
    except Exception:
        logger.exception("Failed to decrement Redis online session for %s", username)


async def list_online_users() -> list[str]:
    if _redis is None:
        return []
    try:
        users = await _redis.smembers(ONLINE_USERS_KEY)
        return sorted(users)
    except Exception:
        logger.exception("Failed to list Redis online users")
        return []
