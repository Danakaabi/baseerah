import pytest
from fastapi.testclient import TestClient

from app.main import app
import app.api.verify as verify_api


@pytest.mark.parametrize("score, expected", [
    (0.7062869, "low_similarity"),
    (0.9020602, "uncertain"),
    (0.9219809, "uncertain"),
    (0.9418507, "uncertain"),
    (0.95, "strong_match"),
    (0.976622, "strong_match"),
])
def test_comparison_policy_does_not_confirm_identity(monkeypatch, score, expected):
    # Tests the API decision policy; does not evaluate the real model's accuracy.
    monkeypatch.setattr(verify_api, "compare_speakers",
                        lambda a, b: {"speaker_similarity": score})
    with TestClient(app) as client:
        response = client.post("/verify/speaker", files={
            "reference_audio": ("reference.wav", b"test", "audio/wav"),
            "candidate_audio": ("candidate.wav", b"test", "audio/wav"),
        })
    assert response.status_code == 200
    result = response.json()
    assert result["speaker_similarity"] == score
    assert result["speaker_interpretation"] == expected
    assert result["decision_threshold"] == 0.95
    assert result["identity_confirmed"] is False
