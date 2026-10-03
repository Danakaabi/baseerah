import pytest

from app.models.schemas import DocumentChunk
from app.rag.vector_store import VectorStore


def make_chunk(
    index: int,
    text: str,
) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=f"test-{index:04d}",
        source_id="test-source",
        source_name="Test Source",
        source_url=None,
        document_title="Vector Search Test",
        speaker_or_author=None,
        section="Test",
        chunk_index=index,
        original_text=text,
        normalized_text=text,
    )


def test_vector_store_returns_results() -> None:
    chunks = [
        make_chunk(
            0,
            "عند غياب الدليل لا ينبغي إعطاء نتيجة مؤكدة.",
        ),
        make_chunk(
            1,
            "يجب عرض المصدر والسياق المرتبط بالنص.",
        ),
        make_chunk(
            2,
            "الطقس جميل اليوم والسماء صافية.",
        ),
    ]

    store = VectorStore()
    store.build(chunks)

    results = store.search(
        "لا يوجد دليل كاف للتحقق",
        top_k=2,
    )

    assert len(results) == 2

    assert (
        results[0].chunk.chunk_id
        == "test-0000"
    )

    assert (
        results[0].score
        >= results[1].score
    )


def test_vector_store_rejects_empty_chunks() -> None:
    store = VectorStore()

    with pytest.raises(ValueError):
        store.build([])


def test_vector_store_requires_build() -> None:
    store = VectorStore()

    with pytest.raises(RuntimeError):
        store.search("اختبار")


def test_vector_store_rejects_empty_query() -> None:
    chunks = [
        make_chunk(
            0,
            "نص تجريبي",
        )
    ]

    store = VectorStore()
    store.build(chunks)

    with pytest.raises(ValueError):
        store.search("   ")
