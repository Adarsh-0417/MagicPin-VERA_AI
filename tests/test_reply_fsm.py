from app.reply_fsm import ReplyFSM
from app.conversation_store import ConversationStore


AUTO_REPLY = (
    "Thank you for contacting Dr. Meera's Dental Clinic! "
    "Our team will respond shortly."
)


def test_first_auto_reply_sends():

    store = ConversationStore()
    fsm = ReplyFSM()

    conversation = store.get_or_create(
        "conv_test"
    )

    conversation = store.add_message(
        "conv_test",
        "merchant",
        AUTO_REPLY
    )

    decision = fsm.evaluate(
        AUTO_REPLY,
        conversation
    )

    assert decision.action == "send"


def test_second_auto_reply_waits_24_hours():

    store = ConversationStore()
    fsm = ReplyFSM()

    conversation = store.get_or_create(
        "conv_test"
    )

    store.add_message(
        "conv_test",
        "merchant",
        AUTO_REPLY
    )

    store.add_message(
        "conv_test",
        "merchant",
        AUTO_REPLY
    )

    decision = fsm.evaluate(
        AUTO_REPLY,
        conversation
    )

    assert decision.action == "wait"
    assert decision.wait_seconds == 86400


def test_third_auto_reply_ends():

    store = ConversationStore()
    fsm = ReplyFSM()

    conversation = store.get_or_create(
        "conv_test"
    )

    store.add_message(
        "conv_test",
        "merchant",
        AUTO_REPLY
    )

    store.add_message(
        "conv_test",
        "merchant",
        AUTO_REPLY
    )

    store.add_message(
        "conv_test",
        "merchant",
        AUTO_REPLY
    )

    decision = fsm.evaluate(
        AUTO_REPLY,
        conversation
    )

    assert decision.action == "end"


def test_positive_intent():

    store = ConversationStore()
    fsm = ReplyFSM()

    conversation = store.get_or_create(
        "conv_positive"
    )

    store.add_message(
        "conv_positive",
        "merchant",
        "Yes"
    )

    decision = fsm.evaluate(
        "Yes",
        conversation
    )

    assert decision.action == "send"


def test_opt_out_ends():

    store = ConversationStore()
    fsm = ReplyFSM()

    conversation = store.get_or_create(
        "conv_optout"
    )

    store.add_message(
        "conv_optout",
        "merchant",
        "Stop messaging me"
    )

    decision = fsm.evaluate(
        "Stop messaging me",
        conversation
    )

    assert decision.action == "end"


def test_question_gets_response():

    store = ConversationStore()
    fsm = ReplyFSM()

    conversation = store.get_or_create(
        "conv_question"
    )

    store.add_message(
        "conv_question",
        "merchant",
        "What is the price?"
    )

    decision = fsm.evaluate(
        "What is the price?",
        conversation
    )

    assert decision.action == "send"