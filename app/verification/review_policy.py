def determine_review_policy(
    content_verification: dict,
    audio_authenticity: dict,
) -> dict:
    """
    Decide whether a BASEERAH result can be presented as
    supported or should be escalated for human review.

    This policy does not claim forensic certainty.
    """

    content_status = content_verification.get(
        "status",
        "unknown",
    )

    authenticity_status = audio_authenticity.get(
        "overall_status",
        "needs_review",
    )

    speaker_status = (
        audio_authenticity
        .get("speaker_identity", {})
        .get("interpretation", "unknown")
    )

    synthetic_status = (
        audio_authenticity
        .get("synthetic_voice", {})
        .get("interpretation", "uncertain")
    )

    reasons = []

    # Strongest escalation:
    # synthetic-speech detector raised a flag.
    if synthetic_status == "likely_synthetic":
        return {
            "decision": "high_priority_review",
            "human_review_required": True,
            "priority": "high",
            "reasons": [
                (
                    "Synthetic-speech indicators "
                    "were detected."
                )
            ],
        }

    if synthetic_status == "uncertain":
        reasons.append(
            "Synthetic-speech analysis is uncertain."
        )

    if speaker_status != "trusted_match":
        reasons.append(
            "Speaker identity is not confirmed."
        )

    if content_status in {
        "insufficient_evidence",
        "not_found",
        "unknown",
    }:
        reasons.append(
            "Trusted-source evidence is insufficient."
        )

    if authenticity_status != "supported":
        reasons.append(
            "Audio-level verification is not fully supported."
        )

    if reasons:
        return {
            "decision": "human_review",
            "human_review_required": True,
            "priority": "normal",
            "reasons": reasons,
        }

    return {
        "decision": "auto_supported",
        "human_review_required": False,
        "priority": "none",
        "reasons": [
            (
                "Available verification signals "
                "are mutually supportive."
            )
        ],
    }
