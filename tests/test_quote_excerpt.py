from types import SimpleNamespace

from app.models.schemas import DocumentChunk
from app.verification.quote_excerpt import locate_quote_excerpt
from app.verification.quote_matcher import find_quote_match
from app.verification.verifier import Verifier


def chunk(text, identity="source"):
    return DocumentChunk(chunk_id=identity + "-0", source_id=identity,
                         source_name="مصدر اختبار", source_url=None,
                         document_title="وثيقة اختبار", speaker_or_author=None,
                         section=None, chunk_index=0, original_text=text,
                         normalized_text=text)


def test_excerpt_preserves_original_context_and_offsets():
    source = "المقدمة. إِنَّمَا الأعمالُ بالنِّياتِ ولكلِّ امرئٍ ما نوى. الشرح اللاحق."
    result = locate_quote_excerpt("انما الاعمال بالنيات ولكل امرئ ما نوى", source)
    assert result is not None
    assert result.before == "المقدمة. "
    assert result.after == ". الشرح اللاحق."
    assert source[result.start_char:result.end_char] == result.matched_text
    assert result.is_partial_chunk
    assert not result.audio_origin_verified


def test_paraphrase_short_and_repeated_quotes_do_not_claim_excerpt():
    assert locate_quote_excerpt("الاعمال بالنيات", "الاعمال بالنيات") is None
    assert locate_quote_excerpt("هذا النص يتحدث عن النية", "الاعمال تتوقف على النيات") is None
    quote = "هذه عبارة اختبار طويلة"
    assert locate_quote_excerpt(quote, quote + ". " + quote) is None


def test_full_chunk_is_not_marked_partial():
    result = locate_quote_excerpt("هذه عبارة اختبار طويلة", "هذه عبارة اختبار طويلة.")
    assert result is not None and not result.is_partial_chunk


def test_match_keeps_actual_candidate_and_deduplicates_same_chunk():
    quote = "هذه عبارة اختبار طويلة"
    source = chunk("السياق السابق. " + quote + ". السياق اللاحق.")
    result = find_quote_match(["نص غير مطابق", quote, quote], [source])
    assert result is not None and result.query == quote
    assert result.score == 1.0


def test_ambiguous_sources_do_not_claim_unique_source():
    quote = "هذه عبارة اختبار طويلة"
    assert find_quote_match([quote], [chunk(quote, "a"), chunk(quote, "b")]) is None


def test_verifier_returns_excerpt_without_semantic_model():
    # Real verification integration; no expensive models needed for exact match.
    verifier = Verifier.__new__(Verifier)
    verifier.retriever = SimpleNamespace(chunks=[chunk(
        "قبل الكلام. هذه عبارة اختبار طويلة. بعد الكلام."
    )])
    result = verifier.verify("هذه عبارة اختبار طويلة")
    assert result.status == "evidence_found"
    assert result.quote_excerpt.before == "قبل الكلام. "
    assert result.quote_excerpt.after == ". بعد الكلام."
    assert not result.quote_excerpt.audio_origin_verified


def test_text_api_serializes_source_excerpt(monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    import app.api.verify as verify_api

    verifier = Verifier.__new__(Verifier)
    verifier.retriever = SimpleNamespace(chunks=[chunk(
        "قبل الكلام. هذه عبارة اختبار طويلة. بعد الكلام."
    )])
    monkeypatch.setattr(verify_api, "get_verifier", lambda: verifier)
    with TestClient(app) as client:
        response = client.post("/verify/text", json={"text": "هذه عبارة اختبار طويلة"})
    assert response.status_code == 200
    assert response.json()["quote_excerpt"]["matched_text"] == "هذه عبارة اختبار طويلة"
    assert response.json()["quote_excerpt"]["audio_origin_verified"] is False
