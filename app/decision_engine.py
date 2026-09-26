from datetime import datetime, timezone
from typing import Optional

from app.context_resolver import CompositionContext, ContextResolver
from app.context_store import ContextStore
from app.suppression import SuppressionLedger


class DecisionResult:

    def __init__(
        self,
        action: str,
        rationale: str,
        context: Optional[CompositionContext] = None
    ):
        self.action = action
        self.rationale = rationale
        self.context = context


class DecisionEngine:

    def __init__(
        self,
        store: ContextStore,
        resolver: ContextResolver,
        suppression: SuppressionLedger
    ):
        self.store = store
        self.resolver = resolver
        self.suppression = suppression

    def _is_expired(
        self,
        expires_at: Optional[str],
        now: Optional[str]
    ) -> bool:

        if not expires_at:
            return False

        try:

            expiry = datetime.fromisoformat(
                expires_at.replace("Z", "+00:00")
            )

            current_time = (
                datetime.fromisoformat(
                    now.replace("Z", "+00:00")
                )
                if now
                else datetime.now(timezone.utc)
            )

            return current_time >= expiry

        except (ValueError, TypeError):

            return False

    def evaluate(
        self,
        trigger_id: str,
        now: Optional[str] = None
    ) -> DecisionResult:

        # -----------------------------------------
        # 1. TRIGGER EXISTS?
        # -----------------------------------------

        trigger = self.store.get(
            "trigger",
            trigger_id
        )

        if trigger is None:

            return DecisionResult(
                "wait",
                "Trigger context is unavailable."
            )

        payload = trigger.payload

        # -----------------------------------------
        # 2. SUPPRESSION CHECK
        # -----------------------------------------

        suppression_key = payload.get(
            "suppression_key"
        )

        if (
            suppression_key
            and self.suppression.is_suppressed(
                suppression_key
            )
        ):

            return DecisionResult(
                "wait",
                "Trigger is suppressed because the same suppression key was already used."
            )

        # -----------------------------------------
        # 3. EXPIRY CHECK
        # -----------------------------------------

        expires_at = payload.get(
            "expires_at"
        )

        if self._is_expired(
            expires_at,
            now
        ):

            return DecisionResult(
                "wait",
                f"Trigger expired at {expires_at}."
            )

        # -----------------------------------------
        # 4. RESOLVE ALL REQUIRED CONTEXTS
        # -----------------------------------------

        try:

            context = self.resolver.resolve_trigger(
                trigger_id
            )

        except (KeyError, ValueError) as exc:

            return DecisionResult(
                "wait",
                f"Required context unavailable: {exc}"
            )

        # -----------------------------------------
        # 5. CUSTOMER CONTEXT REQUIRED?
        # -----------------------------------------

        customer_id = payload.get(
            "customer_id"
        )

        if (
            customer_id
            and context.customer is None
        ):

            return DecisionResult(
                "wait",
                "Trigger requires customer context, but the customer context is unavailable."
            )

        # -----------------------------------------
        # 6. CUSTOMER CONSENT / REMINDER OPT-IN
        # -----------------------------------------

        if (
            customer_id
            and context.customer
        ):

            customer_payload = (
                context.customer.payload
            )

            preferences = customer_payload.get(
                "preferences",
                {}
            )

            consent = customer_payload.get(
                "consent",
                {}
            )

            reminder_opt_in = preferences.get(
                "reminder_opt_in",
                True
            )

            if reminder_opt_in is False:

                return DecisionResult(
                    "wait",
                    "Customer has not opted in to reminders."
                )

            if not consent:

                return DecisionResult(
                    "wait",
                    "Customer consent information is unavailable."
                )

        # -----------------------------------------
        # 7. EXPLICITLY EXPIRED FLAG
        # -----------------------------------------

        if payload.get("expired") is True:

            return DecisionResult(
                "wait",
                "Trigger is explicitly expired."
            )

        # -----------------------------------------
        # 8. EVERYTHING PASSED
        # -----------------------------------------

        return DecisionResult(
            "send",
            (
                "Trigger is active, not suppressed, "
                "not expired, customer context and consent "
                "requirements are satisfied."
            ),
            context
        )