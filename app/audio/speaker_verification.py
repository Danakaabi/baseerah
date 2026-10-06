from __future__ import annotations
from functools import lru_cache
from pathlib import Path
import subprocess
import tempfile
import wave

import numpy as np



MODEL_NAME = "microsoft/wavlm-base-plus-sv"


@lru_cache(maxsize=1)
def get_speaker_model():
    import torch
    from transformers import AutoFeatureExtractor, WavLMForXVector

    feature_extractor = AutoFeatureExtractor.from_pretrained(
        MODEL_NAME
    )
    model = WavLMForXVector.from_pretrained(
        MODEL_NAME
    )

    device = "cpu"

    model = model.to(device)
    model.eval()

    return feature_extractor, model, device


def convert_to_wav_16k_mono(
    audio_path: str | Path,
) -> Path:
    source = Path(audio_path)

    if not source.is_file():
        raise FileNotFoundError(
            f"Audio not found: {source}"
        )

    temp = tempfile.NamedTemporaryFile(
        suffix=".wav",
        delete=False,
    )
    temp.close()

    output_path = Path(temp.name)

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source),
            "-t",
            "20",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-f",
            "wav",
            str(output_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    return output_path


def load_wav_pcm16(
    wav_path: str | Path,
) -> np.ndarray:
    path = Path(wav_path)

    with wave.open(str(path), "rb") as wav_file:
        if wav_file.getsampwidth() != 2:
            raise ValueError("Expected 16-bit PCM WAV.")

        if wav_file.getnchannels() != 1:
            raise ValueError("Expected mono WAV.")

        if wav_file.getframerate() != 16000:
            raise ValueError("Expected 16 kHz WAV.")

        frames = wav_file.readframes(
            wav_file.getnframes()
        )

    audio = np.frombuffer(
        frames,
        dtype=np.int16,
    ).astype(np.float32)

    return audio / 32768.0


def extract_speaker_embedding(
    audio_path: str | Path,
) -> np.ndarray:
    import torch
    wav_path = convert_to_wav_16k_mono(
        audio_path
    )

    try:
        waveform = load_wav_pcm16(
            wav_path
        )

        feature_extractor, model, device = get_speaker_model()

        inputs = feature_extractor(
            waveform,
            sampling_rate=16000,
            return_tensors="pt",
        )

        input_values = inputs["input_values"].to(
            device
        )

        with torch.no_grad():
            outputs = model(
                input_values
            )

        embedding = outputs.embeddings[0]

        embedding = torch.nn.functional.normalize(
            embedding,
            dim=0,
        )

        return (
            embedding
            .detach()
            .cpu()
            .numpy()
            .astype(np.float32)
        )

    finally:
        wav_path.unlink(
            missing_ok=True
        )


def compare_speakers(
    audio_a: str | Path,
    audio_b: str | Path,
) -> dict[str, float]:
    embedding_a = extract_speaker_embedding(
        audio_a
    )

    embedding_b = extract_speaker_embedding(
        audio_b
    )

    similarity = float(
        np.dot(
            embedding_a,
            embedding_b,
        )
    )

    return {
        "speaker_similarity": similarity,
    }
