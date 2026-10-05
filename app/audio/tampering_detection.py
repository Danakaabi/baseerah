from pathlib import Path
import subprocess
import tempfile
import wave

import numpy as np


SAMPLE_RATE = 16000

# Compare independent 100 ms windows on both sides
# of each candidate boundary.
WINDOW_MS = 100
WINDOW_SIZE = int(SAMPLE_RATE * WINDOW_MS / 1000)

# Analyze a candidate boundary every 20 ms.
HOP_MS = 20
HOP_SIZE = int(SAMPLE_RATE * HOP_MS / 1000)


def _load_audio(audio_path: str | Path) -> np.ndarray:
    audio_path = Path(audio_path)

    if not audio_path.exists():
        raise FileNotFoundError(
            f"Audio file not found: {audio_path}"
        )

    with tempfile.NamedTemporaryFile(
        suffix=".wav"
    ) as tmp:
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
                "-f",
                "wav",
                tmp.name,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )

        with wave.open(tmp.name, "rb") as wf:
            samples = np.frombuffer(
                wf.readframes(wf.getnframes()),
                dtype=np.int16,
            ).astype(np.float32)

    if samples.size == 0:
        raise ValueError("Audio contains no samples.")

    return samples / 32768.0


def _robust_z(values: np.ndarray) -> np.ndarray:
    median = np.median(values)
    mad = np.median(
        np.abs(values - median)
    )

    if mad < 1e-9:
        return np.zeros_like(values)

    return (
        np.abs(values - median)
        / (1.4826 * mad)
    )


def detect_tampering_indicators(
    audio_path: str | Path,
) -> dict:
    """
    Detect abrupt acoustic discontinuities that may indicate
    an edit boundary.

    Experimental heuristic only. A detected discontinuity
    does not prove manipulation.
    """

    audio = _load_audio(audio_path)
    duration = len(audio) / SAMPLE_RATE

    if len(audio) < WINDOW_SIZE * 3:
        return {
            "interpretation": "uncertain",
            "duration_seconds": round(duration, 3),
            "indicator_count": 0,
            "candidate_boundaries": [],
            "experimental": True,
            "method": "acoustic_discontinuity_heuristics_v2",
            "note": "Audio is too short for analysis.",
        }

    positions = np.arange(
        WINDOW_SIZE,
        len(audio) - WINDOW_SIZE,
        HOP_SIZE,
    )

    energy_changes = []
    spectral_changes = []
    waveform_jumps = []

    hann = np.hanning(
        WINDOW_SIZE
    ).astype(np.float32)

    for pos in positions:
        before = audio[
            pos - WINDOW_SIZE:pos
        ]
        after = audio[
            pos:pos + WINDOW_SIZE
        ]

        before_rms = np.sqrt(
            np.mean(before ** 2) + 1e-12
        )
        after_rms = np.sqrt(
            np.mean(after ** 2) + 1e-12
        )

        energy_changes.append(
            abs(
                np.log(after_rms + 1e-8)
                - np.log(before_rms + 1e-8)
            )
        )

        before_spec = np.abs(
            np.fft.rfft(before * hann)
        )
        after_spec = np.abs(
            np.fft.rfft(after * hann)
        )

        before_spec /= (
            np.linalg.norm(before_spec)
            + 1e-12
        )
        after_spec /= (
            np.linalg.norm(after_spec)
            + 1e-12
        )

        spectral_changes.append(
            np.linalg.norm(
                after_spec - before_spec
            )
        )

        # Actual waveform discontinuity exactly
        # across the candidate boundary.
        waveform_jumps.append(
            abs(
                float(audio[pos])
                - float(audio[pos - 1])
            )
        )

    energy_changes = np.asarray(
        energy_changes,
        dtype=np.float32,
    )
    spectral_changes = np.asarray(
        spectral_changes,
        dtype=np.float32,
    )
    waveform_jumps = np.asarray(
        waveform_jumps,
        dtype=np.float32,
    )

    energy_z = _robust_z(energy_changes)
    spectral_z = _robust_z(spectral_changes)
    jump_z = _robust_z(waveform_jumps)

    # Spectral change carries the largest weight because
    # speaker/environment changes often appear there.
    combined = (
        0.45 * spectral_z
        + 0.35 * energy_z
        + 0.20 * jump_z
    )

    candidates = np.where(
        (
            (combined >= 4.0)
            & (spectral_z >= 2.5)
            & (
                (energy_z >= 2.0)
                | (jump_z >= 2.0)
            )
        )
    )[0]

    raw_boundaries = []

    for index in candidates:
        raw_boundaries.append(
            {
                "time_seconds": float(
                    positions[index]
                    / SAMPLE_RATE
                ),
                "indicator_strength": float(
                    combined[index]
                ),
            }
        )

    # Keep strongest point within each 300 ms region.
    raw_boundaries.sort(
        key=lambda x: x["indicator_strength"],
        reverse=True,
    )

    selected = []

    for candidate in raw_boundaries:
        if all(
            abs(
                candidate["time_seconds"]
                - existing["time_seconds"]
            ) >= 0.30
            for existing in selected
        ):
            selected.append(candidate)

    selected.sort(
        key=lambda x: x["time_seconds"]
    )

    boundaries = [
        {
            "time_seconds": round(
                item["time_seconds"],
                3,
            ),
            "indicator_strength": round(
                item["indicator_strength"],
                3,
            ),
        }
        for item in selected[:20]
    ]

    if not boundaries:
        interpretation = "no_strong_indicators"
    elif len(boundaries) <= 3:
        interpretation = "possible_edit_boundary"
    else:
        interpretation = "multiple_discontinuities"

    return {
        "interpretation": interpretation,
        "duration_seconds": round(duration, 3),
        "indicator_count": len(boundaries),
        "candidate_boundaries": boundaries,
        "experimental": True,
        "method": "acoustic_discontinuity_heuristics_v2",
        "note": (
            "Detected discontinuities are indicators only. "
            "Natural pauses, noise, compression, microphone "
            "changes, and recording conditions may produce "
            "similar patterns."
        ),
    }
