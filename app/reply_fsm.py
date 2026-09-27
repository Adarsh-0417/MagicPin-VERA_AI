import os
import json
import re

from app.llm_reply import LLMReplyIntent


# ============================================================
# LLM
# ============================================================

llm_reply = LLMReplyIntent()


# ============================================================
# DECISION OBJECT
# ============================================================

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


# ============================================================
# REPLY FSM
# ============================================================

class ReplyFSM:

    # --------------------------------------------------------
    # HARD SAFETY / DETERMINISTIC SIGNALS
    # --------------------------------------------------------

    OPT_OUT_PHRASES = [
        "stop",
        "unsubscribe",
        "remove me",
        "don't message",
        "do not message",
        "no more messages",
        "stop messaging",
        "do not contact",
        "don't contact",
        "never message me",
    ]

    NEGATIVE_PHRASES = [
        "not interested",
        "leave me alone",
        "spam",
        "annoying",
        "don't want this",
        "do not want this",
        "not now",
        "maybe later",
        "no thanks",
        "no thank you",
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
        "we are currently away",
        "thank you for reaching out",
        "thanks for reaching out",
        "our representative will",
        "our executive will",
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
        "whats next",
        "do it",
        "proceed",
        "continue",
        "i want to join",
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
        "which",
        "who",
        "how much",
    }

    # --------------------------------------------------------
    # AUTO REPLY
    # --------------------------------------------------------

    def _looks_like_auto_reply(self, text: str) -> bool:

        return any(
            marker in text
            for marker in self.AUTO_REPLY_MARKERS
        )

    # --------------------------------------------------------
    # CONVERSATION HISTORY
    # --------------------------------------------------------

    def _history(self, conversation):

        if not conversation:
            return []

        messages = getattr(
            conversation,
            "messages",
            []
        )

        history = []

        for message in messages[-8:]:

            role = getattr(
                message,
                "role",
                None
            )

            content = getattr(
                message,
                "content",
                None
            )

            # Support dictionary-style messages too
            if isinstance(message, dict):
                role = message.get("role")
                content = message.get(
                    "content",
                    message.get("message")
                )

            if content:
                history.append(
                    {
                        "role": role or "unknown",
                        "message": str(content),
                    }
                )

        return history

    # --------------------------------------------------------
    # PREVIOUS OUTBOUND MESSAGE
    # --------------------------------------------------------

    def _last_bot_message(self, conversation):

        history = self._history(conversation)

        for item in reversed(history):

            role = str(
                item.get("role", "")
            ).lower()

            if role in {
                "assistant",
                "bot",
                "vera",
                "system",
            }:
                return item.get(
                    "message",
                    ""
                )

        return ""

    # --------------------------------------------------------
    # LLM RESPONSE GENERATOR
    # --------------------------------------------------------

    def _generate_response(
        self,
        incoming_message,
        intent,
        conversation=None,
    ):

        if not llm_reply.enabled:
            return None

        history = self._history(
            conversation
        )

        last_bot_message = self._last_bot_message(
            conversation
        )

        trigger_id = (
            getattr(
                conversation,
                "last_trigger_id",
                None
            )
            if conversation
            else None
        )

        prompt = f"""
You are Vera, a merchant engagement AI operating on WhatsApp.

You are replying to a merchant's latest message.

Your job is to continue the EXISTING conversation.
Do not restart the conversation.
Do not repeat the original pitch.
Do not ask qualification questions if the merchant has already
clearly agreed to proceed.

LATEST USER INTENT:
{intent}

LATEST USER MESSAGE:
{incoming_message}

PREVIOUS OUTBOUND MESSAGE:
{last_bot_message or "No previous outbound message available."}

TRIGGER CONTEXT:
{trigger_id or "No trigger ID available."}

RECENT CONVERSATION:
{json.dumps(history, ensure_ascii=False, indent=2)}

RULES:

1. Respond directly to the latest message.
2. Preserve the context of the previous conversation.
3. If the user says yes / let's do it / go ahead:
   switch immediately into action mode.
4. If the user asks a question:
   answer the question if the available conversation context
   contains enough information.
5. Never invent prices, dates, links, statistics, offers,
   documents, or completed actions.
6. If required information is unavailable, say what is needed
   instead of hallucinating.
7. If the user has made multiple compatible requests,
   acknowledge and address them together.
8. Keep WhatsApp tone natural and concise.
9. One primary CTA maximum.
10. Do not reintroduce yourself.
11. Do not say "I hope you're doing well".
12. Do not mention internal trigger IDs or system logic.
13. Do not use "guaranteed" or "100%".
14. Match the user's language style.
15. Do not pretend an action has already happened unless the
    conversation proves it happened.
16. If the user only acknowledges something, do not manufacture
    a new sales pitch.

IMPORTANT INTENT RULES:

positive_action:
Move to the next concrete step immediately.

question:
Answer the actual question. If the information is unavailable,
ask for only the missing information.

informational:
Acknowledge the information and continue naturally.

greeting:
Respond briefly and connect back to the existing conversation
when useful.

ambiguous:
Give a short clarification prompt.

Return ONLY JSON:

{{
  "body": "response message",
  "cta": "short CTA identifier or none"
}}
"""

        try:

            response = llm_reply.client.models.generate_content(
                model=llm_reply.model,
                contents=prompt,
                config=__import__(
                    "google.genai",
                    fromlist=["types"]
                ).types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="application/json",
                ),
            )

            result = self._parse_json(
                response.text
            )

            body = str(
                result.get("body", "")
            ).strip()

            cta = str(
                result.get("cta", "none")
            ).strip()

            if not body:
                return None

            if len(body) > 1000:
                return None

            # Hard safety checks
            forbidden = [
                "guaranteed",
                "100% guaranteed",
                "trigger_id",
                "merchant_id",
                "customer_id",
                "suppression_key",
                "internal system",
            ]

            lower = body.lower()

            for phrase in forbidden:
                if phrase in lower:
                    return None

            return {
                "body": body,
                "cta": cta,
            }

        except Exception as e:

            print(
                f"[LLM RESPONSE FALLBACK] "
                f"{type(e).__name__}: {e}"
            )

            return None

    # --------------------------------------------------------
    # JSON PARSER
    # --------------------------------------------------------

    def _parse_json(self, text):

        text = text.strip()

        try:
            return json.loads(text)

        except json.JSONDecodeError:

            match = re.search(
                r"\{[\s\S]*\}",
                text
            )

            if not match:
                raise ValueError(
                    "LLM returned invalid JSON"
                )

            return json.loads(
                match.group()
            )

    # --------------------------------------------------------
    # RULE-BASED FALLBACK
    # --------------------------------------------------------

    def _fallback_positive(self, conversation=None):
        trigger_id = (
            getattr(conversation, "last_trigger_id", None)
            if conversation
            else None
        )

        if trigger_id:
            return ReplyDecision(
                "send",
                body=(
                    "Done. I'll take this forward and move to the "
                    "next step for this request."
                ),
                cta="next_step",
                rationale=(
                    "Merchant explicitly committed to proceed. "
                    "Moved directly to action mode."
                )
            )

        return ReplyDecision(
            "send",
            body=(
                "Done. I'll take this forward and move to the "
                "next concrete step."
            ),
            cta="next_step",
            rationale=(
                "Merchant explicitly committed to proceed. "
                "Skipped further qualification."
            )
        )

        # ====================================================
        # AUTO-REPLY
        #
        # Keep this deterministic.
        # We don't need an LLM deciding whether a message
        # containing "automated response" is automated.
        # Humans invented enough ambiguity already.
        # ====================================================

        if self._looks_like_auto_reply(text):

            repeat_count = (
                conversation.same_incoming_count
                if conversation
                else 1
            )

            # First auto reply
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
                        "Canned auto-reply detected for the "
                        "first time. One gentle follow-up."
                    )
                )

            # Second identical auto reply
            if repeat_count == 2:

                return ReplyDecision(
                    "wait",
                    wait_seconds=86400,
                    rationale=(
                        "Same auto-reply received twice. "
                        "Backing off for 24 hours."
                    )
                )

            # Third+
            return ReplyDecision(
                "end",
                rationale=(
                    "Repeated auto-reply detected three or "
                    "more times. Conversation closed to "
                    "avoid message spam."
                )
            )

        # ====================================================
        # EXPLICIT OPT OUT
        #
        # Deterministic safety always wins over LLM.
        # ====================================================

        for phrase in self.OPT_OUT_PHRASES:

            if phrase in text:

                return ReplyDecision(
                    "end",
                    body=(
                        "Understood. We won't send further "
                        "messages in this conversation."
                    ),
                    rationale=(
                        "Explicit opt-out detected."
                    )
                )

        # ====================================================
        # LLM INTENT CLASSIFICATION
        # ====================================================

        llm_intent = None

        if llm_reply.enabled:

            try:

                llm_intent = llm_reply.classify(
                    message=message,
                    history=self._history(
                        conversation
                    )
                )

                print(
                    "[LLM INTENT] "
                    f"{llm_intent.get('intent')} "
                    f"("
                    f"{llm_intent.get('confidence', 0):.2f}"
                    f")"
                )

            except Exception as e:

                print(
                    f"[LLM INTENT FALLBACK] "
                    f"{type(e).__name__}: {e}"
                )

        # ====================================================
        # HIGH-CONFIDENCE LLM ROUTING
        # ====================================================

        if llm_intent:

            intent = llm_intent.get(
                "intent",
                "ambiguous"
            )

            try:
                confidence = float(
                    llm_intent.get(
                        "confidence",
                        0
                    )
                )
            except Exception:
                confidence = 0

            # -----------------------------------------------
            # OPT OUT
            # -----------------------------------------------

            if (
                intent == "opt_out"
                and confidence >= 0.70
            ):

                return ReplyDecision(
                    "end",
                    body=(
                        "Understood. We won't send further "
                        "messages in this conversation."
                    ),
                    rationale=(
                        "LLM detected explicit opt-out intent."
                    )
                )

            # -----------------------------------------------
            # AUTO REPLY
            # -----------------------------------------------

            if (
                intent == "auto_reply"
                and confidence >= 0.75
            ):

                repeat_count = (
                    conversation.same_incoming_count
                    if conversation
                    else 1
                )

                if repeat_count == 1:

                    return ReplyDecision(
                        "send",
                        body=(
                            "Looks like an auto-reply 😊 "
                            "When the owner sees this, just "
                            "reply 'Yes' for the update."
                        ),
                        cta="yes_no",
                        rationale=(
                            "LLM detected a likely canned "
                            "auto-reply."
                        )
                    )

                if repeat_count == 2:

                    return ReplyDecision(
                        "wait",
                        wait_seconds=86400,
                        rationale=(
                            "Repeated auto-reply detected. "
                            "Backing off for 24 hours."
                        )
                    )

                return ReplyDecision(
                    "end",
                    rationale=(
                        "Repeated auto-reply detected three "
                        "or more times."
                    )
                )

            # -----------------------------------------------
            # POSITIVE ACTION
            # -----------------------------------------------

            if (
                intent == "positive_action"
                and confidence >= 0.70
            ):

                generated = self._generate_response(
                    incoming_message=message,
                    intent=intent,
                    conversation=conversation,
                )

                if generated:

                    return ReplyDecision(
                        "send",
                        body=generated["body"],
                        cta=generated["cta"],
                        rationale=(
                            "Positive intent detected by LLM. "
                            "Switched directly to action mode "
                            "and generated a context-aware "
                            "next-step response."
                        )
                    )

                return self._fallback_positive(
                    conversation
                )

            # -----------------------------------------------
            # QUESTION
            # -----------------------------------------------

            if (
                intent == "question"
                and confidence >= 0.70
            ):

                generated = self._generate_response(
                    incoming_message=message,
                    intent=intent,
                    conversation=conversation,
                )

                if generated:

                    return ReplyDecision(
                        "send",
                        body=generated["body"],
                        cta=generated["cta"],
                        rationale=(
                            "Question intent detected by LLM. "
                            "Generated a response using the "
                            "existing conversation context."
                        )
                    )

                return ReplyDecision(
                    "send",
                    body=(
                        "Happy to explain. Tell me which "
                        "part you'd like more details on."
                    ),
                    cta="continue",
                    rationale=(
                        "Question detected; LLM response "
                        "generation unavailable."
                    )
                )

            # -----------------------------------------------
            # NEGATIVE
            # -----------------------------------------------

            if (
                intent == "negative"
                and confidence >= 0.75
            ):

                return ReplyDecision(
                    "wait",
                    wait_seconds=86400,
                    rationale=(
                        "User declined the current suggestion "
                        "without explicitly opting out."
                    )
                )

            # -----------------------------------------------
            # INFORMATIONAL
            # -----------------------------------------------

            if (
                intent == "informational"
                and confidence >= 0.70
            ):

                generated = self._generate_response(
                    incoming_message=message,
                    intent=intent,
                    conversation=conversation,
                )

                if generated:

                    return ReplyDecision(
                        "send",
                        body=generated["body"],
                        cta=generated["cta"],
                        rationale=(
                            "Informational response detected. "
                            "Generated a context-aware continuation."
                        )
                    )

            # -----------------------------------------------
            # GREETING
            # -----------------------------------------------

            if (
                intent == "greeting"
                and confidence >= 0.80
            ):

                generated = self._generate_response(
                    incoming_message=message,
                    intent=intent,
                    conversation=conversation,
                )

                if generated:

                    return ReplyDecision(
                        "send",
                        body=generated["body"],
                        cta=generated["cta"],
                        rationale=(
                            "Greeting detected. Continued the "
                            "existing conversation naturally."
                        )
                    )

        # ====================================================
        # DETERMINISTIC FALLBACK
        # ====================================================
        #
        # If Gemini isn't available or confidence is low,
        # old FSM logic still works.
        # ====================================================

        # ----------------------------------------------------
        # NEGATIVE FALLBACK
        # ----------------------------------------------------

        for phrase in self.NEGATIVE_PHRASES:

            if phrase in text:

                return ReplyDecision(
                    "wait",
                    wait_seconds=86400,
                    rationale=(
                        "Negative intent detected without "
                        "explicit opt-out. Conversation paused."
                    )
                )

        # ----------------------------------------------------
        # POSITIVE FALLBACK
        # ----------------------------------------------------

        for phrase in self.POSITIVE_PHRASES:

            if phrase in text:

                return self._fallback_positive(
                    conversation
                )

        # ----------------------------------------------------
        # QUESTION FALLBACK
        # ----------------------------------------------------

        words = set(
            text.replace(
                "?",
                ""
            ).split()
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
                cta="continue",
                rationale=(
                    "Information-seeking intent detected "
                    "by deterministic fallback."
                )
            )

        # ----------------------------------------------------
        # AMBIGUOUS
        # ----------------------------------------------------

        return ReplyDecision(
            "wait",
            wait_seconds=1800,
            rationale=(
                "Intent was ambiguous. Waiting instead of "
                "sending an unnecessary message."
            )
        )