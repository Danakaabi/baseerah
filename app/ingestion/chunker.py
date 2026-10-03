from app.ingestion.text import normalize_arabic


def chunk_original_text(
    text: str,
    max_chars: int = 700,
) -> list[str]:
    """
    Split source text while preserving its original readable form.

    Paragraph boundaries are preferred because BASEERAH needs
    surrounding context for Context Trace.
    """

    if not isinstance(text, str):
        raise TypeError("text must be a string")

    if max_chars < 100:
        raise ValueError("max_chars must be at least 100")

    text = text.strip()

    if not text:
        return []

    paragraphs = [
        paragraph.strip()
        for paragraph in text.split("\n\n")
        if paragraph.strip()
    ]

    chunks: list[str] = []
    current_parts: list[str] = []
    current_length = 0

    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            if current_parts:
                chunks.append("\n\n".join(current_parts))
                current_parts = []
                current_length = 0

            for start in range(0, len(paragraph), max_chars):
                piece = paragraph[start : start + max_chars].strip()

                if piece:
                    chunks.append(piece)

            continue

        separator_length = 2 if current_parts else 0
        added_length = len(paragraph) + separator_length

        if current_length + added_length <= max_chars:
            current_parts.append(paragraph)
            current_length += added_length

        else:
            if current_parts:
                chunks.append("\n\n".join(current_parts))

            current_parts = [paragraph]
            current_length = len(paragraph)

    if current_parts:
        chunks.append("\n\n".join(current_parts))

    return chunks


def chunk_text(
    text: str,
    max_chars: int = 700,
) -> list[str]:
    """
    Backwards-compatible normalized chunk output.

    Existing tests and callers can continue using this function.
    """

    original_chunks = chunk_original_text(
        text=text,
        max_chars=max_chars,
    )

    return [
        normalize_arabic(chunk)
        for chunk in original_chunks
    ]