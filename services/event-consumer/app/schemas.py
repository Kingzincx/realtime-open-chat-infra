from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChatEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    event_id: UUID
    event_type: Literal["user.joined", "user.left", "message.sent"]
    username: str = Field(min_length=1, max_length=80)
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime
