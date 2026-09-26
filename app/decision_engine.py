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

            if now:
                current_time = datetime.fromisoformat(
                    now.replace("Z", "+00:00")
                )
            else:
                current_time = datetime.now(timezone.utc)

            return current_time >= expiry

        except (ValueError, TypeError):
            return False

    def evaluate(
        self,
        trigger_id: str,
        now: Optional[str] = None
    ) -> DecisionResult:

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

        # ---------------------------------------------------------
        # 1. Suppression check
        # ---------------------------------------------------------

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

        # ---------------------------------------------------------
        # 2. Expiry check
        # ---------------------------------------------------------

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

        # ---------------------------------------------------------
        # 3. Resolve all required contexts
        # ---------------------------------------------------------

        try:

            context = self.resolver.resolve_trigger(
                trigger_id
            )

        except (KeyError, ValueError) as exc:

            return DecisionResult(
                "wait",
                f"Required context unavailable: {exc}"
            )

        # ---------------------------------------------------------
        # 4. Customer validation
        # ---------------------------------------------------------

        customer_id = payload.get(
            "customer_id"
        )

        if customer_id and context.customer is None:

            return DecisionResult(
                "wait",
                "Trigger requires customer context, but the customer context is unavailable."
            )

        # ---------------------------------------------------------
        # 5. Explicit expiry flag
        # ---------------------------------------------------------

        if payload.get("expired") is True:

            return DecisionResult(
                "wait",
                "Trigger is explicitly expired."
            )

        # ---------------------------------------------------------
        # 6. Everything is valid
        # ---------------------------------------------------------

        return DecisionResult(
            "send",
            "Trigger is active, not suppressed, not expired, and all required contexts are available.",
            context
        )