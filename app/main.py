from datetime import datetime, timezone
from time import monotonic
from uuid import uuid4
from app.conversation_store import ConversationStore
from app.reply_fsm import ReplyFSM
from app.conversation_store import ConversationStore
from app.reply_fsm import ReplyFSM
from app.reply_fsm import ReplyFSM
from app.composer import Composer
from app.validator import ActionValidator
from app.trigger_ranker import TriggerRanker
from app.suppression import SuppressionLedger
from app.decision_engine import DecisionEngine
from fastapi import FastAPI, HTTPException
from pathlib import Path
from app.dataset_loader import DatasetLoader
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

composer = Composer()
action_validator = ActionValidator()

suppression_ledger = SuppressionLedger()

reply_fsm = ReplyFSM()

trigger_ranker = TriggerRanker(
    context_store
)

conversation_store = ConversationStore()
reply_fsm = ReplyFSM()

decision_engine = DecisionEngine(
    store=context_store,
    resolver=context_resolver,
    suppression=suppression_ledger,
)

# ============================================================
# DATASET
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "dataset" / "expanded"

dataset_loader = DatasetLoader(
    dataset_dir=str(DATASET_DIR),
    store=context_store,
)

DATASET_COUNTS = dataset_loader.load_all()

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
    response_model=ContextResponse
)
def upsert_context(
    request: ContextPayload
):
    if request.scope not in VALID_SCOPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scope: {request.scope}"
        )

    try:
        result = context_store.upsert(request)

    except ValueError as exc:

        raise HTTPException(
            status_code=409,
            detail={
                "reason": "stale_version",
                "details": str(exc),
                "current_version": (
                    context_store
                    .get(
                        request.scope,
                        request.context_id
                    )
                    .version
                )
            }
        )

    stored = context_store.get(
        request.scope,
        request.context_id
    )

    return ContextResponse(
        accepted=True,
        ack_id=f"ack_{request.scope}_{request.context_id}_{stored.version}",
        stored_at=datetime.now(
            timezone.utc
        ).isoformat(),
        reason=result,
        current_version=stored.version
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

@app.post("/v1/tick", response_model=TickResponse)
def tick(request: TickRequest):

    ranked_triggers = trigger_ranker.rank(
        request.available_triggers
    )

    actions = []

    for trigger, score in ranked_triggers:

        result = decision_engine.evaluate(
            trigger.context_id,
            now=request.now
        )

        if result.action != "send":
            continue

        context = result.context

        trigger_payload = context.trigger.payload
        merchant_payload = context.merchant.payload

        merchant_id = merchant_payload.get("merchant_id")
        customer_id = trigger_payload.get("customer_id")

        composed = composer.compose(context)

        valid, validation_reason = action_validator.validate(
            composed
        )

        if not valid:
            continue

        conversation_id = f"conv_{trigger.context_id}"

        action = Action(
            conversation_id=conversation_id,
            merchant_id=merchant_id,
            customer_id=customer_id,

            send_as=(
                "merchant_on_behalf"
                if customer_id
                else "vera"
            ),

            trigger_id=trigger.context_id,

            template_name=composed.get(
                "template_name"
            ),

            template_params=composed.get(
                "template_params",
                []
            ),

            body=composed["body"],

            cta=composed.get("cta"),

            suppression_key=trigger_payload.get(
                "suppression_key"
            ),

            rationale=(
                f"{result.rationale} "
                f"Trigger score={score:.2f}. "
                f"{composed['rationale']} "
                f"Validation={validation_reason}."
            ),
        )

        actions.append(action)

        conversation_store.get_or_create(
            conversation_id=conversation_id,
            merchant_id=merchant_id,
            customer_id=customer_id
        )

        conversation_store.set_trigger(
            conversation_id=conversation_id,
            trigger_id=trigger.context_id
        )

        suppression_key = trigger_payload.get(
            "suppression_key"
        )

        if suppression_key:
            suppression_ledger.mark_sent(
                suppression_key
            )

        if len(actions) >= 20:
            break

    return TickResponse(actions=actions)
# ============================================================
# REPLY
# ============================================================

@app.post(
    "/v1/reply",
    response_model=ReplyResponse
)
def reply(request: ReplyRequest):

    conversation = conversation_store.get_or_create(
        conversation_id=request.conversation_id,
        merchant_id=request.merchant_id,
        customer_id=request.customer_id
    )

    # Store incoming message BEFORE FSM evaluation
    # so repeated-message detection sees the current turn.
    conversation = conversation_store.add_message(
        conversation_id=request.conversation_id,
        role=request.from_role,
        message=request.message
    )

    decision = reply_fsm.evaluate(
        message=request.message,
        conversation=conversation
    )

    if decision.action == "end":

        conversation_store.end(
            request.conversation_id
        )

    return ReplyResponse(
        action=decision.action,
        body=decision.body,
        cta=decision.cta,
        wait_seconds=decision.wait_seconds,
        rationale=decision.rationale
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