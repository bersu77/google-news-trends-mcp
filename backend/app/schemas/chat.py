from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: Any
    result: Optional[str] = None
    status: Optional[str] = None


class Message(BaseModel):
    id: Optional[str] = None
    conversation_id: str
    user_id: str
    role: MessageRole
    content: str
    tool_calls: Optional[List[ToolCall]] = None
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class Conversation(BaseModel):
    id: Optional[str] = None
    user_id: str
    title: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    content: str
    tool_calls: Optional[List[ToolCall]] = None


class StreamingChunk(BaseModel):
    type: str  # "token", "tool_call", "content", "error"
    content: Optional[str] = None
    token: Optional[str] = None
    tool_call: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    conversation_id: str
    message_id: str
