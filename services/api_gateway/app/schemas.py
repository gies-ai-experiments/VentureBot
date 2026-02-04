from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from .models import MessageRole, JourneyStage


class ChatSessionCreate(BaseModel):
    title: Optional[str] = Field(default=None, description="Optional session label")
    auto_start: bool = Field(default=False, description="Whether to auto-run onboarding agent")


class ChatSessionRead(BaseModel):
    id: str
    title: Optional[str]
    current_stage: JourneyStage
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatMessageCreate(BaseModel):
    role: MessageRole
    content: str


class ChatMessageRead(BaseModel):
    id: str
    session_id: str
    role: MessageRole
    content: str
    created_at: datetime
    suggested_replies: Optional[List[str]] = None

    class Config:
        from_attributes = True


class ChatTurnResponse(BaseModel):
    session: ChatSessionRead
    user_message: ChatMessageRead
    assistant_message: ChatMessageRead


class SessionStartResponse(BaseModel):
    """Response when starting a new session with auto-onboarding."""
    session: ChatSessionRead
    onboarding_message: Optional[ChatMessageRead] = None
