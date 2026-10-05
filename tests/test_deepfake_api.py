from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_deepfake_endpoint_accepts_audio(monkeypatch):
    def fake_detector(_path):
        return {
            "interpretation": "likely_natural",
            "natural_score": 0.91,
            "synthetic_score": 0.09,
            "raw_logits": [-1.0, 1.0],
            "model": "test-model",
            "window_seconds": 4,
            "experimental": True,
            "calibration_status": "provisional_mvp_thresholds",
            "note": "test",
        }

    monkeypatch.setattr(
        "app.api.verify.detect_synthetic_voice",
        fake_detector,
    )

    response = client.post(
        "/verify/audio/deepfake",
        files={
            "audio": (
                "sample.wav",
                b"fake-audio-bytes",
                "audio/wav",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["interpretation"] == "likely_natural"
    assert data["experimental"] is True
    assert data["natural_score"] == 0.91


def test_deepfake_endpoint_rejects_non_audio():
    response = client.post(
        "/verify/audio/deepfake",
        files={
            "audio": (
                "sample.txt",
                b"not audio",
                "text/plain",
            )
        },
    )

    assert response.status_code == 415
