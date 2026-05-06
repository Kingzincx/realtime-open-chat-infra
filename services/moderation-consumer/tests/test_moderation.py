from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.moderation import ModerationRules, ModerationState
from app.schemas import MessageSentPayload


def make_payload(content: str) -> MessageSentPayload:
    return MessageSentPayload(
        message_id=uuid4(),
        content=content,
        content_length=len(content),
    )


def make_state() -> ModerationState:
    return ModerationState(
        ModerationRules(
            blocked_words=("spam", "scam"),
            max_message_length=20,
            duplicate_window_seconds=30,
            flood_window_seconds=10,
            flood_message_threshold=3,
        )
    )


def test_detects_blocked_word() -> None:
    state = make_state()

    alerts = state.evaluate(
        username="joel",
        payload=make_payload("this looks like spam"),
        timestamp=datetime.now(timezone.utc),
    )

    assert {alert.reason for alert in alerts} == {"blocked_word.detected"}


def test_detects_long_message() -> None:
    state = make_state()

    alerts = state.evaluate(
        username="joel",
        payload=make_payload("x" * 25),
        timestamp=datetime.now(timezone.utc),
    )

    assert {alert.reason for alert in alerts} == {"message.too_long"}


def test_detects_duplicate_message_inside_window() -> None:
    state = make_state()
    now = datetime.now(timezone.utc)

    state.evaluate("joel", make_payload("same text"), now)
    alerts = state.evaluate("joel", make_payload("same text"), now + timedelta(seconds=1))

    assert {alert.reason for alert in alerts} == {"duplicate_message.detected"}


def test_detects_flood_inside_window() -> None:
    state = make_state()
    now = datetime.now(timezone.utc)

    state.evaluate("joel", make_payload("one"), now)
    state.evaluate("joel", make_payload("two"), now + timedelta(seconds=1))
    alerts = state.evaluate("joel", make_payload("three"), now + timedelta(seconds=2))

    assert {alert.reason for alert in alerts} == {"flood.detected"}
