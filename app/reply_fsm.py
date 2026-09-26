class ReplyDecision:

    def __init__(
        self,
        action,
        body=None,
        cta=None,
        wait_seconds=None,
        rationale=""
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
        "stop messaging"
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
        "let's do it",
        "lets do it",
        "what's next",
        "whats next"
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
        "explain"
    }

    NEGATIVE_PHRASES = [
        "not interested",
        "leave me alone",
        "spam",
        "annoying",
        "don't want this"
    ]

    AUTO_REPLY_MARKERS = [
        "thank you for contacting",
        "thanks for contacting",
        "our team will respond",
        "our team will get back",
        "we will respond shortly",
        "we'll respond shortly",
        "will respond shortly",
        "will get back to you",
        "we'll get back to you",
        "automated response",
        "automatic response",
        "currently unavailable",
        "office hours",
        "we are currently away"
    ]

    def _looks_like_auto_reply(
        self,
        text: str
    ) -> bool:

        return any(
            marker in text
            for marker in self.AUTO_REPLY_MARKERS
        )

    def evaluate(
        self,
        message,
        conversation=None
    ):

        text = message.strip().lower()

        if not text:

            return ReplyDecision(
                "wait",
                wait_seconds=1800,
                rationale="Empty message received."
            )

        if conversation and conversation.ended:

            return ReplyDecision(
                "end",
                rationale="Conversation has already been ended."
            )

        # -----------------------------------------
        # AUTO-REPLY HANDLING
        # -----------------------------------------

        if self._looks_like_auto_reply(text):

            repeat_count = (
                conversation.same_incoming_count
                if conversation
                else 1
            )

            # First identical auto-reply
            if repeat_count == 1:

                return ReplyDecision(
                    "send",
                    body=(
                        "Looks like an auto-reply 😊 "
                        "When the owner sees this, just reply "
                        "'Yes' for the update."
                    ),
                    cta="yes_no",
                    rationale=(
                        "Canned auto-reply detected for the first time. "
                        "The system sends one gentle follow-up."
                    )
                )

            # Second identical auto-reply
            if repeat_count == 2:

                return ReplyDecision(
                    "wait",
                    wait_seconds=86400,
                    rationale=(
                        "The same auto-reply was received twice. "
                        "The system waits 24 hours instead of sending again."
                    )
                )

            # Third identical auto-reply
            return ReplyDecision(
                "end",
                rationale=(
                    "The same auto-reply was received repeatedly. "
                    "The system ends the conversation to avoid message spam."
                )
            )

        # -----------------------------------------
        # OPT OUT
        # -----------------------------------------

        for phrase in self.OPT_OUT_PHRASES:

            if phrase in text:

                return ReplyDecision(
                    "end",
                    body=(
                        "Understood. We won't send further "
                        "messages in this conversation."
                    ),
                    rationale="Explicit opt-out detected."
                )

        # -----------------------------------------
        # NEGATIVE INTENT
        # -----------------------------------------

        for phrase in self.NEGATIVE_PHRASES:

            if phrase in text:

                return ReplyDecision(
                    "end",
                    body=(
                        "Understood. We won't continue "
                        "this conversation."
                    ),
                    rationale="Negative intent detected."
                )

        # -----------------------------------------
        # POSITIVE INTENT
        # -----------------------------------------

        for phrase in self.POSITIVE_PHRASES:

            if phrase in text:

                if (
                    conversation
                    and conversation.last_trigger_id
                ):

                    return ReplyDecision(
                        "send",
                        body=(
                            "Absolutely. Let's take this forward. "
                            "I can help you with the next steps "
                            "related to this update."
                        ),
                        cta="Continue",
                        rationale=(
                            "Positive intent detected with "
                            "an active trigger context."
                        )
                    )

                return ReplyDecision(
                    "send",
                    body=(
                        "Absolutely. I can help with that. "
                        "What would you like to explore?"
                    ),
                    cta="Continue",
                    rationale="Positive intent detected."
                )

        # -----------------------------------------
        # QUESTION / INFORMATION SEEKING
        # -----------------------------------------

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
                "send",
                body=(
                    "Happy to explain. Tell me which part "
                    "you'd like more details on, and I'll "
                    "keep it specific to your business."
                ),
                cta="Continue",
                rationale=(
                    "Information-seeking intent detected."
                )
            )

        # -----------------------------------------
        # AMBIGUOUS
        # -----------------------------------------

        return ReplyDecision(
            "wait",
            wait_seconds=1800,
            rationale=(
                "Intent was ambiguous, so the system waits "
                "instead of sending unnecessary messages."
            )
        )