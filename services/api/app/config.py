from dataclasses import dataclass
import os

from common.config import (
    read_kafka_bootstrap_servers,
    read_kafka_topic,
)


@dataclass(frozen=True)
class Settings:
    app_name: str
    redis_url: str
    kafka_bootstrap_servers: str
    kafka_topic: str

def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "realtime-open-chat-infra"),
        redis_url=os.getenv("REDIS_URL", "redis://redis:6379/0"),
        kafka_bootstrap_servers=read_kafka_bootstrap_servers(),
        kafka_topic=read_kafka_topic(),
    )


settings = get_settings()
