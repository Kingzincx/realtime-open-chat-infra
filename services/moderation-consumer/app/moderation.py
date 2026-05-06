from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta

from .schemas import DetectedAlert, MessageSentPayload


@dataclass(frozen=True)
class ModerationRules:
    blocked_words: tuple[str, ...]
    max_message_length: int
    duplicate_window_seconds: int
    flood_window_seconds: int
    flood_message_threshold: int


class ModerationState:
    def __init__(self, rules: ModerationRules) -> None:
        self.rules = rules
        self._message_times: dict[str, deque[datetime]] = defaultdict(deque)
        self._last_seen_content: dict[str, dict[str, datetime]] = defaultdict(dict)

    def evaluate(
        self,
        username: str,
        payload: MessageSentPayload,
        timestamp: datetime,
    ) -> list[DetectedAlert]:
        alerts: list[DetectedAlert] = []
        normalized_content = payload.content.lower()

        alerts.extend(self._check_blocked_words(normalized_content))
        alerts.extend(self._check_message_length(payload))
        alerts.extend(self._check_duplicate_message(username, normalized_content, timestamp))
        alerts.extend(self._check_flood(username, timestamp))

        return alerts

    def _check_blocked_words(self, content: str) -> list[DetectedAlert]:
        matches = [word for word in self.rules.blocked_words if word in content]
        if not matches:
            return []
        return [
            DetectedAlert(
                reason="blocked_word.detected",
                severity="medium",
                details={"blocked_words": matches},
            )
        ]

    def _check_message_length(self, payload: MessageSentPayload) -> list[DetectedAlert]:
        observed_length = max(len(payload.content), payload.content_length)
        if observed_length <= self.rules.max_message_length:
            return []
        return [
            DetectedAlert(
                reason="message.too_long",
                severity="low",
                details={
                    "observed_length": observed_length,
                    "max_message_length": self.rules.max_message_length,
                },
            )
        ]

    def _check_duplicate_message(
        self,
        username: str,
        content: str,
        timestamp: datetime,
    ) -> list[DetectedAlert]:
        cutoff = timestamp - timedelta(seconds=self.rules.duplicate_window_seconds)
        user_content = self._last_seen_content[username]

        for previous_content, seen_at in list(user_content.items()):
            if seen_at < cutoff:
                del user_content[previous_content]

        previous_seen_at = user_content.get(content)
        user_content[content] = timestamp

        if previous_seen_at is None:
            return []

        return [
            DetectedAlert(
                reason="duplicate_message.detected",
                severity="low",
                details={
                    "duplicate_window_seconds": self.rules.duplicate_window_seconds,
                    "previous_seen_at": previous_seen_at.isoformat(),
                },
            )
        ]

    def _check_flood(self, username: str, timestamp: datetime) -> list[DetectedAlert]:
        cutoff = timestamp - timedelta(seconds=self.rules.flood_window_seconds)
        times = self._message_times[username]
        times.append(timestamp)

        while times and times[0] < cutoff:
            times.popleft()

        if len(times) < self.rules.flood_message_threshold:
            return []

        return [
            DetectedAlert(
                reason="flood.detected",
                severity="high",
                details={
                    "message_count": len(times),
                    "flood_window_seconds": self.rules.flood_window_seconds,
                    "threshold": self.rules.flood_message_threshold,
                },
            )
        ]
