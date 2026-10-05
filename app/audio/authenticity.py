from pathlib import Path

from app.audio.deepfake_detection import detect_synthetic_voice
from app.audio.speaker_identification import identify_speaker


def analyze_audio_authenticity(
    audio_path: str | Path,
) -> dict:
    """
    Run BASEERAH audio-level verification.

    Speaker identity and synthetic-speech detection answer
    different questions and are intentionally kept separate.
    """

    speaker = identify_speaker(audio_path)
    synthetic = detect_synthetic_voice(audio_path)

    speaker_status = speaker.get(
        "interpretation",
        "unknown",
    )

    synthetic_status = synthetic.get(
        "interpretation",
        "uncertain",
    )

    reasons = []

    if synthetic_status == "likely_synthetic":
        overall_status = "needs_review"
        reasons.append(
            "Synthetic-speech indicators were detected."
        )

    elif synthetic_status == "uncertain":
        overall_status = "needs_review"
        reasons.append(
            "Synthetic-speech analysis is uncertain."
        )

    elif speaker_status == "trusted_match":
        overall_status = "supported"
        reasons.append(
            "The voice matches a trusted reference profile."
        )
        reasons.append(
            "No strong synthetic-speech indicators were detected."
        )

    else:
        overall_status = "needs_review"

        if speaker_status == "uncertain":
            reasons.append(
                "Speaker identity could not be confirmed."
            )
        else:
            reasons.append(
                "Speaker is not in the trusted voice registry."
            )

        reasons.append(
            "No strong synthetic-speech indicators were detected."
        )

    return {
        "overall_status": overall_status,
        "speaker_identity": speaker,
        "synthetic_voice": synthetic,
        "tampering_analysis": {
            "status": "not_enabled",
            "experimental": True,
            "reason": (
                "Current heuristic did not pass the controlled "
                "splice-detection validation."
            ),
        },
        "reasons": reasons,
        "disclaimer": (
            "This result is a verification aid, not definitive "
            "proof of audio authenticity. Speaker identity and "
            "synthetic-speech detection are separate signals."
        ),
    }
