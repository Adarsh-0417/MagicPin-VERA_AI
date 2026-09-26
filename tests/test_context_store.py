from app.context_store import ContextStore
from app.models import ContextPayload


def test_context_created():

    store = ContextStore()

    context = ContextPayload(
        scope="merchant",
        context_id="merchant_001",
        version=1,
        payload={
            "merchant_id": "merchant_001",
            "name": "Test Merchant"
        }
    )

    result = store.upsert(context)

    assert result == "created"

    saved = store.get(
        "merchant",
        "merchant_001"
    )

    assert saved is not None
    assert saved.version == 1


def test_same_version_is_idempotent():

    store = ContextStore()

    context = ContextPayload(
        scope="merchant",
        context_id="merchant_001",
        version=1,
        payload={
            "merchant_id": "merchant_001"
        }
    )

    assert store.upsert(context) == "created"

    assert store.upsert(context) == "idempotent"


def test_higher_version_updates():

    store = ContextStore()

    v1 = ContextPayload(
        scope="merchant",
        context_id="merchant_001",
        version=1,
        payload={
            "name": "Old Name"
        }
    )

    v2 = ContextPayload(
        scope="merchant",
        context_id="merchant_001",
        version=2,
        payload={
            "name": "New Name"
        }
    )

    assert store.upsert(v1) == "created"

    assert store.upsert(v2) == "updated"

    saved = store.get(
        "merchant",
        "merchant_001"
    )

    assert saved.version == 2
    assert saved.payload["name"] == "New Name"


def test_lower_version_is_rejected():

    store = ContextStore()

    v2 = ContextPayload(
        scope="merchant",
        context_id="merchant_001",
        version=2,
        payload={
            "name": "Current"
        }
    )

    v1 = ContextPayload(
        scope="merchant",
        context_id="merchant_001",
        version=1,
        payload={
            "name": "Old"
        }
    )

    store.upsert(v2)

    try:
        store.upsert(v1)
        assert False, "Expected stale version error"

    except ValueError as exc:

        assert "stale_version" in str(exc)