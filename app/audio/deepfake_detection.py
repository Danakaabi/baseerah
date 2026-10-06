from functools import lru_cache
from pathlib import Path
import subprocess
import tempfile
import wave

import numpy as np



MODEL_REPO = "SpeechAntiSpoofingBenchmarks/Wav2Vec2-Small-AntiDeepfake"
MODEL_FILE = "wav2vec2-small-antideepfake.onnx"

SAMPLE_RATE = 16000
WINDOW_SAMPLES = 64000  # 4 seconds


@lru_cache(maxsize=1)
def get_deepfake_session():
    import onnxruntime as ort
    from huggingface_hub import hf_hub_download

    model_path = hf_hub_download(
        repo_id=MODEL_REPO,
        filename=MODEL_FILE,
    )

    return ort.InferenceSession(
        model_path,
        providers=["CPUExecutionProvider"],
    )


def _prepare_audio(audio_path: str | Path) -> np.ndarray:
    audio_path = Path(audio_path)

    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(audio_path),
                "-ac",
                "1",
                "-ar",
                str(SAMPLE_RATE),
                "-t",
                "4",
                "-f",
                "wav",
                tmp.name,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )

        with wave.open(tmp.name, "rb") as wf:
            audio = np.frombuffer(
                wf.readframes(wf.getnframes()),
                dtype=np.int16,
            ).astype(np.float32) / 32768.0

    if len(audio) < WINDOW_SAMPLES:
        audio = np.pad(
            audio,
            (0, WINDOW_SAMPLES - len(audio)),
        )
    else:
        audio = audio[:WINDOW_SAMPLES]

    return audio.reshape(1, WINDOW_SAMPLES).astype(np.float32)


def detect_synthetic_voice(audio_path: str | Path) -> dict:
    session = get_deepfake_session()
    audio = _prepare_audio(audio_path)

    logits = session.run(
        ["logits"],
        {"wav": audio},
    )[0][0]

    shifted = logits - np.max(logits)
    exp = np.exp(shifted)
    scores = exp / exp.sum()

    synthetic_score = float(scores[0])
    natural_score = float(scores[1])

    # Conservative MVP interpretation.
    # These are provisional thresholds, not calibrated probabilities.
    if natural_score >= 0.80:
        interpretation = "likely_natural"
    elif synthetic_score >= 0.80:
        interpretation = "likely_synthetic"
    else:
        interpretation = "uncertain"

    return {
        "interpretation": interpretation,
        "natural_score": natural_score,
        "synthetic_score": synthetic_score,
        "raw_logits": [
            float(logits[0]),
            float(logits[1]),
        ],
        "model": MODEL_REPO,
        "window_seconds": 4,
        "experimental": True,
        "calibration_status": "provisional_mvp_thresholds",
        "note": (
            "Scores are model outputs and must not be interpreted "
            "as calibrated probabilities of authenticity."
        ),
    }
