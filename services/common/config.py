import os
from pathlib import Path
from urllib.parse import quote_plus


def read_env_or_file(secret_env: str, file_env: str) -> str:
    secret_file = os.getenv(file_env)
    if secret_file:
        return Path(secret_file).read_text(encoding="utf-8").strip()

    secret = os.getenv(secret_env)
    if secret:
        return secret

    raise RuntimeError(f"{file_env} or {secret_env} must be set")


def read_database_url() -> str:
    database_url_file = os.getenv("DATABASE_URL_FILE")
    if database_url_file:
        return Path(database_url_file).read_text(encoding="utf-8").strip()

    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    user = os.getenv("POSTGRES_USER", "chat")
    password = quote_plus(
        read_env_or_file("POSTGRES_PASSWORD", "POSTGRES_PASSWORD_FILE")
    )
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "chatdb")
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


def read_kafka_bootstrap_servers() -> str:
    return os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")


def read_kafka_topic() -> str:
    return os.getenv("KAFKA_TOPIC", "chat.events")
