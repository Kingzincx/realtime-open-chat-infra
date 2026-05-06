from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChatEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    event_id: UUID
    event_type: Literal["user.joined", "user.left", "message.sent"]
    username: str = Field(min_length=1, max_length=80)
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime


class MessageSentPayload(BaseModel):
    message_id: UUID
    content: str = Field(min_length=1, max_length=1000)
    content_length: int = Field(ge=1, le=1000)

    @field_validator("content")
    @classmethod
    def normalize_content(cls, value: str) -> str:
        content = value.strip()
        if not content:
            raise ValueError("message content cannot be empty")
        return content
