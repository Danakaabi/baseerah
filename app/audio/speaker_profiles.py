import json
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
VOICE_PROFILES_DIR = PROJECT_ROOT / "data" / "voice_profiles"


@dataclass(frozen=True)
class SpeakerProfile:
    speaker_id: str
    speaker_name: str
    status: str
    official_source_name: str
    reference_audio: Path
    reference_title: str
    source_id: str | None = None


def load_speaker_profiles() -> list[SpeakerProfile]:
    profiles: list[SpeakerProfile] = []

    if not VOICE_PROFILES_DIR.exists():
        return profiles

    for profile_path in sorted(
        VOICE_PROFILES_DIR.glob("*/profile.json")
    ):
        data = json.loads(
            profile_path.read_text(encoding="utf-8")
        )

        reference_audio = (
            profile_path.parent / data["reference_audio"]
        )

        if not reference_audio.exists():
            raise FileNotFoundError(
                f"Reference audio not found: {reference_audio}"
            )

        profiles.append(
            SpeakerProfile(
                speaker_id=data["speaker_id"],
                speaker_name=data["speaker_name"],
                status=data["status"],
                official_source_name=data["official_source_name"],
                reference_audio=reference_audio,
                reference_title=data["reference_title"],
                source_id=data.get("source_id"),
            )
        )

    return profiles
