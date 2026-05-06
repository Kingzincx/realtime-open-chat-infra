from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest

CHAT_HISTORY_EVENTS_CONSUMED_TOTAL = Counter(
    "chat_history_events_consumed_total",
    "Total message.sent events consumed by the chat history consumer.",
)

CHAT_HISTORY_EVENTS_SKIPPED_TOTAL = Counter(
    "chat_history_events_skipped_total",
    "Total non-message events skipped by the chat history consumer.",
    ["event_type"],
)

CHAT_HISTORY_MESSAGES_PERSISTED_TOTAL = Counter(
    "chat_history_messages_persisted_total",
    "Total chat messages persisted by the chat history consumer.",
)

CHAT_HISTORY_DUPLICATE_MESSAGES_TOTAL = Counter(
    "chat_history_duplicate_messages_total",
    "Total duplicate chat messages skipped by message_id.",
)

CHAT_HISTORY_INVALID_EVENTS_TOTAL = Counter(
    "chat_history_invalid_events_total",
    "Total malformed Kafka messages skipped by the chat history consumer.",
)

CHAT_HISTORY_CONSUMER_ERRORS_TOTAL = Counter(
    "chat_history_consumer_errors_total",
    "Total unexpected errors in the chat history consumer.",
)

CHAT_HISTORY_CONSUMER_KAFKA_LAG = Gauge(
    "chat_history_consumer_kafka_lag",
    "Approximate Kafka lag observed by the chat history consumer.",
    ["topic", "partition"],
)


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
