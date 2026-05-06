import pytest
from pydantic import ValidationError

from app.schemas import ChatEvent, InboundMessage, OutboundMessage, utc_timestamp


def test_inbound_message_trims_content() -> None:
    message = InboundMessage(content="  hello  ")

    assert message.content == "hello"


def test_inbound_message_rejects_blank_content() -> None:
    with pytest.raises(ValidationError):
        InboundMessage(content="   ")


def test_outbound_message_defaults_to_timestamp() -> None:
    message = OutboundMessage(type="system", content="joel entrou no chat")

    assert message.timestamp.endswith("Z")


def test_outbound_message_can_carry_message_id() -> None:
    message = OutboundMessage(
        type="message",
        message_id="6d98351c-ff1d-4e21-b5b6-4a77ec2f5353",
        username="joel",
        content="hello",
    )

    assert message.message_id == "6d98351c-ff1d-4e21-b5b6-4a77ec2f5353"


def test_utc_timestamp_is_utc() -> None:
    assert utc_timestamp().endswith("Z")


def test_chat_event_has_event_id() -> None:
    event = ChatEvent(event_type="user.joined", username="joel")

    assert event.event_id
