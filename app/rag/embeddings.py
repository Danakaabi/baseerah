from functools import lru_cache

import numpy as np


from app.ingestion.text import normalize_arabic


MODEL_NAME = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)


@lru_cache(maxsize=1)
def get_embedding_model():
    """
    Load the embedding model once and reuse it.

    Caching is important because loading the model repeatedly
    would make BASEERAH unnecessarily slow.
    """

    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODEL_NAME)


def embed_texts(texts: list[str]) -> np.ndarray:
    """
    Convert Arabic texts into normalized embedding vectors.
    """

    if not texts:
        raise ValueError("texts cannot be empty")

    normalized_texts: list[str] = []

    for text in texts:
        if not isinstance(text, str):
            raise TypeError("all texts must be strings")

        normalized = normalize_arabic(text)

        if not normalized:
            raise ValueError("texts cannot contain empty values")

        normalized_texts.append(normalized)

    model = get_embedding_model()

    embeddings = model.encode(
        normalized_texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )

    return np.asarray(
        embeddings,
        dtype=np.float32,
    )


def embed_query(query: str) -> np.ndarray:
    """
    Convert one user query into a normalized embedding vector.
    """

    embeddings = embed_texts([query])

    return embeddings[0]
