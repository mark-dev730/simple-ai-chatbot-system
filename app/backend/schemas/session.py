from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SessionCreate(BaseModel):
    """Create new chat session"""
    session_name: Optional[str] = Field(None, max_length=100)


class SessionUpdate(BaseModel):
    """Update chat session"""
    session_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class SessionResponse(BaseModel):
    """Chat session response"""
    session_id: int
    user_id: int
    session_name: Optional[str]
    created_at: datetime
    updated_at: datetime
    is_active: bool
    message_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    """List of sessions"""
    sessions: list[SessionResponse]
    total: int

