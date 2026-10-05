from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_audio_authenticity_success(monkeypatch):
    def fake_analyze_audio_authenticity(path):
        return {
            "overall_status": "supported",
            "speaker_identity": {
                "interpretation": "trusted_match",
                "best_score": 0.98,
            },
            "synthetic_voice": {
                "interpretation": "likely_natural",
                "natural_score": 0.99,
                "synthetic_score": 0.01,
            },
            "tampering_analysis": {
                "status": "not_enabled",
                "experimental": True,
            },
            "reasons": [
                "The voice matches a trusted reference profile."
            ],
            "disclaimer": (
                "Verification aid only."
            ),
        }

    monkeypatch.setattr(
        "app.api.verify.analyze_audio_authenticity",
        fake_analyze_audio_authenticity,
    )

    response = client.post(
        "/verify/audio/authenticity",
        files={
            "audio": (
                "sample.wav",
                b"fake-audio-data",
                "audio/wav",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["overall_status"] == "supported"
    assert (
        data["speaker_identity"]["interpretation"]
        == "trusted_match"
    )
    assert (
        data["synthetic_voice"]["interpretation"]
        == "likely_natural"
    )


def test_audio_authenticity_rejects_non_audio():
    response = client.post(
        "/verify/audio/authenticity",
        files={
            "audio": (
                "sample.txt",
                b"not audio",
                "text/plain",
            )
        },
    )

    assert response.status_code == 415
