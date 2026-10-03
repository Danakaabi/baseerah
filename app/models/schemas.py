from pydantic import BaseModel, Field, HttpUrl


class SourceDocument(BaseModel):
    """A trusted source document before chunking."""

    source_id: str = Field(min_length=1, max_length=100)
    source_name: str = Field(min_length=1, max_length=200)
    source_url: HttpUrl | None = None

    document_title: str = Field(min_length=1, max_length=300)
    speaker_or_author: str | None = Field(default=None, max_length=200)
    section: str | None = Field(default=None, max_length=200)

    text: str = Field(min_length=1)


class DocumentChunk(BaseModel):
    """An ordered, traceable chunk from a trusted source."""

    chunk_id: str

    source_id: str
    source_name: str
    source_url: str | None

    document_title: str
    speaker_or_author: str | None
    section: str | None

    chunk_index: int = Field(ge=0)

    # Exact/readable source content shown to the user.
    original_text: str = Field(min_length=1)

    # Normalized representation used later for retrieval.
    normalized_text: str = Field(min_length=1)


class ContextTrace(BaseModel):
    """Context surrounding a matched chunk."""

    previous: DocumentChunk | None
    current: DocumentChunk
    next: DocumentChunk | None

class EvidenceScore(BaseModel):
    """Technical retrieval evidence scores."""

    final_score: float
    title_score: float
    content_score: float
    margin: float


class VerificationResult(BaseModel):
    """Explainable BASEERAH verification result."""

    query: str
    status: str
    message: str
    evidence_score: EvidenceScore | None = None
    source: DocumentChunk | None = None
    context_trace: ContextTrace | None = None


class VerifyTextRequest(BaseModel):
    """Text submitted to BASEERAH for verification."""

    text: str = Field(min_length=1, max_length=5000)
