from typing import Optional


class ReplyDecision:

    def __init__(
        self,
        action: str,
        body: Optional[str] = None,
        cta: Optional[str] = None,
        wait_seconds: Optional[int] = None,
        rationale: str = ""
    ):
        self.action = action
        self.body = body
        self.cta = cta
        self.wait_seconds = wait_seconds
        self.rationale = rationale


class ReplyFSM:

    OPT_OUT_WORDS = {
        "stop",
        "unsubscribe",
        "remove me",
        "don't message",
        "do not message",
        "no more",
    }

    POSITIVE_WORDS = {
        "yes",
        "haan",
        "sure",
        "okay",
        "ok",
        "interested",
        "tell me",
        "go ahead",
        "send",
        "sounds good",
    }

    QUESTION_WORDS = {
        "how",
        "what",
        "why",
        "when",
        "where",
        "can",
        "could",
        "price",
        "cost",
        "details",
    }

    def evaluate(
        self,
        message: str,
        turn_number: Optional[int] = None
    ) -> ReplyDecision:

        text = message.strip().lower()

        if not text:
            return ReplyDecision(
                action="wait",
                wait_seconds=1800,
                rationale="Empty message received."
            )

        # -----------------------------------------
        # Opt-out / stop
        # -----------------------------------------

        for phrase in self.OPT_OUT_WORDS:

            if phrase in text:

                return ReplyDecision(
                    action="end",
                    body="Understood. We won't send further messages in this conversation.",
                    rationale="Merchant/customer explicitly requested no further messages."
                )

        # -----------------------------------------
        # Positive intent
        # -----------------------------------------

        for phrase in self.POSITIVE_WORDS:

            if phrase in text:

                return ReplyDecision(
                    action="send",
                    body=(
                        "Absolutely. I can help with that. "
                        "Tell me what you'd like to explore and we'll take it from there."
                    ),
                    cta="Continue",
                    rationale="Positive intent detected from the incoming message."
                )

        # -----------------------------------------
        # Question / information request
        # -----------------------------------------

        words = set(text.replace("?", "").split())

        if "?" in text or words.intersection(
            self.QUESTION_WORDS
        ):

            return ReplyDecision(
                action="send",
                body=(
                    "Good question. I can help you work through the relevant "
                    "details for your business. What specific part would you "
                    "like to know more about?"
                ),
                cta="Continue",
                rationale="Information-seeking intent detected."
            )

        # -----------------------------------------
        # Hostile / negative response
        # -----------------------------------------

        negative_words = {
            "no",
            "not interested",
            "leave me alone",
            "annoying",
            "spam",
            "stop messaging",
        }

        for phrase in negative_words:

            if phrase in text:

                return ReplyDecision(
                    action="end",
                    body=(
                        "Understood. We won't continue this conversation."
                    ),
                    rationale="Negative or hostile intent detected."
                )

        # -----------------------------------------
        # Default
        # -----------------------------------------

        return ReplyDecision(
            action="wait",
            wait_seconds=1800,
            rationale=(
                "Intent was ambiguous, so the system waits "
                "rather than sending an unnecessary message."
            )
        )