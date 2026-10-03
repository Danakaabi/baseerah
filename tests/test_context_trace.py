from app.models.schemas import DocumentChunk
from app.verification.context_trace import get_context_trace


def make_chunk(
    index: int,
    text: str,
) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=f"test-source-{index:04d}",
        source_id="test-source",
        source_name="Test Source",
        source_url=None,
        document_title="Context Trace Test",
        speaker_or_author="Test Author",
        section="Test",
        chunk_index=index,
        original_text=text,
        normalized_text=text,
    )


def test_context_trace_middle_chunk() -> None:
    chunks = [
        make_chunk(0, "السياق السابق"),
        make_chunk(1, "النص المطابق"),
        make_chunk(2, "السياق اللاحق"),
    ]

    result = get_context_trace(
        chunks,
        "test-source-0001",
    )

    assert result.previous is not None
    assert result.previous.original_text == "السياق السابق"

    assert result.current.original_text == "النص المطابق"

    assert result.next is not None
    assert result.next.original_text == "السياق اللاحق"


def test_context_trace_first_chunk() -> None:
    chunks = [
        make_chunk(0, "النص الأول"),
        make_chunk(1, "النص الثاني"),
    ]

    result = get_context_trace(
        chunks,
        "test-source-0000",
    )

    assert result.previous is None
    assert result.next is not None


def test_context_trace_last_chunk() -> None:
    chunks = [
        make_chunk(0, "النص الأول"),
        make_chunk(1, "النص الثاني"),
    ]

    result = get_context_trace(
        chunks,
        "test-source-0001",
    )

    assert result.previous is not None
    assert result.next is None