from dataclasses import dataclass

from app.rag.vector_store import SearchResult


MIN_FINAL_SCORE = 0.30
MIN_MARGIN = 0.05


@dataclass(frozen=True)
class ConfidenceDecision:
    """Technical decision about retrieved evidence."""

    sufficient: bool
    final_score: float
    title_score: float
    content_score: float
    margin: float
    reason: str


def evaluate_evidence(
    results: list[SearchResult],
) -> ConfidenceDecision:
    """
    Evaluate whether retrieval evidence is strong enough.

    This is a technical retrieval confidence gate.
    It is not a religious correctness score.
    """

    if not results:
        return ConfidenceDecision(
            sufficient=False,
            final_score=0.0,
            title_score=0.0,
            content_score=0.0,
            margin=0.0,
            reason="no_results",
        )

    best = results[0]

    second_score = (
        results[1].score
        if len(results) > 1
        else 0.0
    )

    margin = max(
        0.0,
        best.score - second_score,
    )

    if best.score < MIN_FINAL_SCORE:
        return ConfidenceDecision(
            sufficient=False,
            final_score=best.score,
            title_score=best.title_score,
            content_score=best.content_score,
            margin=margin,
            reason="low_score",
        )

    if (
        len(results) > 1
        and margin < MIN_MARGIN
    ):
        return ConfidenceDecision(
            sufficient=False,
            final_score=best.score,
            title_score=best.title_score,
            content_score=best.content_score,
            margin=margin,
            reason="ambiguous_results",
        )

    return ConfidenceDecision(
        sufficient=True,
        final_score=best.score,
        title_score=best.title_score,
        content_score=best.content_score,
        margin=margin,
        reason="sufficient_evidence",
    )
