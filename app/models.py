from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ============================================================
# CONTEXT
# ============================================================

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


class ContextResponse(BaseModel):
    accepted: bool
    ack_id: Optional[str] = None
    stored_at: Optional[str] = None
    reason: Optional[str] = None
    current_version: Optional[int] = None
    details: Optional[str] = None


# ============================================================
# TICK
# ============================================================

class TickRequest(BaseModel):
    now: Optional[str] = None
    available_triggers: List[str] = Field(default_factory=list)


class Action(BaseModel):
    conversation_id: str
    merchant_id: Optional[str] = None
    customer_id: Optional[str] = None
    send_as: str
    trigger_id: str
    template_name: Optional[str] = None
    template_params: List[Any] = Field(default_factory=list)
    body: str
    cta: Optional[str] = None
    suppression_key: Optional[str] = None
    rationale: str


class TickResponse(BaseModel):
    actions: List[Action] = Field(default_factory=list)


# ============================================================
# REPLY
# ============================================================

class ReplyRequest(BaseModel):
    conversation_id: str
    merchant_id: Optional[str] = None
    customer_id: Optional[str] = None
    from_role: str
    message: str
    received_at: Optional[str] = None
    turn_number: Optional[int] = None


class ReplyResponse(BaseModel):
    action: str
    body: Optional[str] = None
    cta: Optional[str] = None
    wait_seconds: Optional[int] = None
    rationale: str


# ============================================================
# HEALTH
# ============================================================

class HealthResponse(BaseModel):
    status: str
    uptime_seconds: float
    contexts_loaded: Dict[str, int]


# ============================================================
# METADATA
# ============================================================

class MetadataResponse(BaseModel):
    team_name: str
    team_members: List[str]
    model: str
    approach: str
    contact_email: str
    version: str
    submitted_at: Optional[str] = None