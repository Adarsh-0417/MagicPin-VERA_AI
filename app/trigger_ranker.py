from typing import List

from app.context_store import ContextStore


TRIGGER_WEIGHTS = {

    "regulation_change": 1.20,
    "renewal_due": 1.10,
    "perf_dip": 1.00,
    "perf_spike": 0.90,

    "milestone_reached": 0.85,
    "recall_due": 0.95,
    "appointment_tomorrow": 0.95,

    "customer_lapsed_soft": 0.80,
    "research_digest": 0.75,
    "review_theme_emerged": 0.75,

    "competitor_opened": 0.70,
    "festival_upcoming": 0.70,

    "trial_followup": 0.80,
    "chronic_refill_due": 0.90,

    "dormant_with_vera": 0.60,
    "curious_ask_due": 0.65,
}


class TriggerRanker:

    def __init__(
        self,
        store: ContextStore
    ):
        self.store = store

    def _score(self, trigger):

        payload = trigger.payload

        kind = payload.get(
            "kind",
            "unknown"
        )

        urgency = payload.get(
            "urgency",
            1
        )

        base_weight = TRIGGER_WEIGHTS.get(
            kind,
            0.50
        )

        try:
            urgency = float(
                urgency
            )
        except (
            ValueError,
            TypeError
        ):
            urgency = 1.0

        score = (
            base_weight
            * max(1.0, urgency)
        )

        # Customer-specific triggers get
        # a small relevance boost.
        if payload.get(
            "customer_id"
        ):
            score *= 1.10

        # Explicit priority can further refine
        # ranking when available.
        priority = payload.get(
            "priority"
        )

        if priority is not None:

            try:
                priority = float(
                    priority
                )

                score *= (
                    1.0
                    + min(priority, 5.0)
                    * 0.05
                )

            except (
                ValueError,
                TypeError
            ):
                pass

        return score

    def rank(
        self,
        trigger_ids: List[str]
    ):

        candidates = []

        for trigger_id in trigger_ids:

            trigger = self.store.get(
                "trigger",
                trigger_id
            )

            if trigger is None:
                continue

            score = self._score(
                trigger
            )

            candidates.append(
                (
                    trigger,
                    score
                )
            )

        candidates.sort(
            key=lambda item: item[1],
            reverse=True
        )

        return candidates