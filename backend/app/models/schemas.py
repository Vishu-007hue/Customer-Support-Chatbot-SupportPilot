from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=2)
    message: str = Field(..., min_length=1)
    user_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    intent: str
    confidence: float
    handover_suggested: bool
    source: str


class HandoverRequest(BaseModel):
    session_id: str = Field(..., min_length=2)
    reason: str = Field(..., min_length=3)
    transcript: Optional[list[str]] = None


class HandoverResponse(BaseModel):
    status: str
    handover_id: str


class ResponseRecordIn(BaseModel):
    intent: str = Field(..., min_length=2)
    variants: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class ResponseRecordOut(ResponseRecordIn):
    id: str


class AnalyticsSummary(BaseModel):
    total_queries: int
    bot_messages: int
    handover_count: int
    top_intents: list[dict]


class AdminLoginRequest(BaseModel):
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=3)


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class NLPResult(BaseModel):
    intent: str
    confidence: float
    entities: dict
    raw_text: str


class MessageDocument(BaseModel):
    session_id: str
    sender: str
    text: str
    intent: Optional[str] = None
    confidence: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
