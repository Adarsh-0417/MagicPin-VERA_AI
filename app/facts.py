from typing import Dict, Any

from app.context_resolver import CompositionContext


class FactsExtractor:

    def extract(
        self,
        context: CompositionContext
    ) -> Dict[str, Any]:

        category = context.category.payload
        merchant = context.merchant.payload
        trigger = context.trigger.payload

        customer = (
            context.customer.payload
            if context.customer
            else None
        )

        merchant_identity = merchant.get(
            "identity",
            {}
        )

        merchant_performance = merchant.get(
            "performance",
            {}
        )

        customer_identity = (
            customer.get("identity", {})
            if customer
            else {}
        )

        customer_relationship = (
            customer.get("relationship", {})
            if customer
            else {}
        )

        trigger_payload = trigger.get(
            "payload",
            {}
        )

        return {

            "category": {
                "slug": category.get(
                    "slug"
                ),
                "name": category.get(
                    "name"
                ),
                "primary_goal": category.get(
                    "primary_goal"
                ),
                "voice": category.get(
                    "voice"
                ),
            },

            "merchant": {
                "merchant_id": merchant.get(
                    "merchant_id"
                ),

                "name": (
                    merchant_identity.get(
                        "name"
                    )
                    or merchant.get("name")
                ),

                "city": (
                    merchant_identity.get(
                        "city"
                    )
                    or merchant.get("city")
                ),

                "rating": (
                    merchant_performance.get(
                        "rating"
                    )
                    or merchant.get("rating")
                ),

                "avg_order_value": merchant.get(
                    "avg_order_value"
                ),

                "identity": merchant_identity,

                "performance": merchant_performance,
            },

            "trigger": {
                "id": trigger.get(
                    "id"
                ),

                "kind": trigger.get(
                    "kind"
                ),

                "urgency": trigger.get(
                    "urgency"
                ),

                "title": trigger.get(
                    "title"
                ),

                "description": trigger.get(
                    "description"
                ),

                "source": trigger.get(
                    "source"
                ),

                "expires_at": trigger.get(
                    "expires_at"
                ),

                "suppression_key": trigger.get(
                    "suppression_key"
                ),

                "payload": trigger_payload,

                # Useful normalized recall fields
                "service_due": trigger_payload.get(
                    "service_due"
                ),

                "last_service_date": trigger_payload.get(
                    "last_service_date"
                ),

                "due_date": trigger_payload.get(
                    "due_date"
                ),

                "available_slots": trigger_payload.get(
                    "available_slots",
                    []
                ),
            },

            "customer": {

                "customer_id": customer.get(
                    "customer_id"
                ),

                "name": customer_identity.get(
                    "name"
                ),

                "language_pref": customer_identity.get(
                    "language_pref"
                ),

                "visits_total": customer_relationship.get(
                    "visits_total"
                ),

                "last_visit": customer_relationship.get(
                    "last_visit"
                ),

                "first_visit": customer_relationship.get(
                    "first_visit"
                ),

                "services_received": customer_relationship.get(
                    "services_received",
                    []
                ),

                "state": customer.get(
                    "state"
                ),

                "preferences": customer.get(
                    "preferences",
                    {}
                ),

                "consent": customer.get(
                    "consent",
                    {}
                ),
            } if customer else None,
        }