from typing import Optional

from app.context_resolver import CompositionContext, ContextResolver
from app.context_store import ContextStore
from app.suppression import SuppressionLedger


class DecisionResult:
    def __init__(
        self,
        action: str,
        rationale: str,
        context: Optional[CompositionContext] = None,
    ):
        self.action = action
        self.rationale = rationale
        self.context = context


class DecisionEngine:

    def __init__(
        self,
        store: ContextStore,
        resolver: ContextResolver,
        suppression: SuppressionLedger,
    ):
        self.store = store
        self.resolver = resolver
        self.suppression = suppression

    def evaluate(
        self,
        trigger_id: str,
    ) -> DecisionResult:

        # ----------------------------------------------------
        # 1. Trigger exists?
        # ----------------------------------------------------

        trigger = self.store.get(
            "trigger",
            trigger_id,
        )

        if trigger is None:
            return DecisionResult(
                action="wait",
                rationale="Trigger context is unavailable.",
            )

        payload = trigger.payload

        # ----------------------------------------------------
        # 2. Suppression
        # ----------------------------------------------------

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
                action="wait",
                rationale=(
                    "Trigger is suppressed because "
                    "the same suppression key was already used."
                ),
            )

        # ----------------------------------------------------
        # 3. Resolve four-context composition
        # ----------------------------------------------------

        try:
            context = self.resolver.resolve_trigger(
                trigger_id
            )

        except (KeyError, ValueError) as exc:

            return DecisionResult(
                action="wait",
                rationale=f"Required context unavailable: {exc}",
            )

        # ----------------------------------------------------
        # 4. Customer-specific trigger validation
        # ----------------------------------------------------

        customer_id = payload.get("customer_id")

        if customer_id and context.customer is None:
            return DecisionResult(
                action="wait",
                rationale=(
                    "Trigger requires customer context, "
                    "but the customer context is unavailable."
                ),
            )

        # ----------------------------------------------------
        # 5. Expiration
        # ----------------------------------------------------

        if payload.get("expired") is True:
            return DecisionResult(
                action="wait",
                rationale="Trigger is explicitly expired.",
            )

        # ----------------------------------------------------
        # 6. Basic eligibility
        # ----------------------------------------------------

        return DecisionResult(
            action="send",
            rationale=(
                "Trigger is active, not suppressed, and "
                "all required contexts are available."
            ),
            context=context,
        )