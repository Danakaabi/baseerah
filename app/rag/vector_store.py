from __future__ import annotations
from dataclasses import dataclass


import numpy as np

from app.models.schemas import DocumentChunk
from app.rag.embeddings import embed_query, embed_texts


TITLE_WEIGHT = 0.6
CONTENT_WEIGHT = 0.4


@dataclass
class SearchResult:
    """One hybrid semantic-search result."""

    chunk: DocumentChunk
    score: float
    title_score: float
    content_score: float


class VectorStore:
    """
    Hybrid in-memory FAISS vector store for BASEERAH.

    Title and content are embedded separately.
    The final retrieval score combines both similarities.
    """

    def __init__(self) -> None:
        self.title_index: faiss.Index | None = None
        self.content_index: faiss.Index | None = None
        self.chunks: list[DocumentChunk] = []
        self.dimension: int | None = None

    def build(
        self,
        chunks: list[DocumentChunk],
    ) -> None:
        if not chunks:
            raise ValueError("chunks cannot be empty")

        import faiss

        title_embeddings = embed_texts(
            [
                chunk.document_title
                for chunk in chunks
            ]
        )

        content_embeddings = embed_texts(
            [
                chunk.normalized_text
                for chunk in chunks
            ]
        )

        if (
            title_embeddings.ndim != 2
            or content_embeddings.ndim != 2
        ):
            raise ValueError(
                "embeddings must be 2D arrays"
            )

        if (
            title_embeddings.shape
            != content_embeddings.shape
        ):
            raise ValueError(
                "title and content embeddings "
                "must have matching shapes"
            )

        self.dimension = title_embeddings.shape[1]

        self.title_index = faiss.IndexFlatIP(
            self.dimension
        )
        self.content_index = faiss.IndexFlatIP(
            self.dimension
        )

        self.title_index.add(
            np.ascontiguousarray(
                title_embeddings,
                dtype=np.float32,
            )
        )

        self.content_index.add(
            np.ascontiguousarray(
                content_embeddings,
                dtype=np.float32,
            )
        )

        self.chunks = list(chunks)

    def search(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[SearchResult]:
        if (
            self.title_index is None
            or self.content_index is None
        ):
            raise RuntimeError(
                "vector store has not been built"
            )

        if not query.strip():
            raise ValueError(
                "query cannot be empty"
            )

        if top_k < 1:
            raise ValueError(
                "top_k must be at least 1"
            )

        query_vector = embed_query(query)

        query_matrix = np.ascontiguousarray(
            query_vector.reshape(1, -1),
            dtype=np.float32,
        )

        # Search every demo chunk so title and content
        # scores can be combined for the same chunk.
        result_count = len(self.chunks)

        title_scores, title_indices = (
            self.title_index.search(
                query_matrix,
                result_count,
            )
        )

        content_scores, content_indices = (
            self.content_index.search(
                query_matrix,
                result_count,
            )
        )

        title_by_index = {
            int(index): float(score)
            for score, index in zip(
                title_scores[0],
                title_indices[0],
            )
            if index >= 0
        }

        content_by_index = {
            int(index): float(score)
            for score, index in zip(
                content_scores[0],
                content_indices[0],
            )
            if index >= 0
        }

        results: list[SearchResult] = []

        for index, chunk in enumerate(self.chunks):
            title_score = title_by_index[index]
            content_score = content_by_index[index]

            final_score = (
                TITLE_WEIGHT * title_score
                + CONTENT_WEIGHT * content_score
            )

            results.append(
                SearchResult(
                    chunk=chunk,
                    score=final_score,
                    title_score=title_score,
                    content_score=content_score,
                )
            )

        results.sort(
            key=lambda result: result.score,
            reverse=True,
        )

        return results[: min(top_k, len(results))]
