class ActionValidator:

    MAX_BODY_LENGTH = 1000

    FORBIDDEN_PHRASES = [
        "guaranteed",
        "100% guaranteed",
        "password",
        "otp",
    ]

    def validate(
        self,
        result: dict
    ) -> tuple[bool, str]:

        body = (
            result.get("body", "")
            .strip()
        )

        # ---------------------------------------------------------
        # Empty message
        # ---------------------------------------------------------

        if not body:
            return False, "Message body is empty."

        # ---------------------------------------------------------
        # Length
        # ---------------------------------------------------------

        if len(body) > self.MAX_BODY_LENGTH:
            return (
                False,
                "Message body exceeds maximum length."
            )

        # ---------------------------------------------------------
        # Forbidden content
        # ---------------------------------------------------------

        body_lower = body.lower()

        for phrase in self.FORBIDDEN_PHRASES:

            if phrase in body_lower:

                return (
                    False,
                    f"Message contains forbidden phrase: {phrase}"
                )

        return True, "valid"