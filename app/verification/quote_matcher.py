from dataclasses import dataclass
from difflib import SequenceMatcher

from app.ingestion.text import normalize_arabic
from app.models.schemas import DocumentChunk


MIN_QUOTE_SCORE = 0.40
MIN_QUOTE_MARGIN = 0.15


@dataclass(frozen=True)
class QuoteMatch:
    """Lexical match for quoted OCR/ASR content."""

    chunk: DocumentChunk
    score: float
    margin: float


def find_quote_match(
    candidates: list[str],
    chunks: list[DocumentChunk],
) -> QuoteMatch | None:
    """
    Find a strong lexical quotation match.

    Intended for OCR/ASR candidate text, not general
    semantic questions.
    """

    if not candidates or not chunks:
        return None

    matches: list[tuple[float, DocumentChunk]] = []

    for candidate in candidates:
        if not isinstance(candidate, str):
            continue

        query = normalize_arabic(candidate)

        if not query:
            continue

        for chunk in chunks:
            source = normalize_arabic(
                chunk.original_text
            )

            score = SequenceMatcher(
                None,
                query,
                source,
            ).ratio()

            matches.append(
                (score, chunk)
            )

    if not matches:
        return None

    matches.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    best_score, best_chunk = matches[0]

    second_score = (
        matches[1][0]
        if len(matches) > 1
        else 0.0
    )

    margin = max(
        0.0,
        best_score - second_score,
    )

    if best_score < MIN_QUOTE_SCORE:
        return None

    if margin < MIN_QUOTE_MARGIN:
        return None

    return QuoteMatch(
        chunk=best_chunk,
        score=best_score,
        margin=margin,
    )
