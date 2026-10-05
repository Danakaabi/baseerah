from app.verification.review_policy import (
    determine_review_policy,
)


def test_auto_supported():
    content = {
        "status": "verified",
    }

    authenticity = {
        "overall_status": "supported",
        "speaker_identity": {
            "interpretation": "trusted_match",
        },
        "synthetic_voice": {
            "interpretation": "likely_natural",
        },
    }

    result = determine_review_policy(
        content,
        authenticity,
    )

    assert result["decision"] == "auto_supported"
    assert result["human_review_required"] is False
    assert result["priority"] == "none"


def test_gray_zone_requires_human_review():
    content = {
        "status": "insufficient_evidence",
    }

    authenticity = {
        "overall_status": "needs_review",
        "speaker_identity": {
            "interpretation": "uncertain",
        },
        "synthetic_voice": {
            "interpretation": "likely_natural",
        },
    }

    result = determine_review_policy(
        content,
        authenticity,
    )

    assert result["decision"] == "human_review"
    assert result["human_review_required"] is True
    assert result["priority"] == "normal"
    assert len(result["reasons"]) >= 1


def test_synthetic_signal_gets_high_priority():
    content = {
        "status": "verified",
    }

    authenticity = {
        "overall_status": "needs_review",
        "speaker_identity": {
            "interpretation": "trusted_match",
        },
        "synthetic_voice": {
            "interpretation": "likely_synthetic",
        },
    }

    result = determine_review_policy(
        content,
        authenticity,
    )

    assert (
        result["decision"]
        == "high_priority_review"
    )
    assert result["human_review_required"] is True
    assert result["priority"] == "high"
