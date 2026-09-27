import os
import json
import re
from typing import Optional

from google import genai
from google.genai import types


class LLMComposer:
    """
    Gemini-powered composer.
    Deterministic rule-based composer remains the fallback.
    """

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("LLM_MODEL", "gemini-2.5-flash")

        self.client = None

        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)

    @property
    def enabled(self) -> bool:
        return self.client is not None

    def compose(
        self,
        category: dict,
        merchant: dict,
        trigger: dict,
        customer: Optional[dict] = None,
    ) -> dict:

        if not self.enabled:
            raise RuntimeError("GEMINI_API_KEY not configured")

        strategy = self._strategy(trigger, customer)

        prompt = self._build_prompt(
            category,
            merchant,
            trigger,
            customer,
            strategy,
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json",
            ),
        )

        raw = response.text.strip()

        result = self._parse_json(raw)

        self._validate(
            result,
            category,
            merchant,
            trigger,
            customer,
        )

        return result

    # ---------------------------------------------------------
    # ROUTING
    # ---------------------------------------------------------

    def _strategy(self, trigger: dict, customer: Optional[dict]) -> str:

        kind = trigger.get("kind", "")

        if kind == "recall_due":
            return """
CUSTOMER RECALL MODE:
- This is a customer-facing reminder.
- Be warm and clinically appropriate.
- Use the customer's name.
- Mention the actual service due.
- Mention actual available slots if provided.
- Mention actual offer/price only if present in merchant context.
- Give exactly one clear booking CTA.
"""

        if kind in {"perf_dip", "performance_dip"}:
            return """
PERFORMANCE RECOVERY MODE:
- Merchant-facing.
- Clearly explain what changed.
- Use actual merchant performance numbers.
- Compare with peer/category numbers only if explicitly provided.
- Avoid generic marketing advice.
- Give one practical next step.
"""

        if kind in {"perf_spike", "performance_spike"}:
            return """
PERFORMANCE SPIKE MODE:
- Merchant-facing.
- Highlight the positive signal.
- Explain why it matters.
- Suggest one concrete action to capitalize on it.
- Do not exaggerate or invent causality.
"""

        if kind in {"research_digest_release", "research_digest"}:
            return """
RESEARCH DIGEST MODE:
- Merchant-facing.
- Lead with the most relevant research insight.
- Use source information only when actually present.
- Explain why it matters to this merchant.
- CTA should be low-friction and specific.
"""

        if kind in {"renewal_due", "chronic_refill_due", "trial_followup"}:
            return """
FOLLOW-UP / RENEWAL MODE:
- Make the reason for contacting the merchant obvious immediately.
- Use exact dates, products, services or values only when supplied.
- One action-oriented CTA.
"""

        if kind in {
            "festival_upcoming",
            "competitor_opened",
            "regulation_change",
            "milestone_reached",
            "review_theme_emerged",
        }:
            return """
EVENT / SIGNAL MODE:
- Merchant-facing.
- Start from the concrete signal.
- Explain the business implication briefly.
- Avoid generic promotional copy.
- Suggest one specific next action.
"""

        return """
GENERAL MERCHANT ENGAGEMENT MODE:
- Merchant-facing.
- Personalize from actual merchant data.
- Make the trigger/reason explicit.
- Provide one useful insight.
- End with one low-friction CTA.
"""

    # ---------------------------------------------------------
    # PROMPT
    # ---------------------------------------------------------

    def _build_prompt(
        self,
        category,
        merchant,
        trigger,
        customer,
        strategy,
    ):

        return f"""
You are Vera, an AI engagement assistant for magicpin merchants.

Your job is NOT to write generic marketing copy.

You receive four structured contexts:

1. CATEGORY
2. MERCHANT
3. TRIGGER
4. CUSTOMER (optional)

Your output must be a concise WhatsApp message that feels specifically written
for this exact situation.

==============================
CORE RULES
==============================

1. NEVER invent facts.
2. NEVER invent prices, offers, dates, statistics, competitors, research,
   customer history, slots, or performance numbers.
3. Use ONLY information contained in the supplied contexts.
4. Match the category voice.
5. Match the merchant's language preference.
6. If customer context exists, personalize using it.
7. Make the reason for contacting them obvious.
8. Keep the message concise.
9. Use ONE primary CTA only.
10. CTA should be in the final sentence.
11. Do not expose internal system terminology.
12. Do not mention context, payload, trigger IDs, suppression keys,
    merchant IDs, customer IDs, or internal routing.
13. Do not introduce yourself repeatedly.
14. Do not use fake urgency.
15. Do not use phrases like "guaranteed", "100% guaranteed".
16. Avoid excessive emojis.
17. WhatsApp tone, natural and human.
18. Hindi-English mixing is allowed when the context indicates it.
19. If the trigger does not justify a message, produce a useful,
    low-pressure message rather than inventing a reason.
20. Never use multiple competing questions or CTAs.

==============================
TRIGGER STRATEGY
==============================

{strategy}

==============================
CATEGORY CONTEXT
==============================

{json.dumps(category, ensure_ascii=False, indent=2)}

==============================
MERCHANT CONTEXT
==============================

{json.dumps(merchant, ensure_ascii=False, indent=2)}

==============================
TRIGGER CONTEXT
==============================

{json.dumps(trigger, ensure_ascii=False, indent=2)}

==============================
CUSTOMER CONTEXT
==============================

{json.dumps(customer, ensure_ascii=False, indent=2)
if customer else "NO CUSTOMER CONTEXT"}

==============================
OUTPUT FORMAT
==============================

Return ONLY valid JSON.

{{
  "body": "WhatsApp message",
  "cta": "short CTA identifier",
  "rationale": "one short internal rationale"
}}

Do NOT wrap JSON in markdown.

Now compose the message.
"""

    # ---------------------------------------------------------
    # JSON
    # ---------------------------------------------------------

    def _parse_json(self, raw: str) -> dict:

        raw = raw.strip()

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{[\s\S]*\}", raw)

            if not match:
                raise ValueError("Gemini did not return valid JSON")

            return json.loads(match.group())

    # ---------------------------------------------------------
    # HARD VALIDATION
    # ---------------------------------------------------------

    def _validate(
        self,
        result: dict,
        category: dict,
        merchant: dict,
        trigger: dict,
        customer: Optional[dict],
    ):

        body = str(result.get("body", "")).strip()
        cta = str(result.get("cta", "")).strip()

        if not body:
            raise ValueError("LLM returned empty body")

        if len(body) > 1000:
            raise ValueError("LLM message too long")

        forbidden = [
            "guaranteed",
            "100% guaranteed",
            "suppression_key",
            "trigger_id",
            "merchant_id",
            "customer_id",
            "context payload",
            "internal system",
        ]

        lower = body.lower()

        for phrase in forbidden:
            if phrase.lower() in lower:
                raise ValueError(
                    f"LLM exposed forbidden/internal phrase: {phrase}"
                )

        # Prevent obvious multiple-CTA spam
        cta_markers = [
            "reply yes",
            "reply no",
            "reply 1",
            "reply 2",
            "click here",
            "book now",
            "let me know",
            "want me to",
        ]

        marker_count = sum(
            1 for marker in cta_markers
            if marker in lower
        )

        if marker_count > 2:
            raise ValueError("Potentially multiple CTAs")

        # Customer messages should normally contain customer name
        if customer:
            customer_name = (
                customer.get("identity", {})
                .get("name")
            )

            if customer_name and len(customer_name) > 2:
                # Don't hard fail because some customer journeys
                # intentionally avoid repeating names.
                pass

        result["body"] = body
        result["cta"] = cta or "open_ended"
        result["rationale"] = str(
            result.get("rationale", "")
        )[:500]