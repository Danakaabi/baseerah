from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_verify_text_returns_evidence() -> None:
    response = client.post(
        "/verify/text",
        json={
            "text": (
                "هل ينظر الله إلى صور الناس وأجسامهم "
                "أم إلى قلوبهم وأعمالهم؟"
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "evidence_found"
    assert data["source"] is not None
    assert (
        data["source"]["source_id"]
        == "hadeethenc-4555"
    )
    assert data["context_trace"] is not None


def test_verify_text_abstains_without_evidence() -> None:
    response = client.post(
        "/verify/text",
        json={
            "text": "ما حكم زكاة الذهب المعد للاستعمال؟"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "insufficient_evidence"
    assert data["source"] is None
    assert data["context_trace"] is None


def test_verify_text_rejects_empty_input() -> None:
    response = client.post(
        "/verify/text",
        json={"text": ""},
    )

    assert response.status_code == 422
