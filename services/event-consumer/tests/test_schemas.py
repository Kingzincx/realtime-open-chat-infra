from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas import ChatEvent


def test_chat_event_accepts_expected_payload() -> None:
    message_id = uuid4()
    event = ChatEvent(
        event_id=uuid4(),
        event_type="message.sent",
        username="joel",
        payload={"message_id": str(message_id), "content_length": 5},
        timestamp="2026-04-26T14:00:00Z",
    )

    assert event.event_type == "message.sent"
    assert event.payload["message_id"] == str(message_id)


def test_chat_event_requires_event_id() -> None:
    with pytest.raises(ValidationError):
        ChatEvent(
            event_type="user.joined",
            username="joel",
            payload={},
            timestamp="2026-04-26T14:00:00Z",
        )
