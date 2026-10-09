from pydantic import BaseModel, Field, field_serializer
from typing import Optional
from datetime import datetime


class MessageCreate(BaseModel):
    """Send a message in a chat session"""
    content: str = Field(..., min_length=1)
    model_name: Optional[str] = Field(None, description="Ollama model to use")
    enable_rag: Optional[bool] = Field(False, description="Enable RAG context injection")
    rag_table: Optional[str] = Field(None, description="Specific table for RAG context")


class MessageResponse(BaseModel):
    """Chat message response"""
    message_id: int
    session_id: int
    role: str
    content: str
    timestamp: datetime
    token_count: Optional[int] = None
    clarification: Optional[dict] = None  # New field for clarification requests
    
    @field_serializer('timestamp')
    def serialize_timestamp(self, dt: datetime, _info):
        # Ensure timestamp is always returned as ISO format with UTC timezone
        if dt.tzinfo is None:
            # If naive datetime, assume it's UTC
            from datetime import timezone
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    
    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    """Chat history for a session"""
    session_id: int
    messages: list[MessageResponse]
    total: int


class ChatRequest(BaseModel):
    """Chat request with optional configuration"""
    message: str = Field(..., min_length=1)
    session_id: int
    model_name: Optional[str] = "gemma2:2b"
    temperature: Optional[float] = Field(0.7, ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(2000, ge=100, le=4000)
    stream: Optional[bool] = False


class ModelInfo(BaseModel):
    """Ollama model information"""
    name: str
    size: Optional[int] = None
    modified_at: Optional[str] = None


class ModelListResponse(BaseModel):
    """List of available models"""
    models: list[ModelInfo]
    total: int

