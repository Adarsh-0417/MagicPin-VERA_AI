import os
import json
import re

from google import genai
from google.genai import types


class LLMReplyIntent:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("LLM_MODEL", "gemini-2.5-flash")
        self.client = genai.Client(api_key=api_key) if api_key else None

    @property
    def enabled(self):
        return self.client is not None

    def classify(self, message: str, history=None) -> dict:
        if not self.enabled:
            raise RuntimeError("GEMINI_API_KEY not configured")

        history = history or []

        prompt = f"""
You classify WhatsApp replies in a merchant AI assistant.

Classify the user's latest message into exactly ONE intent:

- opt_out
- positive_action
- question
- negative
- auto_reply
- ambiguous
- informational
- greeting

Definitions:

opt_out:
User explicitly wants no more messages.
Examples: stop, don't message me, not interested, unsubscribe.

positive_action:
User wants to proceed or take the offered action.
Examples:
"yes"
"do it"
"let's do it"
"go ahead"
"send it"
"I want to join"
"book Thursday"

question:
User asks for information before deciding.
Examples:
"how much?"
"what's next?"
"how does this work?"

negative:
User declines the current suggestion but has NOT explicitly asked to stop all communication.
Examples:
"not now"
"maybe later"
"don't need this"

auto_reply:
Clearly looks like a canned WhatsApp Business / automated response.
Examples:
"Thank you for contacting us. Our team will respond shortly."
"Thanks for reaching out. We are currently unavailable."

ambiguous:
Cannot confidently determine intent.

informational:
User provides useful information without clearly asking or accepting/rejecting.

greeting:
Hi, hello, good morning, etc.

IMPORTANT:
- Do not confuse a polite acknowledgement with positive_action.
- "Thanks" alone is ambiguous/informational.
- "Okay, let's do it" is positive_action.
- "Not interested, stop messaging me" is opt_out.
- "Not interested right now" is negative.
- Auto-reply detection should be conservative.

Conversation history:
{json.dumps(history[-6:], ensure_ascii=False)}

Latest message:
{message}

Return ONLY JSON:

{{
  "intent": "...",
  "confidence": 0.0,
  "language": "en|hi|hi-en|other",
  "reason": "short reason"
}}
"""

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json",
            ),
        )

        result = self._parse(response.text)

        allowed = {
            "opt_out",
            "positive_action",
            "question",
            "negative",
            "auto_reply",
            "ambiguous",
            "informational",
            "greeting",
        }

        if result.get("intent") not in allowed:
            raise ValueError("Invalid intent returned by LLM")

        confidence = float(result.get("confidence", 0))

        if confidence < 0.60:
            result["intent"] = "ambiguous"

        return result

    def _parse(self, text):
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{[\s\S]*\}", text)

            if not match:
                raise ValueError("Invalid LLM JSON")

            return json.loads(match.group())