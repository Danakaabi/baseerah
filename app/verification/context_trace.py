from app.models.schemas import ContextTrace, DocumentChunk


def get_context_trace(
    chunks: list[DocumentChunk],
    matched_chunk_id: str,
) -> ContextTrace:
    """
    Return the previous, matched, and next chunks
    belonging to the same source document.
    """

    if not chunks:
        raise ValueError("chunks cannot be empty")

    matched_chunk = next(
        (
            chunk
            for chunk in chunks
            if chunk.chunk_id == matched_chunk_id
        ),
        None,
    )

    if matched_chunk is None:
        raise ValueError(
            f"Chunk not found: {matched_chunk_id}"
        )

    document_chunks = sorted(
        (
            chunk
            for chunk in chunks
            if chunk.source_id == matched_chunk.source_id
        ),
        key=lambda chunk: chunk.chunk_index,
    )

    current_position = next(
        index
        for index, chunk in enumerate(document_chunks)
        if chunk.chunk_id == matched_chunk_id
    )

    previous_chunk = (
        document_chunks[current_position - 1]
        if current_position > 0
        else None
    )

    next_chunk = (
        document_chunks[current_position + 1]
        if current_position + 1 < len(document_chunks)
        else None
    )

    return ContextTrace(
        previous=previous_chunk,
        current=matched_chunk,
        next=next_chunk,
    )