from typing import Optional

from app.conversation_store import ConversationState


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

    OPT_OUT_PHRASES = [
        "stop",
        "unsubscribe",
        "remove me",
        "don't message",
        "do not message",
        "no more messages",
        "stop messaging",
    ]

    POSITIVE_PHRASES = [
        "yes",
        "haan",
        "sure",
        "okay",
        "ok",
        "interested",
        "tell me more",
        "go ahead",
        "sounds good",
        "send it",
    ]

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
        "explain",
    }

    NEGATIVE_PHRASES = [
        "not interested",
        "leave me alone",
        "spam",
        "annoying",
        "don't want this",
    ]

    def evaluate(
        self,
        message: str,
        conversation: Optional[ConversationState] = None
    ) -> ReplyDecision:

        text = message.strip().lower()

        if not text:

            return ReplyDecision(
                action="wait",
                wait_seconds=1800,
                rationale="Empty message received."
            )

        # --------------------------------------------------
        # Already ended
        # --------------------------------------------------

        if conversation and conversation.ended:

            return ReplyDecision(
                action="end",
                rationale="Conversation has already been ended."
            )

        # --------------------------------------------------
        # Explicit opt-out
        # --------------------------------------------------

        for phrase in self.OPT_OUT_PHRASES:

            if phrase in text:

                return ReplyDecision(
                    action="end",
                    body=(
                        "Understood. We won't send "
                        "further messages in this conversation."
                    ),
                    rationale=(
                        "Explicit opt-out detected."
                    )
                )

        # --------------------------------------------------
        # Negative / hostile
        # --------------------------------------------------

        for phrase in self.NEGATIVE_PHRASES:

            if phrase in text:

                return ReplyDecision(
                    action="end",
                    body=(
                        "Understood. We won't continue "
                        "this conversation."
                    ),
                    rationale=(
                        "Negative intent detected."
                    )
                )

        # --------------------------------------------------
        # Positive intent
        # --------------------------------------------------

        for phrase in self.POSITIVE_PHRASES:

            if phrase in text:

                if conversation and conversation.last_trigger_id:

                    return ReplyDecision(
                        action="send",
                        body=(
                            "Absolutely. Let's take this "
                            "forward. I can help you with the "
                            "next steps related to this update."
                        ),
                        cta="Continue",
                        rationale=(
                            "Positive intent detected with "
                            "an active trigger context."
                        )
                    )

                return ReplyDecision(
                    action="send",
                    body=(
                        "Absolutely. I can help with that. "
                        "What would you like to explore?"
                    ),
                    cta="Continue",
                    rationale=(
                        "Positive intent detected."
                    )
                )

        # --------------------------------------------------
        # Questions
        # --------------------------------------------------

        words = set(
            text.replace("?", "").split()
        )

        if (
            "?" in text
            or words.intersection(
                self.QUESTION_WORDS
            )
        ):

            return ReplyDecision(
                action="send",
                body=(
                    "Happy to explain. Tell me which "
                    "part you'd like more details on, "
                    "and I'll keep it specific to "
                    "your business."
                ),
                cta="Continue",
                rationale=(
                    "Information-seeking intent detected."
                )
            )

        # --------------------------------------------------
        # Ambiguous
        # --------------------------------------------------

        return ReplyDecision(
            action="wait",
            wait_seconds=1800,
            rationale=(
                "Intent was ambiguous, so the system "
                "waits instead of sending unnecessary "
                "messages."
            )
        )