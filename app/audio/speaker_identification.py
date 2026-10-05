from pathlib import Path

from app.audio.speaker_profiles import load_speaker_profiles
from app.audio.speaker_verification import compare_speakers


def identify_speaker(candidate_audio: str | Path) -> dict:
    """
    Compare one candidate audio file against all trusted
    speaker profiles and return the closest match.
    """

    profiles = load_speaker_profiles()

    if not profiles:
        return {
            "match_found": False,
            "reason": "no_trusted_profiles",
        }

    results: list[dict] = []

    for profile in profiles:
        comparison = compare_speakers(
            str(profile.reference_audio),
            str(candidate_audio),
        )

        similarity = float(
            comparison["speaker_similarity"]
        )

        results.append(
            {
                "speaker_id": profile.speaker_id,
                "speaker_name": profile.speaker_name,
                "speaker_similarity": similarity,
                "official_source_name": profile.official_source_name,
                "reference_title": profile.reference_title,
                "source_id": profile.source_id,
            }
        )

    results.sort(
        key=lambda item: item["speaker_similarity"],
        reverse=True,
    )

    best = results[0]

    # Calibration-aware MVP decision.
    best_score = best["speaker_similarity"]

    second_score = (
        results[1]["speaker_similarity"]
        if len(results) > 1
        else 0.0
    )

    margin = best_score - second_score

    if best_score >= 0.95 and margin >= 0.10:
        interpretation = "trusted_match"
    elif best_score >= 0.85:
        interpretation = "uncertain"
    else:
        interpretation = "unknown"

    return {
        "match_found": interpretation == "trusted_match",
        "best_match": best,
        "interpretation": interpretation,
        "best_score": best_score,
        "second_score": second_score,
        "margin": margin,
        "all_matches": results,
        "calibration_status": "provisional_mvp_thresholds",
    }
