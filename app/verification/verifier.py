from app.models.schemas import (
    EvidenceScore,
    VerificationResult,
)
from app.rag.retriever import Retriever
from app.verification.confidence import evaluate_evidence
from app.verification.context_trace import get_context_trace
from app.verification.quote_matcher import find_quote_match


INSUFFICIENT_EVIDENCE_MESSAGE = (
    "لم يتم العثور على دليل كافٍ للتحقق من هذا المحتوى."
)

SUPPORTED_EVIDENCE_MESSAGE = (
    "تم العثور على دليل ذي صلة في مصدر معتمد."
)


class Verifier:
    """BASEERAH explainable verification engine."""

    def __init__(self) -> None:
        self.retriever = Retriever()
        self.retriever.load()

    def verify(
        self,
        query: str,
    ) -> VerificationResult:
        if not query.strip():
            raise ValueError("query cannot be empty")

        results = self.retriever.search(
            query=query,
            top_k=3,
        )

        return self._build_result(
            query=query,
            results=results,
        )

    def verify_candidates(
        self,
        candidates: list[str],
    ) -> VerificationResult:
        """
        Verify multiple candidate texts.

        Intended for OCR and similar inputs where one source
        produces several possible retrieval queries.
        """

        cleaned_candidates = [
            candidate.strip()
            for candidate in candidates
            if isinstance(candidate, str)
            and candidate.strip()
        ]

        if not cleaned_candidates:
            raise ValueError(
                "candidates cannot be empty"
            )

        best_query: str | None = None
        best_results = None
        best_score = float("-inf")

        for candidate in cleaned_candidates:
            results = self.retriever.search(
                query=candidate,
                top_k=3,
            )

            if (
                results
                and results[0].score > best_score
            ):
                best_query = candidate
                best_results = results
                best_score = results[0].score

        if best_query is None or best_results is None:
            return VerificationResult(
                query="",
                status="insufficient_evidence",
                message=INSUFFICIENT_EVIDENCE_MESSAGE,
                evidence_score=None,
                source=None,
                context_trace=None,
            )

        return self._build_result(
            query=best_query,
            results=best_results,
        )

    def verify_quote_candidates(
        self,
        candidates: list[str],
    ) -> VerificationResult:
        """
        Verify OCR/ASR candidates using strong lexical
        quotation matching before semantic fallback.
        """

        cleaned_candidates = [
            candidate.strip()
            for candidate in candidates
            if isinstance(candidate, str)
            and candidate.strip()
        ]

        if not cleaned_candidates:
            raise ValueError(
                "candidates cannot be empty"
            )

        quote_match = find_quote_match(
            candidates=cleaned_candidates,
            chunks=self.retriever.chunks,
        )

        if quote_match is not None:
            context_trace = get_context_trace(
                chunks=self.retriever.chunks,
                matched_chunk_id=quote_match.chunk.chunk_id,
            )

            evidence_score = EvidenceScore(
                final_score=quote_match.score,
                title_score=0.0,
                content_score=quote_match.score,
                margin=quote_match.margin,
            )

            return VerificationResult(
                query=cleaned_candidates[0],
                status="evidence_found",
                message=SUPPORTED_EVIDENCE_MESSAGE,
                evidence_score=evidence_score,
                source=quote_match.chunk,
                context_trace=context_trace,
            )

        result = self.verify_candidates(
            cleaned_candidates
        )

        # ASR/OCR input is noisy, so semantic retrieval
        # must meet a stricter evidence gate.
        if (
            result.status == "evidence_found"
            and result.evidence_score is not None
            and (
                result.evidence_score.final_score < 0.72
                or result.evidence_score.margin < 0.08
            )
        ):
            return VerificationResult(
                query=result.query,
                status="insufficient_evidence",
                message=INSUFFICIENT_EVIDENCE_MESSAGE,
                evidence_score=result.evidence_score,
                source=None,
                context_trace=None,
            )

        return result

    def _build_result(
        self,
        query: str,
        results,
    ) -> VerificationResult:
        """
        Build a verification result using the shared
        confidence and context-trace pipeline.
        """

        decision = evaluate_evidence(results)

        evidence_score = EvidenceScore(
            final_score=decision.final_score,
            title_score=decision.title_score,
            content_score=decision.content_score,
            margin=decision.margin,
        )

        if not decision.sufficient:
            return VerificationResult(
                query=query,
                status="insufficient_evidence",
                message=INSUFFICIENT_EVIDENCE_MESSAGE,
                evidence_score=evidence_score,
                source=None,
                context_trace=None,
            )

        best = results[0]

        context_trace = get_context_trace(
            chunks=self.retriever.chunks,
            matched_chunk_id=best.chunk.chunk_id,
        )

        return VerificationResult(
            query=query,
            status="evidence_found",
            message=SUPPORTED_EVIDENCE_MESSAGE,
            evidence_score=evidence_score,
            source=best.chunk,
            context_trace=context_trace,
        )
