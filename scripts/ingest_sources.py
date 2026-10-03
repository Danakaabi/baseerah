import json
from pathlib import Path

from pydantic import ValidationError

from app.ingestion.chunker import chunk_original_text
from app.ingestion.text import normalize_arabic
from app.models.schemas import DocumentChunk, SourceDocument


PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

OUTPUT_FILE = PROCESSED_DIR / "chunks.json"


def load_source(path: Path) -> SourceDocument:
    """Load and validate one trusted source file."""

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return SourceDocument.model_validate(data)


def build_chunks(document: SourceDocument) -> list[DocumentChunk]:
    """Convert a validated document into ordered traceable chunks."""

    original_chunks = chunk_original_text(document.text)

    chunks: list[DocumentChunk] = []

    for index, original_text in enumerate(original_chunks):
        normalized_text = normalize_arabic(original_text)

        chunk = DocumentChunk(
            chunk_id=f"{document.source_id}-{index:04d}",
            source_id=document.source_id,
            source_name=document.source_name,
            source_url=(
                str(document.source_url)
                if document.source_url
                else None
            ),
            document_title=document.document_title,
            speaker_or_author=document.speaker_or_author,
            section=document.section,
            chunk_index=index,
            original_text=original_text,
            normalized_text=normalized_text,
        )

        chunks.append(chunk)

    return chunks


def ingest_all_sources() -> list[DocumentChunk]:
    """Ingest all JSON documents from the raw directory."""

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    source_files = sorted(RAW_DIR.glob("*.json"))

    if not source_files:
        raise RuntimeError(
            f"No source files found in {RAW_DIR}"
        )

    all_chunks: list[DocumentChunk] = []

    for source_file in source_files:
        try:
            document = load_source(source_file)
            chunks = build_chunks(document)

            all_chunks.extend(chunks)

            print(
                f"[OK] {source_file.name}: "
                f"{len(chunks)} chunks"
            )

        except (
            json.JSONDecodeError,
            ValidationError,
        ) as exc:
            print(
                f"[ERROR] Failed to process "
                f"{source_file.name}: {exc}"
            )
            raise

    serialized = [
        chunk.model_dump()
        for chunk in all_chunks
    ]

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            serialized,
            file,
            ensure_ascii=False,
            indent=2,
        )

    return all_chunks


if __name__ == "__main__":
    chunks = ingest_all_sources()

    print()
    print(f"Total chunks: {len(chunks)}")
    print(f"Output: {OUTPUT_FILE}")
