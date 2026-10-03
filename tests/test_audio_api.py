from fastapi.testclient import TestClient

from app.main import app
import app.api.verify as verify_api


client = TestClient(app)


def test_verify_audio_returns_evidence(
    monkeypatch,
):
    monkeypatch.setattr(
        verify_api,
        "extract_audio_segments",
        lambda path: [
            (
                "سئل النبي صلى الله عليه وسلم "
                "أي الأعمال أفضل فقال إيمان بالله ورسوله "
                "ثم الجهاد في سبيل الله ثم حج مبرور"
            )
        ],
    )

    response = client.post(
        "/verify/audio",
        files={
            "audio": (
                "test.wav",
                b"fake-audio-data",
                "audio/wav",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "evidence_found"
    assert data["source"] is not None
    assert (
        data["source"]["source_id"]
        == "dorar-bukhari-1519"
    )
    assert data["context_trace"] is not None


def test_verify_audio_rejects_unsupported_type():
    response = client.post(
        "/verify/audio",
        files={
            "audio": (
                "test.txt",
                b"not-audio",
                "text/plain",
            )
        },
    )

    assert response.status_code == 415


def test_verify_audio_rejects_empty_file():
    response = client.post(
        "/verify/audio",
        files={
            "audio": (
                "empty.wav",
                b"",
                "audio/wav",
            )
        },
    )

    assert response.status_code == 400
