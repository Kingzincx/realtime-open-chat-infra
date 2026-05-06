from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import pendulum
import psycopg2
from airflow.decorators import dag, task


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


def read_secret(secret_env: str, file_env: str) -> str:
    secret_file = os.getenv(file_env)
    if secret_file:
        return Path(secret_file).read_text(encoding="utf-8").strip()

    secret = os.getenv(secret_env)
    if secret:
        return secret

    raise RuntimeError(f"{file_env} or {secret_env} must be set")


def connect_to_chat_db():
    return psycopg2.connect(
        host=os.getenv("CHAT_POSTGRES_HOST", "postgres"),
        port=int(os.getenv("CHAT_POSTGRES_PORT", "5432")),
        dbname=os.getenv("CHAT_POSTGRES_DB", "chatdb"),
        user=os.getenv("CHAT_POSTGRES_USER", "chat"),
        password=read_secret("CHAT_POSTGRES_PASSWORD", "CHAT_POSTGRES_PASSWORD_FILE"),
    )


def extract_hour_window(context: dict[str, Any]) -> tuple[pendulum.DateTime, pendulum.DateTime, pendulum.DateTime]:
    start = context["data_interval_start"].in_timezone("UTC")
    end = context["data_interval_end"].in_timezone("UTC")
    hour = start.replace(minute=0, second=0, microsecond=0)
    return hour, start, end


def fetch_hourly_event_counts(cursor, start: pendulum.DateTime, end: pendulum.DateTime) -> tuple[int, int, int]:
    cursor.execute(
        """
        SELECT
            count(*) FILTER (WHERE event_type = 'message.sent') AS total_messages,
            count(*) FILTER (WHERE event_type = 'user.joined') AS total_joins,
            count(*) FILTER (WHERE event_type = 'user.left') AS total_leaves
        FROM chat_events
        WHERE created_at >= %s
          AND created_at < %s;
        """,
        (start, end),
    )
    return cursor.fetchone()


def upsert_hourly_stats(cursor, hour: pendulum.DateTime, total_messages: int, total_joins: int, total_leaves: int) -> None:
    cursor.execute(
        """
        INSERT INTO chat_hourly_stats (
            hour,
            total_messages,
            total_joins,
            total_leaves
        )
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (hour)
        DO UPDATE SET
            total_messages = EXCLUDED.total_messages,
            total_joins = EXCLUDED.total_joins,
            total_leaves = EXCLUDED.total_leaves,
            created_at = now();
        """,
        (hour, total_messages, total_joins, total_leaves),
    )


@dag(
    dag_id="chat_hourly_analytics",
    schedule="@hourly",
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    tags=["chat", "analytics"],
)
def chat_hourly_analytics():
    @task()
    def calculate_hourly_stats(**context: Any) -> None:
        hour, start, end = extract_hour_window(context)

        with connect_to_chat_db() as connection:
            with connection.cursor() as cursor:
                total_messages, total_joins, total_leaves = fetch_hourly_event_counts(cursor, start, end)
                upsert_hourly_stats(cursor, hour, total_messages, total_joins, total_leaves)

        logger.info(
            "Stored hourly chat stats hour=%s messages=%s joins=%s leaves=%s",
            hour,
            total_messages,
            total_joins,
            total_leaves,
        )

    calculate_hourly_stats()


chat_hourly_analytics()
