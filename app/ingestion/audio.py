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


def extract_audio_segments_with_quality(
    audio_path: str | Path,
) -> tuple[list[str], dict[str, float | int]]:
    """
    Transcribe Arabic audio and expose Whisper quality signals.
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

    segment_generator, _ = model.transcribe(
        str(path),
        language="ar",
        beam_size=5,
        temperature=0.0,
        vad_filter=True,
        condition_on_previous_text=False,
        initial_prompt=(
            "محتوى إسلامي باللغة العربية الفصحى، "
            "أحاديث نبوية، فتاوى، محاضرات شرعية، "
            "أسماء العلماء والمصطلحات الإسلامية."
        ),
    )

    whisper_segments = list(segment_generator)

    texts = [
        segment.text.strip()
        for segment in whisper_segments
        if segment.text.strip()
    ]

    log_probs = [
        float(segment.avg_logprob)
        for segment in whisper_segments
        if segment.text.strip()
    ]

    no_speech_probs = [
        float(segment.no_speech_prob)
        for segment in whisper_segments
        if segment.text.strip()
    ]

    metrics: dict[str, float | int] = {
        "segment_count": len(texts),
        "text_length": len(" ".join(texts)),
        "word_count": len(" ".join(texts).split()),
        "avg_logprob": (
            sum(log_probs) / len(log_probs)
            if log_probs
            else -99.0
        ),
        "avg_no_speech_prob": (
            sum(no_speech_probs) / len(no_speech_probs)
            if no_speech_probs
            else 1.0
        ),
        "max_no_speech_prob": (
            max(no_speech_probs)
            if no_speech_probs
            else 1.0
        ),
    }

    return texts, metrics


def extract_audio_segments(
    audio_path: str | Path,
) -> list[str]:
    """
    Backward-compatible transcript-only helper.
    """

    segments, _ = extract_audio_segments_with_quality(
        audio_path
    )

    return segments


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
