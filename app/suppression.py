from typing import Set


class SuppressionLedger:

    def __init__(self):
        self._sent_keys: Set[str] = set()

    def is_suppressed(self, suppression_key: str) -> bool:
        if not suppression_key:
            return False

        return suppression_key in self._sent_keys

    def mark_sent(self, suppression_key: str) -> None:
        if suppression_key:
            self._sent_keys.add(suppression_key)

    def clear(self) -> None:
        self._sent_keys.clear()

    def size(self) -> int:
        return len(self._sent_keys)