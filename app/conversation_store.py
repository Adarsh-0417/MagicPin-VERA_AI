from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ConversationState:
    conversation_id: str
    merchant_id: Optional[str] = None
    customer_id: Optional[str] = None

    last_trigger_id: Optional[str] = None

    messages: List[dict] = field(default_factory=list)

    ended: bool = False
    turn_count: int = 0

    # Repeated incoming-message tracking
    last_incoming_message: Optional[str] = None
    same_incoming_count: int = 0


class ConversationStore:

    def __init__(self):
        self._conversations: Dict[str, ConversationState] = {}

    def get(
        self,
        conversation_id: str
    ) -> Optional[ConversationState]:

        return self._conversations.get(
            conversation_id
        )

    def get_or_create(
        self,
        conversation_id: str,
        merchant_id: Optional[str] = None,
        customer_id: Optional[str] = None
    ) -> ConversationState:

        conversation = self.get(
            conversation_id
        )

        if conversation is None:

            conversation = ConversationState(
                conversation_id=conversation_id,
                merchant_id=merchant_id,
                customer_id=customer_id
            )

            self._conversations[
                conversation_id
            ] = conversation

        else:

            if merchant_id:
                conversation.merchant_id = merchant_id

            if customer_id:
                conversation.customer_id = customer_id

        return conversation

    def add_message(
        self,
        conversation_id: str,
        role: str,
        message: str
    ):

        conversation = self.get_or_create(
            conversation_id
        )

        normalized = " ".join(
            message.strip().lower().split()
        )

        # Track consecutive identical incoming messages
        if role in {"merchant", "customer", "user"}:

            if (
                conversation.last_incoming_message
                == normalized
            ):
                conversation.same_incoming_count += 1

            else:

                conversation.last_incoming_message = normalized
                conversation.same_incoming_count = 1

        conversation.messages.append(
            {
                "role": role,
                "message": message
            }
        )

        conversation.turn_count += 1

        return conversation

    def set_trigger(
        self,
        conversation_id: str,
        trigger_id: str
    ):

        conversation = self.get_or_create(
            conversation_id
        )

        conversation.last_trigger_id = trigger_id

    def end(
        self,
        conversation_id: str
    ):

        conversation = self.get_or_create(
            conversation_id
        )

        conversation.ended = True