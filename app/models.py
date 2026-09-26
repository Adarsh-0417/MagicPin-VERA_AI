from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ContextPayload(BaseModel):
    scope: str
    context_id: str
    version: int
    payload: Dict[str, Any]
    delivered_at: Optional[str] = None


class ContextRecord(BaseModel):
    scope: str
    context_id: str
    version: int
    payload: Dict[str, Any]
    delivered_at: Optional[str] = None


class TickRequest(BaseModel):
    available_triggers: List[str] = Field(default_factory=list)


class Action(BaseModel):
    conversation_id: Optional[str] = None
    trigger_id: Optional[str] = None
    action: str
    rationale: str
    message: Optional[Dict[str, Any]] = None


class TickResponse(BaseModel):
    actions: List[Action]


class ReplyRequest(BaseModel):
    conversation_id: str
    message: str
    customer_id: Optional[str] = None
    merchant_id: Optional[str] = None
    trigger_id: Optional[str] = None


class ReplyResponse(BaseModel):
    action: str
    rationale: str
    message: Optional[Dict[str, Any]] = None
    wait_seconds: Optional[int] = None