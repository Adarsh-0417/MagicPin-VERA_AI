from app.context_resolver import CompositionContext
from app.facts import FactsExtractor
from app.playbooks import (
    get_category_playbook,
    get_trigger_playbook,
)


class Composer:

    def __init__(self):
        self.facts_extractor = FactsExtractor()

    def _safe(
        self,
        value,
        fallback=""
    ):
        if value is None:
            return fallback

        return str(value).strip()

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

        category_slug = self._safe(
            category.get("slug"),
            "business"
        )

        category_name = self._safe(
            category.get("name"),
            category_slug
        )

        merchant_name = self._safe(
            merchant.get("name"),
            "there"
        )

        trigger_kind = self._safe(
            trigger.get("kind"),
            "general_update"
        )

        title = self._safe(
            trigger.get("title")
        )

        description = self._safe(
            trigger.get("description")
        )

        playbook = get_category_playbook(
            category_slug
        )

        trigger_playbook = get_trigger_playbook(
            trigger_kind
        )

        # ======================================================
        # CUSTOMER-SCOPED RECALL
        # ======================================================

        if (
            customer
            and trigger_kind == "recall_due"
        ):

            customer_name = self._safe(
                customer.get("name"),
                "there"
            )

            last_service = self._safe(
                trigger.get(
                    "last_service_date"
                )
                or customer.get(
                    "last_visit"
                )
            )

            service_due = self._safe(
                trigger.get(
                    "service_due"
                ),
                "scheduled service"
            )

            slots = trigger.get(
                "available_slots",
                []
            )

            slot_text = ""

            if slots:

                labels = []

                for slot in slots[:2]:

                    if isinstance(
                        slot,
                        dict
                    ):

                        label = slot.get(
                            "label"
                        )

                        if label:
                            labels.append(
                                label
                            )

                if labels:

                    slot_text = (
                        " Available slots: "
                        + " or ".join(labels)
                        + "."
                    )

            body = (
                f"Hi {customer_name}, "
                f"{merchant_name}'s clinic here. "
                f"Your {service_due.replace('_', ' ')} "
                f"is due."
            )

            if last_service:

                body += (
                    f" Your last service was "
                    f"{last_service}."
                )

            body += slot_text

            body += (
                " Reply with the slot that works "
                "for you, or tell us a convenient time."
            )

            return {
                "body": body,

                "cta": "multi_choice_slot",

                "template_name": (
                    "merchant_recall_reminder_v1"
                ),

                "template_params": [
                    customer_name,
                    merchant_name,
                    service_due,
                    slot_text,
                ],

                "facts": facts,

                "rationale": (
                    "Customer-scoped recall composed "
                    "using customer identity, recall "
                    "payload and available appointment slots."
                ),
            }

        # ======================================================
        # CUSTOMER-SCOPED GENERIC
        # ======================================================

        if customer:

            customer_name = self._safe(
                customer.get("name"),
                "your customer"
            )

            body = (
                f"Hi {merchant_name}, "
                f"{title or trigger_kind.replace('_', ' ').title()}. "
            )

            if description:
                body += (
                    f"{description} "
                )

            body += (
                f"This looks relevant for "
                f"{customer_name}. "
                f"Would you like to explore this?"
            )

        # ======================================================
        # MERCHANT-SCOPED
        # ======================================================

        else:

            body = (
                f"Hi {merchant_name}, "
                f"{title or trigger_kind.replace('_', ' ').title()}. "
            )

            if description:

                body += (
                    f"{description} "
                )

            body += (
                f"This looks relevant to your "
                f"{category_name.lower()} business. "
                f"Would you like to explore a next step?"
            )

        body = " ".join(
            body.split()
        )

        return {
            "body": body,

            "cta": playbook.get(
                "cta",
                "Reply to discuss"
            ),

            "template_name": None,

            "template_params": [],

            "facts": facts,

            "rationale": (
                f"Message composed using "
                f"category={category_slug}, "
                f"trigger={trigger_kind}, "
                f"customer_context={bool(customer)}. "
                f"Goal: "
                f"{trigger_playbook['goal']}."
            ),
        }