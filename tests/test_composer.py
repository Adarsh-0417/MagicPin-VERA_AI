from app.composer import Composer
from app.context_store import ContextStore
from app.context_resolver import ContextResolver
from app.models import ContextPayload


def build_recall_context():

    store = ContextStore()

    store.upsert(
        ContextPayload(
            scope="category",
            context_id="dentists",
            version=1,
            payload={
                "slug": "dentists",
                "name": "Dentists",
                "primary_goal": "patient engagement",
                "voice": "professional and warm"
            }
        )
    )

    store.upsert(
        ContextPayload(
            scope="merchant",
            context_id="merchant_001",
            version=1,
            payload={
                "merchant_id": "merchant_001",
                "category_slug": "dentists",
                "identity": {
                    "name": "Dr. Meera's Dental Clinic",
                    "owner_first_name": "Meera",
                    "city": "Delhi"
                },
                "offers": [
                    {
                        "title": "Dental Cleaning",
                        "price": 299,
                        "status": "active"
                    }
                ]
            }
        )
    )

    store.upsert(
        ContextPayload(
            scope="customer",
            context_id="customer_001",
            version=1,
            payload={
                "customer_id": "customer_001",
                "identity": {
                    "name": "Priya",
                    "language_pref": "hi-en mix"
                },
                "relationship": {
                    "last_visit": "2026-05-12",
                    "visits_total": 3
                },
                "preferences": {
                    "reminder_opt_in": True
                },
                "consent": {
                    "marketing": True
                }
            }
        )
    )

    store.upsert(
        ContextPayload(
            scope="trigger",
            context_id="trigger_001",
            version=1,
            payload={
                "id": "trigger_001",
                "kind": "recall_due",
                "merchant_id": "merchant_001",
                "customer_id": "customer_001",
                "urgency": 3,
                "payload": {
                    "service_due": "6_month_cleaning",
                    "last_service_date": "2026-05-12",
                    "due_date": "2026-11-12",
                    "available_slots": [
                        {
                            "iso": "2026-11-05T18:00:00+05:30",
                            "label": "Wed 5 Nov, 6pm"
                        },
                        {
                            "iso": "2026-11-06T17:00:00+05:30",
                            "label": "Thu 6 Nov, 5pm"
                        }
                    ]
                }
            }
        )
    )

    resolver = ContextResolver(store)

    return resolver.resolve_trigger(
        "trigger_001"
    )


def test_recall_composer_uses_customer_name():

    context = build_recall_context()

    composer = Composer()

    result = composer.compose(
        context
    )

    body = result["body"]

    assert "Priya" in body


def test_recall_composer_uses_slots():

    context = build_recall_context()

    composer = Composer()

    result = composer.compose(
        context
    )

    body = result["body"]

    assert "Wed 5 Nov, 6pm" in body
    assert "Thu 6 Nov, 5pm" in body


def test_recall_composer_uses_offer():

    context = build_recall_context()

    composer = Composer()

    result = composer.compose(
        context
    )

    body = result["body"]

    assert "Dental Cleaning" in body
    assert "299" in body


def test_recall_has_template():

    context = build_recall_context()

    composer = Composer()

    result = composer.compose(
        context
    )

    assert (
        result["template_name"]
        == "merchant_recall_reminder_v1"
    )

    assert (
        result["cta"]
        == "multi_choice_slot"
    )