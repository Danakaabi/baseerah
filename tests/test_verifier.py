import pytest

from app.verification.verifier import (
    INSUFFICIENT_EVIDENCE_MESSAGE,
    Verifier,
)


@pytest.fixture(scope="module")
def verifier() -> Verifier:
    return Verifier()


def test_verifier_finds_supported_evidence(
    verifier: Verifier,
) -> None:
    result = verifier.verify(
        "هل ينظر الله إلى صور الناس وأجسامهم "
        "أم إلى قلوبهم وأعمالهم؟"
    )

    assert result.status == "evidence_found"
    assert result.source is not None
    assert result.context_trace is not None

    assert (
        result.source.source_id
        == "hadeethenc-4555"
    )

    assert result.evidence_score is not None
    assert result.evidence_score.final_score >= 0.30


def test_verifier_abstains_without_evidence(
    verifier: Verifier,
) -> None:
    result = verifier.verify(
        "ما حكم زكاة الذهب المعد للاستعمال؟"
    )

    assert result.status == "insufficient_evidence"
    assert result.message == INSUFFICIENT_EVIDENCE_MESSAGE

    assert result.source is None
    assert result.context_trace is None


def test_verifier_rejects_empty_query(
    verifier: Verifier,
) -> None:
    with pytest.raises(
        ValueError,
        match="query cannot be empty",
    ):
        verifier.verify("   ")
