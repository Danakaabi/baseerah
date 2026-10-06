from functools import lru_cache
from pathlib import Path
import tempfile

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
)

from app.audio.deepfake_detection import detect_synthetic_voice
from app.audio.speaker_identification import identify_speaker
from app.audio.speaker_verification import (
    MODEL_NAME,
    compare_speakers,
)
from app.ingestion.audio import (
    build_audio_windows,
    extract_audio_segments,
)
from app.audio.authenticity import analyze_audio_authenticity
from app.verification.review_policy import determine_review_policy
from app.ingestion.image import (
    build_text_windows,
    extract_text_blocks,
)
from app.models.schemas import (
    VerificationResult,
    VerifyTextRequest,
)
from app.verification.verifier import Verifier


router = APIRouter(
    prefix="/verify",
    tags=["Verification"],
)


ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

MAX_IMAGE_SIZE = 5 * 1024 * 1024

ALLOWED_AUDIO_TYPES = {
    "audio/mpeg": ".mp3",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/mp4": ".m4a",
    "audio/x-m4a": ".m4a",
    "audio/ogg": ".ogg",
    "audio/webm": ".webm",
}

MAX_AUDIO_SIZE = 25 * 1024 * 1024

# Conservative demo policy after observed cross-speaker scores up to 0.922.
# This is not a validated identity threshold or a probability of a match.
SPEAKER_COMPARISON_THRESHOLD = 0.95


@lru_cache(maxsize=1)
def get_verifier() -> Verifier:
    """Load and reuse the BASEERAH verification engine."""

    return Verifier()


@router.post(
    "/text",
    response_model=VerificationResult,
)
async def verify_text(
    request: VerifyTextRequest,
) -> VerificationResult:
    """Verify submitted text against trusted sources."""

    verifier = get_verifier()

    return verifier.verify(request.text)


@router.post(
    "/image",
    response_model=VerificationResult,
)
async def verify_image(
    image: UploadFile = File(...),
) -> VerificationResult:
    """
    Extract Arabic text from an uploaded image and verify it
    against trusted sources.
    """

    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=415,
            detail=(
                "Unsupported image format. "
                "Use JPG, PNG, or WEBP."
            ),
        )

    image_bytes = await image.read()

    if not image_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded image is empty.",
        )

    if len(image_bytes) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Image exceeds the 5 MB limit.",
        )

    suffix = ALLOWED_IMAGE_TYPES[image.content_type]

    temp_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=suffix,
            delete=False,
        ) as temp_file:
            temp_file.write(image_bytes)
            temp_path = Path(temp_file.name)

        blocks = extract_text_blocks(temp_path)
        windows = build_text_windows(blocks)

        if not windows:
            raise HTTPException(
                status_code=422,
                detail=(
                    "No usable Arabic text was "
                    "detected in the image."
                ),
            )

        verifier = get_verifier()

        return verifier.verify_quote_candidates(windows)

    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


@router.post(
    "/audio",
    response_model=VerificationResult,
)
async def verify_audio(
    audio: UploadFile = File(...),
) -> VerificationResult:
    """
    Transcribe Arabic audio and verify quoted content
    against trusted sources.
    """

    if audio.content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=415,
            detail=(
                "Unsupported audio format. "
                "Use MP3, WAV, M4A, OGG, or WEBM."
            ),
        )

    audio_bytes = await audio.read()

    if not audio_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded audio is empty.",
        )

    if len(audio_bytes) > MAX_AUDIO_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Audio exceeds the 25 MB limit.",
        )

    suffix = ALLOWED_AUDIO_TYPES[audio.content_type]

    temp_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=suffix,
            delete=False,
        ) as temp_file:
            temp_file.write(audio_bytes)
            temp_path = Path(temp_file.name)

        segments = extract_audio_segments(
            temp_path
        )

        windows = build_audio_windows(
            segments
        )

        if not windows:
            raise HTTPException(
                status_code=422,
                detail=(
                    "No usable Arabic speech was "
                    "detected in the audio."
                ),
            )

        verifier = get_verifier()

        return verifier.verify_quote_candidates(
            windows
        )

    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


@router.post("/speaker")
async def verify_speaker(
    reference_audio: UploadFile = File(...),
    candidate_audio: UploadFile = File(...),
) -> dict:
    """
    Compare a candidate voice with a trusted reference voice.

    The returned similarity is cosine similarity between
    WavLM speaker embeddings. It is not a probability.
    """

    uploads = {
        "reference_audio": reference_audio,
        "candidate_audio": candidate_audio,
    }

    temp_paths: list[Path] = []

    try:
        saved_paths: dict[str, Path] = {}

        for name, upload in uploads.items():
            if upload.content_type not in ALLOWED_AUDIO_TYPES:
                raise HTTPException(
                    status_code=415,
                    detail=(
                        f"Unsupported format for {name}. "
                        "Use MP3, WAV, M4A, OGG, or WEBM."
                    ),
                )

            data = await upload.read()

            if not data:
                raise HTTPException(
                    status_code=400,
                    detail=f"{name} is empty.",
                )

            if len(data) > MAX_AUDIO_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail=f"{name} exceeds the 25 MB limit.",
                )

            suffix = ALLOWED_AUDIO_TYPES[
                upload.content_type
            ]

            with tempfile.NamedTemporaryFile(
                suffix=suffix,
                delete=False,
            ) as temp_file:
                temp_file.write(data)
                path = Path(temp_file.name)

            temp_paths.append(path)
            saved_paths[name] = path

        result = compare_speakers(
            saved_paths["reference_audio"],
            saved_paths["candidate_audio"],
        )

        similarity = max(
            -1.0,
            min(
                1.0,
                float(result["speaker_similarity"]),
            ),
        )

        if similarity >= SPEAKER_COMPARISON_THRESHOLD:
            interpretation = "strong_match"
        elif similarity >= 0.80:
            interpretation = "uncertain"
        else:
            interpretation = "low_similarity"

        return {
            "reference_available": True,
            "speaker_similarity": similarity,
            "speaker_interpretation": interpretation,
            "metric": "cosine_similarity",
            "model": MODEL_NAME,
            "analysis_seconds": 20,
            "decision_threshold": SPEAKER_COMPARISON_THRESHOLD,
            "identity_confirmed": False,
            "calibration_status": "mvp_thresholds_not_final",
        }

    finally:
        for path in temp_paths:
            path.unlink(missing_ok=True)


@router.post("/speaker/identify")
async def identify_uploaded_speaker(
    audio: UploadFile = File(...),
) -> dict:
    """
    Compare one uploaded audio file against BASEERAH's
    trusted speaker profiles.

    Similarity values are cosine similarities, not
    identity probabilities.
    """

    filename = audio.filename or ""
    extension = Path(filename).suffix.lower()

    allowed_extensions = {
        ".mp3",
        ".wav",
        ".m4a",
        ".ogg",
        ".webm",
    }

    if (
        audio.content_type not in ALLOWED_AUDIO_TYPES
        and extension not in allowed_extensions
    ):
        raise HTTPException(
            status_code=415,
            detail=(
                "Unsupported audio format. "
                "Use MP3, WAV, M4A, OGG, or WEBM."
            ),
        )

    audio_bytes = await audio.read()

    if not audio_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded audio is empty.",
        )

    if len(audio_bytes) > MAX_AUDIO_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Audio exceeds the 25 MB limit.",
        )

    suffix = ALLOWED_AUDIO_TYPES.get(
        audio.content_type,
        extension,
    )
    temp_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=suffix,
            delete=False,
        ) as temp_file:
            temp_file.write(audio_bytes)
            temp_path = Path(temp_file.name)

        result = identify_speaker(temp_path)

        if result.get("reason") == "no_trusted_profiles":
            raise HTTPException(
                status_code=503,
                detail="No trusted speaker profiles are available.",
            )

        return result

    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

@router.post("/audio/deepfake")
async def verify_audio_deepfake(
    audio: UploadFile = File(...),
) -> dict:
    """
    Analyze an uploaded audio clip for synthetic/deepfake
    speech indicators.

    This detector is experimental. Returned scores are model
    outputs and are not calibrated probabilities of authenticity.
    """

    content_type = audio.content_type or ""
    filename = audio.filename or ""
    extension = Path(filename).suffix.lower()

    allowed_extensions = {
        ".mp3",
        ".wav",
        ".m4a",
        ".ogg",
        ".webm",
    }

    if (
        content_type not in ALLOWED_AUDIO_TYPES
        and extension not in allowed_extensions
    ):
        raise HTTPException(
            status_code=415,
            detail=(
                "Unsupported audio format. "
                "Use MP3, WAV, M4A, OGG, or WEBM."
            ),
        )

    audio_bytes = await audio.read()

    if not audio_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded audio is empty.",
        )

    if len(audio_bytes) > MAX_AUDIO_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Audio exceeds the 25 MB limit.",
        )

    suffix = (
        ALLOWED_AUDIO_TYPES.get(content_type)
        or extension
        or ".wav"
    )

    temp_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=suffix,
            delete=False,
        ) as temp_file:
            temp_file.write(audio_bytes)
            temp_path = Path(temp_file.name)

        try:
            return detect_synthetic_voice(temp_path)

        except Exception as exc:
            raise HTTPException(
                status_code=422,
                detail=(
                    "The audio could not be analyzed "
                    "for synthetic speech."
                ),
            ) from exc

    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

@router.post("/audio/authenticity")
async def verify_audio_authenticity(
    audio: UploadFile = File(...),
):
    allowed_extensions = {
        ".mp3",
        ".wav",
        ".m4a",
        ".ogg",
        ".webm",
    }

    suffix = Path(audio.filename or "").suffix.lower()

    content_type = (
        audio.content_type or ""
    ).lower()

    if (
        not content_type.startswith("audio/")
        and suffix not in allowed_extensions
    ):
        raise HTTPException(
            status_code=415,
            detail="Unsupported audio format.",
        )

    data = await audio.read()

    if not data:
        raise HTTPException(
            status_code=400,
            detail="Empty audio file.",
        )

    max_size = 25 * 1024 * 1024

    if len(data) > max_size:
        raise HTTPException(
            status_code=413,
            detail="Audio file is too large. Maximum size is 25 MB.",
        )

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=suffix or ".wav",
            delete=False,
        ) as tmp:
            tmp.write(data)
            temp_path = Path(tmp.name)

        result = analyze_audio_authenticity(
            temp_path
        )

        return result

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=422,
            detail=(
                "The audio could not be analyzed "
                "for authenticity."
            ),
        )

    finally:
        if temp_path is not None:
            temp_path.unlink(
                missing_ok=True
            )



@router.post("/audio/full")
async def verify_audio_full(
    audio: UploadFile = File(...),
):
    """
    Run the complete BASEERAH audio verification pipeline.

    The report combines:
    1. Speech-to-text and trusted-source content verification.
    2. Trusted speaker identification.
    3. Synthetic-speech detection.

    These signals are reported separately because none of them
    alone proves that an audio recording is authentic.
    """

    if audio.content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=415,
            detail=(
                "Unsupported audio format. "
                "Use MP3, WAV, M4A, OGG, or WEBM."
            ),
        )

    audio_bytes = await audio.read()

    if not audio_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded audio is empty.",
        )

    if len(audio_bytes) > MAX_AUDIO_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Audio exceeds the 25 MB limit.",
        )

    suffix = ALLOWED_AUDIO_TYPES[
        audio.content_type
    ]

    temp_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=suffix,
            delete=False,
        ) as temp_file:
            temp_file.write(audio_bytes)
            temp_path = Path(temp_file.name)

        # -----------------------------------------
        # 1. Content verification
        # Whisper -> text windows -> RAG
        # -----------------------------------------

        segments = extract_audio_segments(
            temp_path
        )

        windows = build_audio_windows(
            segments
        )

        if windows:
            verifier = get_verifier()

            content_result = (
                verifier.verify_quote_candidates(
                    windows
                )
            )

            if hasattr(
                content_result,
                "model_dump",
            ):
                content_result = (
                    content_result.model_dump()
                )

        else:
            content_result = {
                "status": "insufficient_evidence",
                "message": (
                    "No usable Arabic speech was "
                    "detected for content verification."
                ),
            }

        # -----------------------------------------
        # 2. Audio-level authenticity signals
        # Speaker + synthetic speech
        # -----------------------------------------

        authenticity_result = (
            analyze_audio_authenticity(
                temp_path
            )
        )

        # -----------------------------------------
        # 3. Human-review policy
        # -----------------------------------------

        review_policy = determine_review_policy(
            content_result,
            authenticity_result,
        )

        review_status = (
            "supported"
            if not review_policy[
                "human_review_required"
            ]
            else "needs_review"
        )

        review_reasons = review_policy[
            "reasons"
        ]

        return {
            "verification_type":
                "baseerah_full_audio",
            "review_status":
                review_status,
            "review_policy":
                review_policy,
            "content_verification":
                content_result,
            "audio_authenticity":
                authenticity_result,
            "review_reasons":
                review_reasons,
            "disclaimer": (
                "BASEERAH combines independent "
                "verification signals. Results are "
                "decision-support indicators and do "
                "not constitute definitive forensic "
                "proof of authenticity."
            ),
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=422,
            detail=(
                "The audio could not be processed "
                "by the full verification pipeline."
            ),
        )

    finally:
        if temp_path is not None:
            temp_path.unlink(
                missing_ok=True
            )
