import json
from pathlib import Path

from pydantic import ValidationError

from app.models.schemas import DocumentChunk
from app.rag.vector_store import SearchResult, VectorStore


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_CHUNKS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "chunks.json"
)


class Retriever:
    """
    Load BASEERAH processed chunks and perform semantic retrieval.
    """

    def __init__(
        self,
        chunks_file: Path = DEFAULT_CHUNKS_FILE,
    ) -> None:
        self.chunks_file = chunks_file
        self.chunks: list[DocumentChunk] = []
        self.vector_store = VectorStore()

    def load(self) -> None:
        """
        Load validated chunks and build the in-memory FAISS index.
        """

        if not self.chunks_file.exists():
            raise FileNotFoundError(
                f"Chunks file not found: {self.chunks_file}"
            )

        try:
            with self.chunks_file.open(
                "r",
                encoding="utf-8",
            ) as file:
                raw_chunks = json.load(file)

        except json.JSONDecodeError as exc:
            raise ValueError(
                "Invalid chunks JSON file"
            ) from exc

        if not isinstance(raw_chunks, list):
            raise ValueError(
                "chunks JSON must contain a list"
            )

        try:
            self.chunks = [
                DocumentChunk.model_validate(item)
                for item in raw_chunks
            ]

        except ValidationError as exc:
            raise ValueError(
                "Invalid chunk data"
            ) from exc

        if not self.chunks:
            raise ValueError(
                "chunks file contains no chunks"
            )

        self.vector_store.build(
            self.chunks
        )

    def search(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[SearchResult]:
        """
        Retrieve the most semantically similar evidence chunks.
        """

        if not self.chunks:
            raise RuntimeError(
                "retriever has not been loaded"
            )

        return self.vector_store.search(
            query=query,
            top_k=top_k,
        )
