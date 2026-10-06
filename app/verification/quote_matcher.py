from dataclasses import dataclass
from difflib import SequenceMatcher

from app.ingestion.text import normalize_arabic
from app.models.schemas import DocumentChunk
from app.verification.quote_excerpt import locate_quote_excerpt


MIN_QUOTE_SCORE = 0.70
MIN_QUOTE_MARGIN = 0.15


@dataclass(frozen=True)
class QuoteMatch:
    """Lexical match for quoted OCR/ASR content."""

    chunk: DocumentChunk
    score: float
    margin: float
    query: str


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

    # Compare distinct chunks, not duplicate candidates from the same input.
    matches_by_chunk: dict[str, tuple[float, DocumentChunk, str]] = {}

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
            if locate_quote_excerpt(candidate, chunk.original_text) is not None:
                score = 1.0
            existing = matches_by_chunk.get(chunk.chunk_id)
            if existing is None or score > existing[0]:
                matches_by_chunk[chunk.chunk_id] = (score, chunk, candidate)

    matches = list(matches_by_chunk.values())
    if not matches:
        return None

    matches.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    best_score, best_chunk, best_query = matches[0]

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
        query=best_query,
    )
