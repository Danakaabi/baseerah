import json

import pytest

from app.rag.retriever import Retriever


def test_retriever_loads_and_searches(
    tmp_path,
) -> None:
    chunks = [
        {
            "chunk_id": "demo-0000",
            "source_id": "demo",
            "source_name": "Demo Source",
            "source_url": None,
            "document_title": "Demo Document",
            "speaker_or_author": None,
            "section": "Demo",
            "chunk_index": 0,
            "original_text": (
                "إذا لم تتوفر أدلة كافية "
                "يجب توضيح ذلك للمستخدم."
            ),
            "normalized_text": (
                "اذا لم تتوفر ادلة كافية "
                "يجب توضيح ذلك للمستخدم."
            ),
        },
        {
            "chunk_id": "demo-0001",
            "source_id": "demo",
            "source_name": "Demo Source",
            "source_url": None,
            "document_title": "Demo Document",
            "speaker_or_author": None,
            "section": "Demo",
            "chunk_index": 1,
            "original_text": (
                "يجب عرض المصدر الأصلي "
                "والسياق المرتبط بالنص."
            ),
            "normalized_text": (
                "يجب عرض المصدر الاصلي "
                "والسياق المرتبط بالنص."
            ),
        },
        {
            "chunk_id": "demo-0002",
            "source_id": "demo",
            "source_name": "Demo Source",
            "source_url": None,
            "document_title": "Demo Document",
            "speaker_or_author": None,
            "section": "Demo",
            "chunk_index": 2,
            "original_text": (
                "الطقس جميل اليوم."
            ),
            "normalized_text": (
                "الطقس جميل اليوم."
            ),
        },
    ]

    chunks_file = tmp_path / "chunks.json"

    chunks_file.write_text(
        json.dumps(
            chunks,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    retriever = Retriever(
        chunks_file=chunks_file
    )

    retriever.load()

    results = retriever.search(
        "لا يوجد دليل كاف",
        top_k=2,
    )

    assert len(results) == 2

    assert (
        results[0].chunk.chunk_id
        == "demo-0000"
    )


def test_retriever_requires_load(
    tmp_path,
) -> None:
    retriever = Retriever(
        chunks_file=tmp_path / "chunks.json"
    )

    with pytest.raises(RuntimeError):
        retriever.search(
            "اختبار"
        )


def test_retriever_missing_file(
    tmp_path,
) -> None:
    retriever = Retriever(
        chunks_file=tmp_path / "missing.json"
    )

    with pytest.raises(FileNotFoundError):
        retriever.load()
