from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_full_audio_verification_success(
    monkeypatch,
):
    class FakeVerificationResult:
        def model_dump(self):
            return {
                "status": "verified",
                "score": 0.91,
                "source": {
                    "title": "Trusted source",
                },
            }

    class FakeVerifier:
        def verify_quote_candidates(
            self,
            windows,
        ):
            assert windows == [
                "verified speech"
            ]
            return FakeVerificationResult()

    monkeypatch.setattr(
        "app.api.verify.extract_audio_segments",
        lambda path: ["speech segment"],
    )

    monkeypatch.setattr(
        "app.api.verify.build_audio_windows",
        lambda segments: ["verified speech"],
    )

    monkeypatch.setattr(
        "app.api.verify.get_verifier",
        lambda: FakeVerifier(),
    )

    monkeypatch.setattr(
        "app.api.verify.analyze_audio_authenticity",
        lambda path: {
            "overall_status": "supported",
            "speaker_identity": {
                "interpretation":
                    "trusted_match",
                "best_score": 0.98,
            },
            "synthetic_voice": {
                "interpretation":
                    "likely_natural",
                "natural_score": 0.99,
                "synthetic_score": 0.01,
            },
            "tampering_analysis": {
                "status": "not_enabled",
                "experimental": True,
            },
            "reasons": [],
        },
    )

    response = client.post(
        "/verify/audio/full",
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

    assert (
        data["verification_type"]
        == "baseerah_full_audio"
    )

    assert data["review_status"] == "supported"

    assert (
        data["content_verification"]["status"]
        == "verified"
    )

    assert (
        data["audio_authenticity"]
        ["speaker_identity"]
        ["interpretation"]
        == "trusted_match"
    )

    assert (
        data["audio_authenticity"]
        ["synthetic_voice"]
        ["interpretation"]
        == "likely_natural"
    )


def test_full_audio_verification_needs_review(
    monkeypatch,
):
    class FakeVerificationResult:
        def model_dump(self):
            return {
                "status":
                    "insufficient_evidence",
            }

    class FakeVerifier:
        def verify_quote_candidates(
            self,
            windows,
        ):
            return FakeVerificationResult()

    monkeypatch.setattr(
        "app.api.verify.extract_audio_segments",
        lambda path: ["speech"],
    )

    monkeypatch.setattr(
        "app.api.verify.build_audio_windows",
        lambda segments: ["speech"],
    )

    monkeypatch.setattr(
        "app.api.verify.get_verifier",
        lambda: FakeVerifier(),
    )

    monkeypatch.setattr(
        "app.api.verify.analyze_audio_authenticity",
        lambda path: {
            "overall_status": "needs_review",
            "speaker_identity": {
                "interpretation": "uncertain",
            },
            "synthetic_voice": {
                "interpretation":
                    "likely_synthetic",
            },
            "tampering_analysis": {
                "status": "not_enabled",
            },
            "reasons": [
                "Synthetic-speech indicators detected."
            ],
        },
    )

    response = client.post(
        "/verify/audio/full",
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

    assert (
        data["review_status"]
        == "needs_review"
    )

    assert len(
        data["review_reasons"]
    ) >= 1


def test_full_audio_rejects_non_audio():
    response = client.post(
        "/verify/audio/full",
        files={
            "audio": (
                "sample.txt",
                b"not-audio",
                "text/plain",
            )
        },
    )

    assert response.status_code == 415
