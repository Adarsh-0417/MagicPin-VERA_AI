from typing import Dict, Any
from app.context_resolver import CompositionContext


class FactsExtractor:

    def extract(self, context: CompositionContext) -> Dict[str, Any]:
        category = context.category.payload
        merchant = context.merchant.payload
        trigger = context.trigger.payload
        customer = context.customer.payload if context.customer else {}

        facts = {
            "category": {
                "slug": category.get("slug"),
                "name": category.get("name"),
                "primary_goal": category.get("primary_goal"),
            },

            "merchant": {
                "merchant_id": merchant.get("merchant_id"),
                "name": merchant.get("name"),
                "city": merchant.get("city"),
                "rating": merchant.get("rating"),
                "avg_order_value": merchant.get("avg_order_value"),
            },

            "trigger": {
                "id": trigger.get("id"),
                "kind": trigger.get("kind"),
                "urgency": trigger.get("urgency"),
                "title": trigger.get("title"),
                "description": trigger.get("description"),
            },

            "customer": {
                "customer_id": customer.get("customer_id"),
                "name": customer.get("name"),
                "visit_count": customer.get("visit_count"),
                "last_visit": customer.get("last_visit"),
            } if customer else None,
        }

        return facts