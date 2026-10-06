"""Locate literal quotations without inferring audio edits or missing context."""
import re

from app.ingestion.text import normalize_arabic
from app.models.schemas import QuoteExcerpt

_TOKENS = re.compile(r"[\w\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]+")


def _tokens(text: str) -> list[tuple[str, int, int]]:
    result = []
    for match in _TOKENS.finditer(text):
        # Keep original offsets, even when normalization expands a ligature.
        for token in normalize_arabic(match.group()).split():
            if token:
                result.append((token, match.start(), match.end()))
    return result


def locate_quote_excerpt(query: str, original_text: str) -> QuoteExcerpt | None:
    """Require at least four consecutive tokens and an unambiguous occurrence.

    Ignore Arabic diacritics and punctuation; never use fuzzy/semantic scores
    to claim a literal excerpt. Offsets refer only to this indexed chunk.
    """
    query_tokens = [token for token, _, _ in _tokens(query)]
    if len(query_tokens) < 4:
        return None
    source_tokens = _tokens(original_text)
    source_words = [token for token, _, _ in source_tokens]
    count = len(query_tokens)
    positions = [i for i in range(len(source_words) - count + 1)
                 if source_words[i:i + count] == query_tokens]
    if len(positions) != 1:
        return None
    position = positions[0]
    start = source_tokens[position][1]
    end = source_tokens[position + count - 1][2]
    return QuoteExcerpt(
        matched_text=original_text[start:end],
        before=original_text[:start],
        after=original_text[end:],
        start_char=start,
        end_char=end,
        is_partial_chunk=(position > 0 or position + count < len(source_tokens)),
    )
