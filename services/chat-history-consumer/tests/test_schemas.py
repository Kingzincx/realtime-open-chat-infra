from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas import ChatEvent, MessageSentPayload


def test_message_sent_payload_accepts_uuid_message_id() -> None:
    message_id = uuid4()
    payload = MessageSentPayload(
        message_id=message_id,
        content="  hello  ",
        content_length=5,
    )

    assert payload.message_id == message_id
    assert payload.content == "hello"


def test_message_sent_payload_rejects_blank_content() -> None:
    with pytest.raises(ValidationError):
        MessageSentPayload(
            message_id=uuid4(),
            content="   ",
            content_length=1,
        )


def test_chat_event_accepts_message_sent() -> None:
    event = ChatEvent(
        event_id=uuid4(),
        event_type="message.sent",
        username="joel",
        payload={
            "message_id": str(uuid4()),
            "content": "hello",
            "content_length": 5,
        },
        timestamp="2026-04-26T14:00:00Z",
    )

    assert event.event_type == "message.sent"
