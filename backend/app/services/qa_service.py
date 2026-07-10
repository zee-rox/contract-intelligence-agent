from collections.abc import Iterator
from uuid import UUID
import json
from typing import Any

from app.agents.qa import (
    build_grounded_answer,
    create_citations,
    has_prompt_injection_marker,
    lexical_overlap,
    validate_or_repair_response,
)
from app.config import Settings, get_settings
from app.retrieval.embeddings import HashEmbeddingService
from app.retrieval.index import DocumentFaissIndex
from app.schemas.qa import ModelQAResponse, QAResponse
from app.storage.repository import StorageRepository


class QAService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.repository = StorageRepository(settings.storage_root)
        self.index = DocumentFaissIndex(
            self.repository,
            HashEmbeddingService(settings.embedding_model, settings.embedding_dimension),
        )

    def answer_question(self, document_id: UUID, question: str) -> QAResponse:
        chunks = self.repository.load_chunks(document_id)
        results = [
            result
            for result in self.index.search(document_id, question, self.settings.retrieval_top_k)
            if result.score >= self.settings.retrieval_score_threshold
        ]
        if not results:
            return self._refuse("insufficient_evidence")
        by_id = {chunk.chunk_id: chunk for chunk in chunks}
        supported_results = [
            result
            for result in results
            if lexical_overlap(question, by_id[result.chunk_id].normalized_text) > 0
            and not has_prompt_injection_marker(by_id[result.chunk_id].normalized_text)
        ]
        if not supported_results:
            return self._refuse("insufficient_evidence")

        citations = create_citations(question, chunks, supported_results)
        if not citations:
            return self._refuse("retrieval_failed")
        fallback_answer = build_grounded_answer(question, citations)
        draft = ModelQAResponse(
            answer=fallback_answer,
            citation_ids=[citation.citation_id for citation in citations],
            confidence="medium",
        )
        return validate_or_repair_response(draft, citations, fallback_answer)

    def stream_answer(self, document_id: UUID, question: str) -> Iterator[str]:
        try:
            response = self.answer_question(document_id, question)
        except FileNotFoundError:
            error = {"code": "document_not_found", "message": "document not found"}
            yield _sse("error", error)
            return
        if response.refused:
            yield _sse("refusal", {"reason": response.refusal_reason, "answer": response.answer})
        else:
            yield _sse("answer_delta", {"text": response.answer})
            for citation in response.citations:
                yield _sse("citation", citation.model_dump(mode="json"))
        yield _sse("final", response.model_dump(mode="json"))

    def _refuse(self, reason: str) -> QAResponse:
        return QAResponse(
            answer="The document does not provide enough information to answer that question.",
            citations=[],
            confidence="low",
            refused=True,
            refusal_reason=reason,  # type: ignore[arg-type]
        )


def _sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, sort_keys=True)}\n\n"


def get_qa_service() -> QAService:
    return QAService(get_settings())
