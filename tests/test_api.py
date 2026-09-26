from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_healthz():

    response = client.get("/v1/healthz")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"


def test_metadata():

    response = client.get("/v1/metadata")

    assert response.status_code == 200

    data = response.json()

    assert "team_name" in data
    assert "model" in data
    assert "approach" in data


def test_context_versioning():

    context_id = "api_test_merchant"

    payload_v1 = {
        "scope": "merchant",
        "context_id": context_id,
        "version": 1,
        "payload": {
            "merchant_id": context_id,
            "category_slug": "dentists"
        }
    }

    response = client.post(
        "/v1/context",
        json=payload_v1
    )

    assert response.status_code == 200

    data = response.json()

    assert data["accepted"] is True
    assert data["current_version"] == 1


def test_context_same_version_is_idempotent():

    payload = {
        "scope": "merchant",
        "context_id": "api_idempotent_test",
        "version": 1,
        "payload": {
            "merchant_id": "api_idempotent_test"
        }
    }

    first = client.post(
        "/v1/context",
        json=payload
    )

    second = client.post(
        "/v1/context",
        json=payload
    )

    assert first.status_code == 200
    assert second.status_code == 200

    assert second.json()["reason"] == "idempotent"


def test_context_stale_version_returns_409():

    context_id = "api_stale_test"

    v2 = {
        "scope": "merchant",
        "context_id": context_id,
        "version": 2,
        "payload": {
            "merchant_id": context_id
        }
    }

    v1 = {
        "scope": "merchant",
        "context_id": context_id,
        "version": 1,
        "payload": {
            "merchant_id": context_id
        }
    }

    first = client.post(
        "/v1/context",
        json=v2
    )

    assert first.status_code == 200

    second = client.post(
        "/v1/context",
        json=v1
    )

    assert second.status_code == 409

    data = second.json()

    assert data["detail"]["reason"] == "stale_version"
    assert data["detail"]["current_version"] == 2


def test_tick_unknown_trigger_returns_no_action():

    response = client.post(
        "/v1/tick",
        json={
            "now": "2026-09-27T10:00:00Z",
            "available_triggers": [
                "does_not_exist"
            ]
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["actions"] == []


def test_reply_positive_intent():

    response = client.post(
        "/v1/reply",
        json={
            "conversation_id": "api_positive_test",
            "merchant_id": "m_test",
            "customer_id": None,
            "from_role": "merchant",
            "message": "Yes",
            "turn_number": 1
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["action"] == "send"


def test_reply_opt_out():

    response = client.post(
        "/v1/reply",
        json={
            "conversation_id": "api_optout_test",
            "merchant_id": "m_test",
            "customer_id": None,
            "from_role": "merchant",
            "message": "Stop messaging me",
            "turn_number": 1
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["action"] == "end"