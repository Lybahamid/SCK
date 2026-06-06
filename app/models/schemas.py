from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


# -----------------------------------------------
# ENUMS
# -----------------------------------------------

class SourcePlatform(str, Enum):
    chatgpt = "chatgpt"
    claude = "claude"
    gemini = "gemini"
    unknown = "unknown"


class InputMethod(str, Enum):
    json_upload = "json_upload"
    share_link = "share_link"
    raw_text = "raw_text"
    extension = "extension"


class ContextStrategy(str, Enum):
    full = "full"
    concise = "concise"
    technical = "technical"
    creative = "creative"
    full_ai = "full_ai"


class TargetPlatform(str, Enum):
    chatgpt = "chatgpt"
    claude = "claude"
    gemini = "gemini"
    generic = "generic"


class MessageRole(str, Enum):
    user = "user"
    assistant = "assistant"


# -----------------------------------------------
# MESSAGE SCHEMAS
# -----------------------------------------------

class MessageBase(BaseModel):
    role: MessageRole
    content: str
    position: int


class MessageCreate(MessageBase):
    session_id: str


class MessageResponse(MessageBase):
    id: str
    session_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# -----------------------------------------------
# SESSION SCHEMAS
# -----------------------------------------------

class SessionBase(BaseModel):
    title: Optional[str] = None
    source_platform: SourcePlatform = SourcePlatform.unknown
    input_method: InputMethod
    message_count: int = 0


class SessionCreate(SessionBase):
    messages: List[MessageBase] = []


class SessionResponse(SessionBase):
    id: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True


class SessionSummary(BaseModel):
    """
    Lightweight session response without messages.
    Used for listing sessions without loading full content.
    """
    id: str
    title: Optional[str]
    source_platform: SourcePlatform
    input_method: InputMethod
    message_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# -----------------------------------------------
# GENERATED CONTEXT SCHEMAS
# -----------------------------------------------

class GeneratedContextBase(BaseModel):
    strategy: ContextStrategy = ContextStrategy.full
    target_platform: TargetPlatform = TargetPlatform.generic
    content: str


class GeneratedContextCreate(GeneratedContextBase):
    session_id: str


class GeneratedContextResponse(GeneratedContextBase):
    id: str
    session_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# -----------------------------------------------
# API RESPONSE WRAPPERS
# -----------------------------------------------

class SuccessResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None
    data: Optional[dict] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[str] = None


class PaginatedSessionsResponse(BaseModel):
    success: bool = True
    total: int
    page: int
    limit: int
    sessions: List[SessionSummary]


class ContextGenerationResponse(BaseModel):
    success: bool = True
    context: str
    strategy: ContextStrategy
    target_platform: TargetPlatform
    source_platform: SourcePlatform
    message_count: int
    title: Optional[str]
    session_id: Optional[str] = None