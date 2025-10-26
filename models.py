from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone


class MessageTemplate(BaseModel):
    id: Optional[int]
    user_id: str
    category: str
    key: str
    content: str
    reply_relay: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: datetime = Field(default_factory=lambda: datetime.now())
