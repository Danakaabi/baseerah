from functools import lru_cache
from pathlib import Path
import tempfile

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
)

from app.ingestion.audio import (
    build_audio_windows,
    extract_audio_segments,
)
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
