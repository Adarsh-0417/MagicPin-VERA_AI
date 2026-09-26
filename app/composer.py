from app.context_resolver import CompositionContext
from app.facts import FactsExtractor
from app.playbooks import (
    get_category_playbook,
    get_trigger_playbook
)


class Composer:

    def __init__(self):
        self.facts_extractor = FactsExtractor()

    def compose(
        self,
        context: CompositionContext
    ) -> dict:

        facts = self.facts_extractor.extract(
            context
        )

        category = facts["category"]
        merchant = facts["merchant"]
        trigger = facts["trigger"]
        customer = facts.get("customer")

        category_slug = (
            category.get("slug")
            or "business"
        )

        category_name = (
            category.get("name")
            or category_slug
        )

        merchant_name = (
            merchant.get("name")
            or "there"
        )

        trigger_kind = (
            trigger.get("kind")
            or "general_update"
        )

        trigger_title = (
            trigger.get("title")
            or trigger_kind.replace("_", " ").title()
        )

        trigger_description = (
            trigger.get("description")
            or ""
        ).strip()

        category_playbook = get_category_playbook(
            category_slug
        )

        trigger_playbook = get_trigger_playbook(
            trigger_kind
        )

        # ---------------------------------------------------------
        # Customer-specific message
        # ---------------------------------------------------------

        if customer:

            customer_name = (
                customer.get("name")
                or "your customer"
            )

            body = (
                f"Hi {merchant_name}, "
                f"quick update about {customer_name}. "
                f"{trigger_title}: "
            )

            if trigger_description:
                body += (
                    f"{trigger_description} "
                )

            body += (
                "This could be a useful opportunity "
                "to reconnect. Would you like to explore "
                "a next step?"
            )

        # ---------------------------------------------------------
        # Merchant-only message
        # ---------------------------------------------------------

        else:

            body = (
                f"Hi {merchant_name}, "
                f"quick update: {trigger_title}. "
            )

            if trigger_description:
                body += (
                    f"{trigger_description} "
                )

            body += (
                f"This looks relevant for your "
                f"{category_name.lower()} business. "
                f"Would you like to explore a next step?"
            )

        return {
            "body": body.strip(),

            "cta": category_playbook.get(
                "cta",
                "Reply to discuss"
            ),

            "template_name": None,

            "template_params": [],

            "facts": facts,

            "rationale": (
                f"Composed for category="
                f"{category_slug}, "
                f"trigger={trigger_kind}. "
                f"Goal: "
                f"{trigger_playbook['goal']}."
            )
        }