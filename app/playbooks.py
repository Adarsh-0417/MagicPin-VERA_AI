CATEGORY_PLAYBOOKS = {

    "dentists": {
        "tone": "professional, warm and patient-focused",
        "cta": "Reply to discuss",
        "focus": "appointments, recalls, patient engagement and clinic growth"
    },

    "salons": {
        "tone": "friendly, practical and appointment-focused",
        "cta": "Reply to discuss",
        "focus": "appointments, repeat visits, offers and customer retention"
    },

    "restaurants": {
        "tone": "concise, practical and commercially focused",
        "cta": "Reply to discuss",
        "focus": "orders, customers, offers and restaurant performance"
    },

    "gyms": {
        "tone": "energetic, friendly and retention-focused",
        "cta": "Reply to discuss",
        "focus": "memberships, retention, engagement and promotions"
    },

    "pharmacies": {
        "tone": "professional, concise and service-focused",
        "cta": "Reply to discuss",
        "focus": "customer service, refills, reminders and pharmacy operations"
    },

    # Backward-compatible aliases
    "clinic": {
        "tone": "professional, concise and patient-focused",
        "cta": "Reply to discuss",
        "focus": "appointments, recalls and patient engagement"
    },

    "salon": {
        "tone": "friendly, practical and appointment-focused",
        "cta": "Reply to discuss",
        "focus": "appointments, repeat customers and promotions"
    },

    "spa": {
        "tone": "friendly, concise and customer-retention focused",
        "cta": "Reply to discuss",
        "focus": "appointments, repeat visits and customer engagement"
    },

    "retail": {
        "tone": "commercial, concise and action-oriented",
        "cta": "Reply to discuss",
        "focus": "customers, promotions and store performance"
    }
}


TRIGGER_PLAYBOOKS = {

    "perf_dip": {
        "goal": "highlight the performance change and suggest a useful next step"
    },

    "perf_spike": {
        "goal": "highlight positive performance and suggest how to sustain it"
    },

    "renewal_due": {
        "goal": "remind the merchant about an upcoming renewal"
    },

    "regulation_change": {
        "goal": "surface an important regulation update"
    },

    "recall_due": {
        "goal": "help the merchant reconnect with a customer"
    },

    "appointment_tomorrow": {
        "goal": "help the merchant prepare for an upcoming appointment"
    },

    "customer_lapsed_soft": {
        "goal": "encourage a relevant customer re-engagement"
    },

    "research_digest": {
        "goal": "share a useful research or market insight"
    },

    "festival_upcoming": {
        "goal": "suggest a timely festival-related opportunity"
    },

    "milestone_reached": {
        "goal": "celebrate the milestone and suggest a next action"
    },

    "review_theme_emerged": {
        "goal": "surface a useful customer-review theme"
    },

    "competitor_opened": {
        "goal": "surface a relevant local competitive development"
    },

    "trial_followup": {
        "goal": "follow up on merchant trial engagement"
    },

    "chronic_refill_due": {
        "goal": "surface a timely refill reminder"
    },

    "dormant_with_vera": {
        "goal": "re-engage the merchant with a useful business action"
    },

    "curious_ask_due": {
        "goal": "respond to a merchant interest signal with useful information"
    }
}


def get_category_playbook(
    category_slug: str
) -> dict:

    return CATEGORY_PLAYBOOKS.get(
        category_slug,
        {
            "tone": "concise, practical and merchant-friendly",
            "cta": "Reply to discuss",
            "focus": "merchant growth and customer engagement"
        }
    )


def get_trigger_playbook(
    trigger_kind: str
) -> dict:

    return TRIGGER_PLAYBOOKS.get(
        trigger_kind,
        {
            "goal": "provide a useful and relevant merchant action"
        }
    )