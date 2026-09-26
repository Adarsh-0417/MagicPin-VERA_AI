class ActionValidator:

    MAX_BODY_LENGTH = 1000

    def validate(self, result: dict) -> tuple[bool, str]:

        body = result.get("body", "").strip()

        if not body:
            return False, "Message body is empty."

        if len(body) > self.MAX_BODY_LENGTH:
            return False, "Message body exceeds maximum length."

        forbidden_phrases = [
            "guaranteed",
            "100% guaranteed",
            "fake",
            "password",
            "otp",
        ]

        body_lower = body.lower()

        for phrase in forbidden_phrases:
            if phrase in body_lower:
                return False, f"Message contains forbidden phrase: {phrase}"

        return True, "valid"