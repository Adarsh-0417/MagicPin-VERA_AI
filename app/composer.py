from app.context_resolver import CompositionContext
from app.facts import FactsExtractor
from app.playbooks import (
    get_category_playbook,
    get_trigger_playbook,
)


class Composer:

    def __init__(self):
        self.facts_extractor = FactsExtractor()

    def _safe(self, value, fallback=""):
        if value is None:
            return fallback

        return str(value).strip()

    def _active_offer(self, merchant):
        offers = merchant.get("offers", [])

        for offer in offers:

            if not isinstance(offer, dict):
                continue

            status = str(
                offer.get("status", "")
            ).lower()

            if status == "active":
                return offer

        return None

    def _offer_text(self, offer):
        if not offer:
            return ""

        title = (
            offer.get("title")
            or offer.get("name")
        )

        price = offer.get("price")

        if title and price:
            return f"{title} @ ₹{price}"

        if title:
            return str(title)

        return ""

    def compose(self, context: CompositionContext) -> dict:

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
            "the business"
        )

        trigger_kind = self._safe(
            trigger.get("kind"),
            "general_update"
        )

        playbook = get_category_playbook(
            category_slug
        )

        trigger_playbook = get_trigger_playbook(
            trigger_kind
        )

        # ======================================================
        # CUSTOMER RECALL
        # ======================================================

        if (
            customer
            and trigger_kind == "recall_due"
        ):

            customer_name = self._safe(
                customer.get("name"),
                "there"
            )

            language = self._safe(
                customer.get("language_pref"),
                "en"
            ).lower()

            service_due = self._safe(
                trigger.get("service_due"),
                "service"
            )

            last_service = self._safe(
                trigger.get("last_service_date")
                or customer.get("last_visit")
            )

            slots = trigger.get(
                "available_slots",
                []
            )

            slot_labels = []

            for slot in slots[:2]:

                if isinstance(slot, dict):

                    label = slot.get(
                        "label"
                    )

                    if label:
                        slot_labels.append(
                            label
                        )

            slot_text = ""

            if slot_labels:

                slot_text = (
                    " | ".join(slot_labels)
                )

            offer = self._active_offer(
                merchant
            )

            offer_text = self._offer_text(
                offer
            )

            # ----------------------------------------------
            # English
            # ----------------------------------------------

            if language == "en":

                body = (
                    f"Hi {customer_name}, "
                    f"{merchant_name} here. "
                    f"Your {service_due.replace('_', ' ')} "
                    f"recall is due."
                )

                if last_service:

                    body += (
                        f" Your last service was "
                        f"{last_service}."
                    )

                if slot_text:

                    body += (
                        f" Available slots: "
                        f"{slot_text}."
                    )

                if offer_text:

                    body += (
                        f" {offer_text} is currently available."
                    )

                body += (
                    " Reply with 1 or 2 for a slot, "
                    "or tell us a time that works."
                )

            # ----------------------------------------------
            # Hindi-English mix
            # ----------------------------------------------

            elif "hi-en" in language or language == "hi":

                body = (
                    f"Hi {customer_name}, "
                    f"{merchant_name} here 🦷 "
                    f"Apka {service_due.replace('_', ' ')} "
                    f"recall due hai."
                )

                if last_service:

                    body += (
                        f" Last visit "
                        f"{last_service} ko tha."
                    )

                if slot_text:

                    body += (
                        f" Apke liye slots available hain: "
                        f"{slot_text}."
                    )

                if offer_text:

                    body += (
                        f" {offer_text} bhi available hai."
                    )

                body += (
                    " Reply 1 ya 2 karke slot choose karein, "
                    "ya apna convenient time bata dein."
                )

            else:

                body = (
                    f"Hi {customer_name}, "
                    f"{merchant_name} here. "
                    f"Your {service_due.replace('_', ' ')} "
                    f"recall is due."
                )

                if slot_text:

                    body += (
                        f" Available slots: {slot_text}."
                    )

                if offer_text:

                    body += (
                        f" {offer_text} is available."
                    )

                body += (
                    " Reply with your preferred slot."
                )

            body = " ".join(
                body.split()
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
                    offer_text,
                ],

                "facts": facts,

                "rationale": (
                    "Customer-scoped recall using "
                    "customer identity, language preference, "
                    "trigger recall data, available slots "
                    "and active merchant offer when available."
                ),
            }

        # ======================================================
        # GENERIC CUSTOMER MESSAGE
        # ======================================================

        if customer:

            customer_name = self._safe(
                customer.get("name"),
                "your customer"
            )

            title = self._safe(
                trigger.get("title"),
                trigger_kind.replace(
                    "_",
                    " "
                ).title()
            )

            description = self._safe(
                trigger.get("description")
            )

            body = (
                f"Hi {merchant_name}, "
                f"{title}. "
            )

            if description:
                body += f"{description} "

            body += (
                f"This looks relevant for "
                f"{customer_name}. "
                f"Would you like to explore this?"
            )

        # ======================================================
        # MERCHANT MESSAGE
        # ======================================================

        else:

            title = self._safe(
                trigger.get("title"),
                trigger_kind.replace(
                    "_",
                    " "
                ).title()
            )

            description = self._safe(
                trigger.get("description")
            )

            owner_name = self._safe(
                merchant.get("owner_first_name")
            )

            greeting = (
                owner_name
                or merchant_name
            )

            body = (
                f"{greeting}, "
                f"{title}. "
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