from app.context_resolver import CompositionContext
from app.facts import FactsExtractor
from app.playbooks import get_category_playbook, get_trigger_playbook


class Composer:

    def __init__(self):
        self.facts_extractor = FactsExtractor()

    def compose(self, context: CompositionContext) -> dict:
        facts = self.facts_extractor.extract(context)

        category_slug = facts["category"]["slug"]
        category_name = facts["category"]["name"] or category_slug

        merchant_name = (
            facts["merchant"]["name"]
            or "there"
        )

        trigger = facts["trigger"]
        trigger_kind = trigger["kind"]
        trigger_title = trigger["title"]
        trigger_description = trigger["description"]

        category_playbook = get_category_playbook(category_slug)
        trigger_playbook = get_trigger_playbook(trigger_kind)

        customer = facts.get("customer")

        if customer and customer.get("name"):
            customer_name = customer["name"]

            body = (
                f"Hi {merchant_name}, quick update: {trigger_title}. "
                f"{trigger_description} "
                f"We noticed this may be relevant for {customer_name}. "
                f"Would you like to explore a next step?"
            )

        else:
            body = (
                f"Hi {merchant_name}, quick update: {trigger_title}. "
                f"{trigger_description} "
                f"This looks relevant for your {category_name.lower()} business. "
                f"Would you like to explore a next step?"
            )

        return {
            "body": body,
            "cta": category_playbook["cta"],
            "template_name": None,
            "template_params": [],
            "facts": facts,
            "rationale": (
                f"Composed for {category_slug} category using "
                f"{trigger_kind} trigger. "
                f"Goal: {trigger_playbook['goal']}."
            ),
        }