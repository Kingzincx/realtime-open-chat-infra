from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest

CHAT_EVENTS_CONSUMED_TOTAL = Counter(
    "chat_events_consumed_total",
    "Total valid chat events consumed from Kafka.",
    ["event_type"],
)

CHAT_EVENT_CONSUMER_DB_WRITES_TOTAL = Counter(
    "chat_event_consumer_db_writes_total",
    "Total chat events written to PostgreSQL by the audit consumer.",
    ["event_type"],
)

CHAT_EVENT_CONSUMER_DUPLICATES_TOTAL = Counter(
    "chat_event_consumer_duplicates_total",
    "Total duplicate chat events skipped by event_id.",
    ["event_type"],
)

CHAT_EVENT_CONSUMER_ERRORS_TOTAL = Counter(
    "chat_event_consumer_errors_total",
    "Total unexpected errors in the event audit consumer.",
)

CHAT_EVENT_CONSUMER_INVALID_EVENTS_TOTAL = Counter(
    "chat_event_consumer_invalid_events_total",
    "Total malformed Kafka messages skipped by the event audit consumer.",
)

CHAT_EVENT_CONSUMER_KAFKA_LAG = Gauge(
    "chat_event_consumer_kafka_lag",
    "Approximate Kafka lag observed by the event audit consumer.",
    ["topic", "partition"],
)


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
