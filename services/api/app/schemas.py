from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class InboundMessage(BaseModel):
    content: str = Field(min_length=1, max_length=1000)

    @field_validator("content")
    @classmethod
    def normalize_content(cls, value: str) -> str:
        content = value.strip()
        if not content:
            raise ValueError("message content cannot be empty")
        return content


class OutboundMessage(BaseModel):
    type: Literal["message", "system", "error"]
    content: str
    message_id: str | None = None
    username: str | None = None
    timestamp: str = Field(default_factory=utc_timestamp)


class ChatEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: Literal["user.joined", "user.left", "message.sent"]
    username: str
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=utc_timestamp)
