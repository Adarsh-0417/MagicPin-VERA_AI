import os
import json

from google import genai
from google.genai import types


class LLMReplyIntent:

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = os.getenv(
            "LLM_MODEL",
            "gemini-2.5-flash"
        )

        print(
            "[LLM INIT] GEMINI_API_KEY:",
            "FOUND" if self.api_key else "MISSING"
        )

        if self.api_key:
            self.client = genai.Client(
                api_key=self.api_key
            )
        else:
            self.client = None

    @property
    def enabled(self):
        return self.client is not None

    def classify(self, message, history=None):

        if not self.enabled:
            raise RuntimeError(
                "GEMINI_API_KEY is missing"
            )

        prompt = f"""
You are an intent classifier for a WhatsApp merchant engagement chatbot.

Classify the latest merchant message into EXACTLY ONE intent.

Allowed intents:

- opt_out
- positive_action
- question
- negative
- auto_reply
- informational
- greeting
- ambiguous

LATEST MESSAGE:
{message}

RECENT CONVERSATION:
{json.dumps(history or [], ensure_ascii=False)}

Rules:

1. opt_out:
   The merchant explicitly wants messages to stop.

2. positive_action:
   The merchant clearly wants to proceed.
   Examples:
   yes, okay, sure, go ahead, let's do it, proceed.

3. question:
   The merchant asks for information.

4. negative:
   The merchant declines but does not explicitly ask to stop all messages.

5. auto_reply:
   The message looks like a canned/automated business response.

6. informational:
   The merchant provides information or an update.

7. greeting:
   Simple greetings such as hi, hello, hey.

8. ambiguous:
   The intent cannot be determined confidently.

Return ONLY valid JSON:

{{
  "intent": "one_allowed_intent",
  "confidence": 0.0
}}

Confidence must be between 0 and 1.
"""

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0,
                response_mime_type="application/json"
            )
        )

        raw = response.text.strip()

        print("[LLM RAW]", raw)

        result = json.loads(raw)

        allowed = {
            "opt_out",
            "positive_action",
            "question",
            "negative",
            "auto_reply",
            "informational",
            "greeting",
            "ambiguous"
        }

        intent = result.get("intent")
        confidence = float(
            result.get("confidence", 0)
        )

        if intent not in allowed:
            raise ValueError(
                f"Invalid intent returned: {intent}"
            )

        if confidence < 0.60:
            intent = "ambiguous"

        return {
            "intent": intent,
            "confidence": confidence
        }