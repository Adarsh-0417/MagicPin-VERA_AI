from app.context_resolver import CompositionContext
from app.facts import FactsExtractor
from app.llm_composer import LLMComposer
from app.playbooks import (
    get_category_playbook,
    get_trigger_playbook
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

    def _active_offer(
        self,
        merchant
    ):
        offers = merchant.get(
            "offers",
            []
        )

        for offer in offers:

            if not isinstance(
                offer,
                dict
            ):
                continue

            status = str(
                offer.get(
                    "status",
                    ""
                )
            ).lower()

            if status == "active":
                return offer

        return None

    def _offer_text(
        self,
        offer
    ):
        if not offer:
            return ""

        title = (
            offer.get("title")
            or offer.get("name")
        )

        price = offer.get(
            "price"
        )

        if title and price:
            price_text = str(
                price
            )

            if "₹" in price_text:
                return f"{title} @ {price_text}"

            return f"{title} @ ₹{price_text}"

        if title:
            return str(title)

        return ""

    def _slot_text(
        self,
        slots
    ):
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
                        str(label)
                    )

        return " | ".join(
            labels
        )

    def _merchant_greeting(
        self,
        merchant
    ):
        owner_name = self._safe(
            merchant.get(
                "owner_first_name"
            )
        )

        merchant_name = self._safe(
            merchant.get(
                "name"
            ),
            "there"
        )

        return owner_name or merchant_name

    def _generic_merchant_message(
        self,
        facts,
        playbook,
        trigger_playbook
    ):
        merchant = facts["merchant"]
        trigger = facts["trigger"]
        category = facts["category"]

        greeting = self._merchant_greeting(
            merchant
        )

        title = self._safe(
            trigger.get(
                "title"
            ),
            trigger.get(
                "kind",
                "Business update"
            ).replace(
                "_",
                " "
            ).title()
        )

        description = self._safe(
            trigger.get(
                "description"
            )
        )

        body = (
            f"{greeting}, {title}."
        )

        if description:
            body += (
                f" {description}"
            )

        body += (
            f" This is relevant to your "
            f"{self._safe(category.get('name'), 'business').lower()} "
            f"business. "
        )

        body += (
            "Would you like to explore a next step?"
        )

        return {
            "body": " ".join(
                body.split()
            ),
            "cta": playbook.get(
                "cta",
                "Reply to discuss"
            ),
            "template_name": None,
            "template_params": [],
            "facts": facts,
            "rationale": (
                f"Grounded fallback composition for "
                f"category={category.get('slug')} "
                f"and trigger={trigger.get('kind')}. "
                f"Goal: {trigger_playbook['goal']}."
            )
        }

    def _compose_recall(
        self,
        facts
    ):
        merchant = facts["merchant"]
        trigger = facts["trigger"]
        customer = facts["customer"]

        customer_name = self._safe(
            customer.get(
                "name"
            ),
            "there"
        )

        language = self._safe(
            customer.get(
                "language_pref"
            ),
            "en"
        ).lower()

        merchant_name = self._safe(
            merchant.get(
                "name"
            ),
            "the clinic"
        )

        service_due = self._safe(
            trigger.get(
                "service_due"
            ),
            "service"
        ).replace(
            "_",
            " "
        )

        last_service = self._safe(
            trigger.get(
                "last_service_date"
            )
            or customer.get(
                "last_visit"
            )
        )

        slot_text = self._slot_text(
            trigger.get(
                "available_slots",
                []
            )
        )

        offer = self._active_offer(
            merchant
        )

        offer_text = self._offer_text(
            offer
        )

        if language == "en":

            body = (
                f"Hi {customer_name}, "
                f"{merchant_name} here. "
                f"Your {service_due} recall is due."
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
                    f" {offer_text} "
                    f"is currently available."
                )

            body += (
                " Reply with 1 or 2 for a slot, "
                "or tell us a time that works."
            )

        elif (
            "hi-en" in language
            or language == "hi"
        ):

            body = (
                f"Hi {customer_name}, "
                f"{merchant_name} here 🦷 "
                f"Apka {service_due} recall "
                f"due hai."
            )

            if last_service:
                body += (
                    f" Last visit "
                    f"{last_service} ko tha."
                )

            if slot_text:
                body += (
                    f" Apke liye slots "
                    f"available hain: "
                    f"{slot_text}."
                )

            if offer_text:
                body += (
                    f" {offer_text} "
                    f"bhi available hai."
                )

            body += (
                " Reply 1 ya 2 karke slot choose karein, "
                "ya apna convenient time bata dein."
            )

        else:

            body = (
                f"Hi {customer_name}, "
                f"{merchant_name} here. "
                f"Your {service_due} recall is due."
            )

            if slot_text:
                body += (
                    f" Available slots: "
                    f"{slot_text}."
                )

            if offer_text:
                body += (
                    f" {offer_text} is available."
                )

            body += (
                " Reply with your preferred slot."
            )

        return {
            "body": " ".join(
                body.split()
            ),
            "cta": "multi_choice_slot",
            "template_name": (
                "merchant_recall_reminder_v1"
            ),
            "template_params": [
                customer_name,
                merchant_name,
                service_due,
                slot_text,
                offer_text
            ],
            "facts": facts,
            "rationale": (
                "Customer recall composed using "
                "customer identity, language preference, "
                "recall data, available slots and active "
                "merchant offer."
            )
        }

    def _compose_customer_generic(
        self,
        facts
    ):
        merchant = facts["merchant"]
        trigger = facts["trigger"]
        customer = facts["customer"]

        customer_name = self._safe(
            customer.get(
                "name"
            ),
            "there"
        )

        merchant_name = self._safe(
            merchant.get(
                "name"
            ),
            "the business"
        )

        title = self._safe(
            trigger.get(
                "title"
            ),
            trigger.get(
                "kind",
                "Update"
            ).replace(
                "_",
                " "
            ).title()
        )

        description = self._safe(
            trigger.get(
                "description"
            )
        )

        body = (
            f"Hi {customer_name}, "
            f"{merchant_name} here. "
            f"{title}."
        )

        if description:
            body += (
                f" {description}"
            )

        body += (
            " Reply if you'd like to discuss this."
        )

        return {
            "body": " ".join(
                body.split()
            ),
            "cta": "Reply",
            "template_name": None,
            "template_params": [],
            "facts": facts,
            "rationale": (
                "Customer-facing message composed "
                "from available trigger and customer context "
                "without inventing unavailable details."
            )
        }

    def _compose_perf_dip(
        self,
        facts
    ):
        merchant = facts["merchant"]
        trigger = facts["trigger"]

        greeting = self._merchant_greeting(
            merchant
        )

        payload = trigger.get(
            "payload",
            {}
        )

        metric = (
            payload.get(
                "metric"
            )
            or payload.get(
                "metric_name"
            )
            or payload.get(
                "metric_or_topic"
            )
        )

        change = (
            payload.get(
                "change"
            )
            or payload.get(
                "delta"
            )
            or payload.get(
                "percentage_change"
            )
        )

        if metric and change:
            body = (
                f"{greeting}, {metric} has changed "
                f"by {change}. "
                "This may be worth a closer look. "
                "Want to review what changed and the next step?"
            )

        elif metric:
            body = (
                f"{greeting}, there is a performance "
                f"signal around {metric}. "
                "Want to review it and decide the next step?"
            )

        else:
            body = (
                f"{greeting}, there is a performance dip "
                "signal for your business. "
                "Want to review the details?"
            )

        return {
            "body": " ".join(
                body.split()
            ),
            "cta": "Review performance",
            "template_name": None,
            "template_params": [],
            "facts": facts,
            "rationale": (
                "Performance-dip message uses only "
                "metric information present in the trigger."
            )
        }

    def _compose_perf_spike(
        self,
        facts
    ):
        merchant = facts["merchant"]
        trigger = facts["trigger"]

        greeting = self._merchant_greeting(
            merchant
        )

        payload = trigger.get(
            "payload",
            {}
        )

        metric = (
            payload.get(
                "metric"
            )
            or payload.get(
                "metric_name"
            )
            or payload.get(
                "metric_or_topic"
            )
        )

        change = (
            payload.get(
                "change"
            )
            or payload.get(
                "delta"
            )
            or payload.get(
                "percentage_change"
            )
        )

        if metric and change:

            body = (
                f"{greeting}, nice movement on "
                f"{metric}: {change}. "
                "Want to look at what may be driving it "
                "and how to sustain it?"
            )

        elif metric:

            body = (
                f"{greeting}, {metric} is showing "
                "a positive performance signal. "
                "Want to review what is driving it?"
            )

        else:

            body = (
                f"{greeting}, there is a positive "
                "performance signal for your business. "
                "Want to see the details?"
            )

        return {
            "body": " ".join(
                body.split()
            ),
            "cta": "Review performance",
            "template_name": None,
            "template_params": [],
            "facts": facts,
            "rationale": (
                "Performance-spike message uses "
                "available trigger metrics without "
                "inventing performance values."
            )
        }

    def _compose_renewal(
        self,
        facts
    ):
        merchant = facts["merchant"]
        trigger = facts["trigger"]

        greeting = self._merchant_greeting(
            merchant
        )

        payload = trigger.get(
            "payload",
            {}
        )

        renewal_date = (
            payload.get(
                "renewal_date"
            )
            or payload.get(
                "due_date"
            )
        )

        plan = (
            payload.get(
                "plan"
            )
            or payload.get(
                "plan_name"
            )
        )

        details = []

        if plan:
            details.append(
                f"{plan}"
            )

        if renewal_date:
            details.append(
                f"renewal is due on {renewal_date}"
            )

        if details:

            body = (
                f"{greeting}, your "
                + " ".join(details)
                + ". Would you like to review the renewal?"
            )

        else:

            body = (
                f"{greeting}, your subscription "
                "has a renewal reminder. "
                "Would you like to review the details?"
            )

        return {
            "body": " ".join(
                body.split()
            ),
            "cta": "Review renewal",
            "template_name": None,
            "template_params": [],
            "facts": facts,
            "rationale": (
                "Renewal message uses only available "
                "plan and renewal-date fields."
            )
        }

    def _compose_external(
        self,
        facts
    ):
        merchant = facts["merchant"]
        trigger = facts["trigger"]

        greeting = self._merchant_greeting(
            merchant
        )

        payload = trigger.get(
            "payload",
            {}
        )

        topic = (
            payload.get(
                "topic"
            )
            or payload.get(
                "event"
            )
            or payload.get(
                "title"
            )
            or payload.get(
                "metric_or_topic"
            )
        )

        source = payload.get(
            "source"
        )

        detail = (
            payload.get(
                "description"
            )
            or payload.get(
                "detail"
            )
            or payload.get(
                "summary"
            )
        )

        body = (
            f"{greeting}, there's a relevant "
            f"{trigger.get('kind', 'update').replace('_', ' ')}"
        )

        if topic:
            body += (
                f": {topic}"
            )

        body += "."

        if detail:
            body += (
                f" {detail}"
            )

        if source:
            body += (
                f" Source: {source}."
            )

        body += (
            " Worth a look for your business?"
        )

        return {
            "body": " ".join(
                body.split()
            ),
            "cta": "Review update",
            "template_name": None,
            "template_params": [],
            "facts": facts,
            "rationale": (
                "External-trigger message uses available "
                "topic, detail and source fields without "
                "fabricating external facts."
            )
        }

    def compose(
        self,
        context: CompositionContext
    ):

        facts = self.facts_extractor.extract(
            context
        )

        category = facts["category"]
        merchant = facts["merchant"]
        trigger = facts["trigger"]
        customer = facts.get(
            "customer"
        )

        category_slug = self._safe(
            category.get(
                "slug"
            ),
            "business"
        )

        trigger_kind = self._safe(
            trigger.get(
                "kind"
            ),
            "general_update"
        )

        playbook = get_category_playbook(
            category_slug
        )

        trigger_playbook = get_trigger_playbook(
            trigger_kind
        )

        # -----------------------------------------
        # CUSTOMER RECALL
        # -----------------------------------------

        if (
            customer
            and trigger_kind == "recall_due"
        ):

            return self._compose_recall(
                facts
            )

        # -----------------------------------------
        # OTHER CUSTOMER TRIGGERS
        # -----------------------------------------

        if customer:

            return self._compose_customer_generic(
                facts
            )

        # -----------------------------------------
        # PERFORMANCE DIP
        # -----------------------------------------

        if trigger_kind == "perf_dip":

            return self._compose_perf_dip(
                facts
            )

        # -----------------------------------------
        # PERFORMANCE SPIKE
        # -----------------------------------------

        if trigger_kind == "perf_spike":

            return self._compose_perf_spike(
                facts
            )

        # -----------------------------------------
        # RENEWAL
        # -----------------------------------------

        if trigger_kind == "renewal_due":

            return self._compose_renewal(
                facts
            )

        # -----------------------------------------
        # EXTERNAL TRIGGERS
        # -----------------------------------------

        if trigger_kind in {
            "research_digest",
            "regulation_change",
            "festival_upcoming",
            "competitor_opened",
            "review_theme_emerged"
        }:

            return self._compose_external(
                facts
            )

        # -----------------------------------------
        # SAFE FALLBACK
        # -----------------------------------------

        return self._generic_merchant_message(
            facts,
            playbook,
            trigger_playbook
        )