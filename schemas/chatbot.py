from typing import Optional, Any
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None  # ID của session để lưu lịch sử
    system_prompt: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    session_id: Optional[str] = None  # Trả về session_id để client lưu lại


class CRUDRequest(BaseModel):
    action: str  # 'create' | 'read' | 'update' | 'delete'
    resource: str  # 'headphone' | 'brand' | 'type'
    id: Optional[str] = None
    data: Optional[dict[str, Any]] = None


class CRUDResponse(BaseModel):
    result: Any
