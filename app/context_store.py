   from typing import Dict, Optional, Tuple

from app.models import ContextPayload, ContextRecord


class ContextStore:
    """
    Stateful store for Category, Merchant, Customer and Trigger contexts.

    Version semantics:
    - Same version  -> idempotent
    - Higher version -> replace
    - Lower version -> stale update
    """

    def __init__(self):
        self._contexts: Dict[Tuple[str, str], ContextRecord] = {}

    def upsert(self, context: ContextPayload) -> str:
        key = (context.scope, context.context_id)

        existing = self._contexts.get(key)

        if existing is None:
            self._contexts[key] = ContextRecord(**context.model_dump())
            return "created"

        if context.version < existing.version:
            raise ValueError(
                f"stale_version: received={context.version}, "
                f"current={existing.version}"
            )

        if context.version == existing.version:
            return "idempotent"

        self._contexts[key] = ContextRecord(**context.model_dump())
        return "updated"

    def get(
        self,
        scope: str,
        context_id: str
    ) -> Optional[ContextRecord]:

        return self._contexts.get((scope, context_id))

    def require(
        self,
        scope: str,
        context_id: str
    ) -> ContextRecord:

        context = self.get(scope, context_id)

        if context is None:
            raise KeyError(
                f"Context not found: {scope}/{context_id}"
            )

        return context

    def all(self, scope: Optional[str] = None):
        if scope is None:
            return list(self._contexts.values())

        return [
            context
            for context in self._contexts.values()
            if context.scope == scope
        ]

    def count(self) -> int:
        return len(self._contexts)