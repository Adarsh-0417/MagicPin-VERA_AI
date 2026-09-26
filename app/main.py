from datetime import datetime, timezone
from time import monotonic
from uuid import uuid4

from fastapi import FastAPI, HTTPException

from app.context_store import ContextStore
from app.context_resolver import ContextResolver
from app.models import (
    Action,
    ContextPayload,
    ContextResponse,
    HealthResponse,
    MetadataResponse,
    ReplyRequest,
    ReplyResponse,
    TickRequest,
    TickResponse,
)


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="Magicpin Vera AI",
    version="0.1.0",
    description="Stateful AI engagement engine for the Vera AI Challenge.",
)


# ============================================================
# GLOBAL STATE
# ============================================================

START_TIME = monotonic()

context_store = ContextStore()
context_resolver = ContextResolver(context_store)


# ============================================================
# CONSTANTS
# ============================================================

VALID_SCOPES = {
    "category",
    "merchant",
    "customer",
    "trigger",
}

TEAM_NAME = "Adarsh"
TEAM_MEMBERS = ["Adarsh"]

MODEL_NAME = "rule-engine-v0.1"

APP_VERSION = "0.1.0"

APPROACH = (
    "stateful 4-context decision engine "
    "with deterministic eligibility and grounded composition"
)

CONTACT_EMAIL = ""


# ============================================================
# HEALTH
# ============================================================

@app.get(
    "/v1/healthz",
    response_model=HealthResponse,
)
def healthz():

    contexts = {
        "category": len(context_store.all("category")),
        "merchant": len(context_store.all("merchant")),
        "customer": len(context_store.all("customer")),
        "trigger": len(context_store.all("trigger")),
    }

    return HealthResponse(
        status="ok",
        uptime_seconds=round(monotonic() - START_TIME, 3),
        contexts_loaded=contexts,
    )


# ============================================================
# METADATA
# ============================================================

@app.get(
    "/v1/metadata",
    response_model=MetadataResponse,
)
def metadata():

    return MetadataResponse(
        team_name=TEAM_NAME,
        team_members=TEAM_MEMBERS,
        model=MODEL_NAME,
        approach=APPROACH,
        contact_email=CONTACT_EMAIL,
        version=APP_VERSION,
        submitted_at=datetime.now(timezone.utc).isoformat(),
    )


# ============================================================
# CONTEXT PUSH
# ============================================================

@app.post(
    "/v1/context",
    response_model=ContextResponse,
)
def receive_context(context: ContextPayload):

    # --------------------------------------------------------
    # Validate scope
    # --------------------------------------------------------

    if context.scope not in VALID_SCOPES:
        raise HTTPException(
            status_code=400,
            detail={
                "accepted": False,
                "reason": "invalid_scope",
                "details": (
                    f"Invalid scope '{context.scope}'. "
                    f"Expected one of {sorted(VALID_SCOPES)}."
                ),
            },
        )

    # --------------------------------------------------------
    # Validate version
    # --------------------------------------------------------

    if context.version < 1:
        raise HTTPException(
            status_code=400,
            detail={
                "accepted": False,
                "reason": "invalid_version",
                "details": "version must be >= 1",
            },
        )

    # --------------------------------------------------------
    # Check existing version before upsert
    # --------------------------------------------------------

    existing = context_store.get(
        context.scope,
        context.context_id,
    )

    if existing is not None:

        # Stale update
        if context.version < existing.version:

            raise HTTPException(
                status_code=409,
                detail={
                    "accepted": False,
                    "reason": "stale_version",
                    "current_version": existing.version,
                },
            )

    # --------------------------------------------------------
    # Store context
    # --------------------------------------------------------

    try:
        result = context_store.upsert(context)

    except ValueError as exc:

        raise HTTPException(
            status_code=409,
            detail={
                "accepted": False,
                "reason": "stale_version",
                "details": str(exc),
            },
        )

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return ContextResponse(
        accepted=True,
        ack_id=f"ack_{uuid4().hex[:12]}",
        stored_at=datetime.now(timezone.utc).isoformat(),
    )


# ============================================================
# TICK
# ============================================================

@app.post(
    "/v1/tick",
    response_model=TickResponse,
)
def tick(request: TickRequest):

    """
    Periodic wake-up endpoint.

    Current milestone:
    - receives active trigger hints
    - verifies trigger contexts exist
    - does not proactively send messages yet

    Decision engine will be connected here next.
    """

    actions = []

    for trigger_id in request.available_triggers:

        trigger = context_store.get(
            "trigger",
            trigger_id,
        )

        if trigger is None:
            continue

        # ----------------------------------------------------
        # No proactive action yet.
        #
        # Trigger ranking + suppression + decision engine
        # will be inserted here.
        # ----------------------------------------------------

        continue

    return TickResponse(
        actions=actions,
    )


# ============================================================
# REPLY
# ============================================================

@app.post(
    "/v1/reply",
    response_model=ReplyResponse,
)
def reply(request: ReplyRequest):

    """
    Conversation endpoint.

    Current milestone:
    safe WAIT response.

    Conversation FSM and intent handling will be
    connected here later.
    """

    return ReplyResponse(
        action="wait",
        wait_seconds=1800,
        rationale=(
            "Conversation policy is not enabled yet. "
            "Waiting for the conversation engine."
        ),
    )


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "name": "Magicpin Vera AI",
        "status": "running",
        "version": APP_VERSION,
    }