from functools import lru_cache
from pathlib import Path




SUPPORTED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


@lru_cache(maxsize=1)
def get_ocr_reader():
    """
    Load and reuse the Arabic EasyOCR reader.
    """

    import easyocr

    return easyocr.Reader(
        ["ar"],
        gpu=False,
    )


def extract_text_blocks(
    image_path: str | Path,
) -> list[str]:
    """
    Extract ordered Arabic text blocks from an image.

    Blocks are kept separate so later stages can build
    sliding windows instead of treating the entire image
    as one retrieval query.
    """

    path = Path(image_path)

    if not path.is_file():
        raise FileNotFoundError(
            f"Image not found: {path}"
        )

    if path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        raise ValueError(
            "Unsupported image format. "
            "Use JPG, JPEG, PNG, or WEBP."
        )

    reader = get_ocr_reader()

    results = reader.readtext(
        str(path),
        detail=0,
        paragraph=False,
    )

    blocks = [
        text.strip()
        for text in results
        if isinstance(text, str)
        and text.strip()
    ]

    return blocks


def build_text_windows(
    blocks: list[str],
    max_window_size: int = 3,
    min_length: int = 15,
) -> list[str]:
    """
    Build consecutive OCR text windows for retrieval.

    Example:
    block 1
    block 1 + block 2
    block 1 + block 2 + block 3
    """

    if max_window_size < 1:
        raise ValueError(
            "max_window_size must be at least 1"
        )

    if min_length < 1:
        raise ValueError(
            "min_length must be at least 1"
        )

    cleaned_blocks = [
        block.strip()
        for block in blocks
        if isinstance(block, str)
        and block.strip()
    ]

    windows: list[str] = []

    for window_size in range(
        1,
        max_window_size + 1,
    ):
        for index in range(
            len(cleaned_blocks)
            - window_size
            + 1
        ):
            text = " ".join(
                cleaned_blocks[
                    index:index + window_size
                ]
            )

            if len(text) >= min_length:
                windows.append(text)

    return windows
