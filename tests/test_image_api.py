from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_verify_image_success(monkeypatch):
    """A valid image should reach the verification pipeline."""

    monkeypatch.setattr(
        "app.api.verify.extract_text_blocks",
        lambda path: [
            "إن الله لا ينظر إلى صوركم",
            "وأموالكم ولكن ينظر إلى",
            "قلوبكم وأعمالكم",
        ],
    )

    response = client.post(
        "/verify/image",
        files={
            "image": (
                "hadith.jpg",
                b"fake-image-bytes",
                "image/jpeg",
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


def test_verify_image_rejects_unsupported_type():
    """Non-image uploads should be rejected."""

    response = client.post(
        "/verify/image",
        files={
            "image": (
                "document.txt",
                b"not-an-image",
                "text/plain",
            )
        },
    )

    assert response.status_code == 415


def test_verify_image_rejects_empty_file():
    """Empty image uploads should be rejected."""

    response = client.post(
        "/verify/image",
        files={
            "image": (
                "empty.jpg",
                b"",
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 400
