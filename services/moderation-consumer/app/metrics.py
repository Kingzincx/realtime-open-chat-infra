from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest

MODERATION_EVENTS_CONSUMED_TOTAL = Counter(
    "moderation_events_consumed_total",
    "Total message.sent events consumed by the moderation consumer.",
)

MODERATION_EVENTS_SKIPPED_TOTAL = Counter(
    "moderation_events_skipped_total",
    "Total non-message events skipped by the moderation consumer.",
    ["event_type"],
)

MODERATION_ALERTS_CREATED_TOTAL = Counter(
    "moderation_alerts_created_total",
    "Total moderation alerts written to PostgreSQL.",
    ["reason", "severity"],
)

MODERATION_DUPLICATE_ALERTS_TOTAL = Counter(
    "moderation_duplicate_alerts_total",
    "Total duplicate moderation alerts skipped by event_id and reason.",
    ["reason"],
)

MODERATION_MESSAGES_FLAGGED_TOTAL = Counter(
    "moderation_messages_flagged_total",
    "Total chat messages with at least one moderation alert.",
)

MODERATION_INVALID_EVENTS_TOTAL = Counter(
    "moderation_invalid_events_total",
    "Total malformed Kafka messages skipped by the moderation consumer.",
)

MODERATION_CONSUMER_ERRORS_TOTAL = Counter(
    "moderation_consumer_errors_total",
    "Total unexpected errors in the moderation consumer.",
)

MODERATION_CONSUMER_KAFKA_LAG = Gauge(
    "moderation_consumer_kafka_lag",
    "Approximate Kafka lag observed by the moderation consumer.",
    ["topic", "partition"],
)


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
