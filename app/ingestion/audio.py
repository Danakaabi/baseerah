from functools import lru_cache
from pathlib import Path

from faster_whisper import WhisperModel


SUPPORTED_AUDIO_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".m4a",
    ".ogg",
    ".webm",
}


@lru_cache(maxsize=1)
def get_whisper_model() -> WhisperModel:
    """
    Load and reuse Whisper for Arabic speech recognition.
    """

    return WhisperModel(
        "small",
        device="cpu",
        compute_type="int8",
    )


def extract_audio_segments(
    audio_path: str | Path,
) -> list[str]:
    """
    Transcribe Arabic audio into ordered text segments.
    """

    path = Path(audio_path)

    if not path.is_file():
        raise FileNotFoundError(
            f"Audio not found: {path}"
        )

    if path.suffix.lower() not in SUPPORTED_AUDIO_EXTENSIONS:
        raise ValueError(
            "Unsupported audio format."
        )

    model = get_whisper_model()

    segments, _ = model.transcribe(
        str(path),
        language="ar",
        beam_size=5,
        vad_filter=True,
    )

    return [
        segment.text.strip()
        for segment in segments
        if segment.text.strip()
    ]


def build_audio_windows(
    segments: list[str],
    max_window_size: int = 3,
    min_length: int = 15,
) -> list[str]:
    """
    Build consecutive transcript windows for semantic retrieval.
    """

    if max_window_size < 1:
        raise ValueError(
            "max_window_size must be at least 1"
        )

    cleaned_segments = [
        segment.strip()
        for segment in segments
        if isinstance(segment, str)
        and segment.strip()
    ]

    windows: list[str] = []

    for window_size in range(
        1,
        max_window_size + 1,
    ):
        for index in range(
            len(cleaned_segments)
            - window_size
            + 1
        ):
            text = " ".join(
                cleaned_segments[
                    index:index + window_size
                ]
            )

            if len(text) >= min_length:
                windows.append(text)

    return windows
