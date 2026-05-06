from dataclasses import dataclass
import os

from common.config import (
    read_database_url,
    read_kafka_bootstrap_servers,
    read_kafka_topic,
)


def parse_words(raw: str) -> tuple[str, ...]:
    return tuple(word.strip().lower() for word in raw.split(",") if word.strip())


@dataclass(frozen=True)
class Settings:
    database_url: str
    kafka_bootstrap_servers: str
    kafka_topic: str
    consumer_group: str
    blocked_words: tuple[str, ...]
    max_message_length: int
    duplicate_window_seconds: int
    flood_window_seconds: int
    flood_message_threshold: int

def get_settings() -> Settings:
    return Settings(
        database_url=read_database_url(),
        kafka_bootstrap_servers=read_kafka_bootstrap_servers(),
        kafka_topic=read_kafka_topic(),
        consumer_group=os.getenv("MODERATION_CONSUMER_GROUP", "chat-moderation"),
        blocked_words=parse_words(os.getenv("MODERATION_BLOCKED_WORDS", "spam,scam")),
        max_message_length=int(os.getenv("MODERATION_MAX_MESSAGE_LENGTH", "500")),
        duplicate_window_seconds=int(os.getenv("MODERATION_DUPLICATE_WINDOW_SECONDS", "30")),
        flood_window_seconds=int(os.getenv("MODERATION_FLOOD_WINDOW_SECONDS", "10")),
        flood_message_threshold=int(os.getenv("MODERATION_FLOOD_MESSAGE_THRESHOLD", "5")),
    )


settings = get_settings()
