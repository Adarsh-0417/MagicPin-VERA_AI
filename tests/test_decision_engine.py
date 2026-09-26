from app.context_store import ContextStore
from app.context_resolver import ContextResolver
from app.suppression import SuppressionLedger
from app.decision_engine import DecisionEngine

from app.models import ContextPayload


def build_engine():

    store = ContextStore()

    category = ContextPayload(
        scope="category",
        context_id="dentists",
        version=1,
        payload={
            "slug": "dentists",
            "name": "Dentists"
        }
    )

    merchant = ContextPayload(
        scope="merchant",
        context_id="merchant_001",
        version=1,
        payload={
            "merchant_id": "merchant_001",
            "category_slug": "dentists",
            "identity": {
                "name": "Test Dental Clinic"
            }
        }
    )

    customer = ContextPayload(
        scope="customer",
        context_id="customer_001",
        version=1,
        payload={
            "customer_id": "customer_001",
            "identity": {
                "name": "Priya"
            },
            "preferences": {
                "reminder_opt_in": True
            },
            "consent": {
                "marketing": True
            }
        }
    )

    trigger = ContextPayload(
        scope="trigger",
        context_id="trigger_001",
        version=1,
        payload={
            "id": "trigger_001",
            "kind": "recall_due",
            "merchant_id": "merchant_001",
            "customer_id": "customer_001",
            "urgency": 3,
            "suppression_key": "recall:test",
            "expires_at": "2099-01-01T00:00:00Z",
            "payload": {
                "service_due": "6_month_cleaning"
            }
        }
    )

    for context in [
        category,
        merchant,
        customer,
        trigger
    ]:
        store.upsert(context)

    resolver = ContextResolver(store)

    suppression = SuppressionLedger()

    engine = DecisionEngine(
        store,
        resolver,
        suppression
    )

    return engine, suppression


def test_active_trigger_can_send():

    engine, _ = build_engine()

    result = engine.evaluate(
        "trigger_001",
        now="2026-09-27T10:00:00Z"
    )

    assert result.action == "send"
    assert result.context is not None


def test_suppressed_trigger_waits():

    engine, suppression = build_engine()

    suppression.mark_sent(
        "recall:test"
    )

    result = engine.evaluate(
        "trigger_001"
    )

    assert result.action == "wait"


def test_customer_without_reminder_opt_in_waits():

    engine, _ = build_engine()

    customer = engine.store.get(
        "customer",
        "customer_001"
    )

    customer.payload["preferences"][
        "reminder_opt_in"
    ] = False

    result = engine.evaluate(
        "trigger_001"
    )

    assert result.action == "wait"
    assert "opted in" in result.rationale


def test_expired_trigger_waits():

    engine, _ = build_engine()

    result = engine.evaluate(
        "trigger_001",
        now="2100-01-01T00:00:00Z"
    )

    assert result.action == "wait"
    assert "expired" in result.rationale.lower()