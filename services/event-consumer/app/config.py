from dataclasses import dataclass
import os

from common.config import (
    read_database_url,
    read_kafka_bootstrap_servers,
    read_kafka_topic,
)


@dataclass(frozen=True)
class Settings:
    database_url: str
    kafka_bootstrap_servers: str
    kafka_topic: str
    consumer_group: str

def get_settings() -> Settings:
    return Settings(
        database_url=read_database_url(),
        kafka_bootstrap_servers=read_kafka_bootstrap_servers(),
        kafka_topic=read_kafka_topic(),
        consumer_group=os.getenv("EVENT_CONSUMER_GROUP", "chat-event-audit"),
    )


settings = get_settings()
