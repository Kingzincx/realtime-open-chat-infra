from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

CHAT_ACTIVE_CONNECTIONS = Gauge(
    "chat_active_connections",
    "Current number of open WebSocket connections.",
)

CHAT_MESSAGES_TOTAL = Counter(
    "chat_messages_total",
    "Total chat messages accepted by the WebSocket API.",
)

CHAT_USER_JOINED_TOTAL = Counter(
    "chat_user_joined_total",
    "Total user joined events.",
)

CHAT_USER_LEFT_TOTAL = Counter(
    "chat_user_left_total",
    "Total user left events.",
)

CHAT_WEBSOCKET_ERRORS_TOTAL = Counter(
    "chat_websocket_errors_total",
    "Total WebSocket errors observed by the API.",
)

CHAT_KAFKA_EVENTS_PUBLISHED_TOTAL = Counter(
    "chat_kafka_events_published_total",
    "Total events successfully published to Kafka.",
    ["event_type"],
)

CHAT_KAFKA_PUBLISH_ERRORS_TOTAL = Counter(
    "chat_kafka_publish_errors_total",
    "Total Kafka publish failures.",
    ["event_type"],
)

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests handled by FastAPI.",
    ["method", "path", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ["method", "path"],
)


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
