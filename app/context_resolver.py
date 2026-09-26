   from dataclasses import dataclass
from typing import Optional

from app.context_store import ContextStore
from app.models import ContextRecord


@dataclass
class CompositionContext:
    category: ContextRecord
    merchant: ContextRecord
    trigger: ContextRecord
    customer: Optional[ContextRecord] = None


class ContextResolver:

    def __init__(self, store: ContextStore):
        self.store = store

    def resolve_trigger(
        self,
        trigger_id: str
    ) -> CompositionContext:

        trigger = self.store.require(
            "trigger",
            trigger_id
        )

        trigger_payload = trigger.payload

        merchant_id = trigger_payload.get("merchant_id")

        if not merchant_id:
            raise ValueError(
                f"Trigger {trigger_id} does not contain merchant_id"
            )

        merchant = self.store.require(
            "merchant",
            merchant_id
        )

        merchant_payload = merchant.payload

        category_slug = merchant_payload.get("category_slug")

        if not category_slug:
            raise ValueError(
                f"Merchant {merchant_id} does not contain category_slug"
            )

        category = self.store.require(
            "category",
            category_slug
        )

        customer = None

        customer_id = trigger_payload.get("customer_id")

        if customer_id:
            customer = self.store.get(
                "customer",
                customer_id
            )

        return CompositionContext(
            category=category,
            merchant=merchant,
            trigger=trigger,
            customer=customer
        )