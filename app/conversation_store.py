from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ConversationMessage:
    role: str
    content: str


@dataclass
class ConversationState:
    conversation_id: str
    merchant_id: Optional[str] = None
    customer_id: Optional[str] = None

    last_trigger_id: Optional[str] = None

    messages: list = field(default_factory=list)

    ended: bool = False
    turn_count: int = 0

    last_incoming_message: str = ""
    same_incoming_count: int = 0

    def add_message(self, role: str, content: str):
        """
        Add a message and maintain conversation-level state.
        """

        content = (content or "").strip()

        normalized = " ".join(content.lower().split())

        previous = (
            " ".join(self.last_incoming_message.lower().split())
            if self.last_incoming_message
            else ""
        )

        if role == "merchant":
            if normalized and normalized == previous:
                self.same_incoming_count += 1
            else:
                self.same_incoming_count = 1

            self.last_incoming_message = content

        self.messages.append(
            ConversationMessage(
                role=role,
                content=content
            )
        )

        self.turn_count += 1


class ConversationStore:

    def __init__(self):
        self._conversations = {}
        self._auto_reply_counts = {}

    def get(self, conversation_id: str):
        return self._conversations.get(conversation_id)

    def create(
        self,
        conversation_id: str,
        merchant_id: Optional[str] = None,
        customer_id: Optional[str] = None,
    ):
        conversation = ConversationState(
            conversation_id=conversation_id,
            merchant_id=merchant_id,
            customer_id=customer_id,
        )

        self._conversations[conversation_id] = conversation

        return conversation

    def get_or_create(
        self,
        conversation_id: str,
        merchant_id: Optional[str] = None,
        customer_id: Optional[str] = None,
    ):
        conversation = self.get(conversation_id)

        if conversation is None:
            conversation = self.create(
                conversation_id=conversation_id,
                merchant_id=merchant_id,
                customer_id=customer_id,
            )

        return conversation

    def save(self, conversation: ConversationState):
        self._conversations[conversation.conversation_id] = conversation

    def set_trigger(
            self,
            conversation_id: str,
            trigger_id: str
        ):
            conversation = self._conversations.get(conversation_id)
    
            if conversation is None:
                return
    
            conversation.last_trigger_id = trigger_id
            self._conversations[conversation_id] = conversation

    def delete(self, conversation_id: str):
        self._conversations.pop(conversation_id, None)

    def record_auto_reply(
        self,
        merchant_id: str | None,
        message: str
    ) -> int:

        normalized = " ".join(
            (message or "").strip().lower().split()
        )

        key = (
            merchant_id or "unknown_merchant",
            normalized,
        )

        count = self._auto_reply_counts.get(key, 0) + 1
        self._auto_reply_counts[key] = count

        return count

    def clear(self):
        self._conversations.clear()
        self._auto_reply_counts.clear()