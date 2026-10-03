import pytest

from app.ingestion.chunker import chunk_text


def test_chunk_text_returns_chunks() -> None:
    text = (
        "هذه الفقرة الأولى للاختبار."
        "\n\n"
        "هذه الفقرة الثانية للاختبار."
        "\n\n"
        "هذه الفقرة الثالثة للاختبار."
    )

    chunks = chunk_text(
        text,
        max_chars=100,
    )

    assert len(chunks) >= 1
    assert all(chunk.strip() for chunk in chunks)


def test_chunk_text_rejects_small_limit() -> None:
    with pytest.raises(ValueError):
        chunk_text(
            "نص تجريبي",
            max_chars=50,
        )


def test_chunk_text_empty_input() -> None:
    assert chunk_text("") == []