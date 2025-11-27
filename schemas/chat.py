from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class ChatMessageBase(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatMessageCreate(ChatMessageBase):
    session_id: str


class ChatMessage(ChatMessageBase):
    id: str
    session_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionBase(BaseModel):
    user_id: Optional[str] = None


class ChatSessionCreate(ChatSessionBase):
    pass


class ChatSession(ChatSessionBase):
    id: str
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessage] = []

    class Config:
        from_attributes = True
