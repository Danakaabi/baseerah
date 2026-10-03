import numpy as np
import pytest

from app.rag.embeddings import embed_query, embed_texts


def test_embed_query_returns_384_dimensions() -> None:
    vector = embed_query(
        "البحث عن دليل موثوق"
    )

    assert isinstance(vector, np.ndarray)
    assert vector.shape == (384,)
    assert vector.dtype == np.float32


def test_embed_texts_returns_correct_shape() -> None:
    vectors = embed_texts(
        [
            "النص الأول",
            "النص الثاني",
        ]
    )

    assert vectors.shape == (2, 384)
    assert vectors.dtype == np.float32


def test_embed_texts_rejects_empty_list() -> None:
    with pytest.raises(ValueError):
        embed_texts([])


def test_embed_query_rejects_empty_text() -> None:
    with pytest.raises(ValueError):
        embed_query("   ")
