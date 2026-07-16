from collections.abc import Iterator
import logging
from uuid import UUID
import json
from typing import Any

from app.agents.qa import (
    build_grounded_answer,
    create_citations,
    has_prompt_injection_marker,
    parse_model_qa_response,
    validate_or_repair_response,
)
from app.config import Settings, get_settings
from app.llm.factory import build_llm_provider
from app.llm.interface import LLMMessage
from app.retrieval.embeddings import HashEmbeddingService
from app.retrieval.bm25 import rank_chunks
from app.retrieval.index import DocumentFaissIndex
from app.schemas.qa import Citation, ModelQAResponse, QAResponse
from app.schemas.retrieval import RetrievalResult
from app.storage.repository import StorageRepository

logger = logging.getLogger(__name__)


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
        semantic_results = [
            result
            for result in self.index.search(document_id, question, self.settings.retrieval_top_k)
            if result.score >= self.settings.retrieval_score_threshold
        ]
        lexical_results = rank_chunks(question, chunks, self.settings.retrieval_top_k)
        results = _merge_retrieval_results(semantic_results, lexical_results)
        if not results:
            return self._refuse("insufficient_evidence")
        by_id = {chunk.chunk_id: chunk for chunk in chunks}
        results.sort(key=lambda result: result.score, reverse=True)
        supported_results = [result for result in results if not has_prompt_injection_marker(by_id[result.chunk_id].normalized_text)]
        if not supported_results:
            return self._refuse("insufficient_evidence")

        citations = create_citations(question, chunks, supported_results)
        if not citations:
            return self._refuse("retrieval_failed")
        fallback_answer = build_grounded_answer(question, citations)
        draft = self._generate_answer(question, citations, fallback_answer)
        return validate_or_repair_response(draft, citations, fallback_answer)

    def _generate_answer(self, question: str, citations: list[Citation], fallback_answer: str) -> ModelQAResponse:
        provider = build_llm_provider(self.settings)
        evidence = "\n\n".join(
            f"[{citation.citation_id}] {citation.quoted_snippet}" for citation in citations
        )
        prompt = (
            "You are a careful contract analyst. Answer the user's question using only the provided contract excerpts. "
            "Write a direct, useful answer with context: explain the rule, conditions, exceptions, and practical effect "
            "when the excerpts support them. Do not merely say that a clause mentions something. Do not invent facts. "
            "Return only valid JSON with exactly these keys: answer (string), citation_ids (array of supplied IDs), "
            "confidence (high, medium, or low). Do not put citation markers in the answer text.\n\n"
            f"User question: {question}\n\nContract excerpts:\n{evidence}"
        )
        try:
            response = provider.generate(
                [
                    LLMMessage(role="system", content="Answer grounded contract questions as concise JSON."),
                    LLMMessage(role="user", content=prompt),
                ],
                temperature=0.1,
            )
            draft = parse_model_qa_response(response.content)
            if not draft.answer.strip():
                raise ValueError("provider returned an empty answer")
            return draft
        except Exception as exc:
            logger.warning("qa provider answer failed provider=%s error=%s; using grounded fallback", provider.provider_name, exc)
            return ModelQAResponse(
                answer=fallback_answer,
                citation_ids=[citation.citation_id for citation in citations],
                confidence="medium",
            )

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
            words = response.answer.split(" ")
            for index, word in enumerate(words):
                yield _sse("answer_delta", {"text": f"{word}{' ' if index < len(words) - 1 else ''}"})
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


def _merge_retrieval_results(
    semantic_results: list[RetrievalResult],
    lexical_results: list[tuple[str, float]],
) -> list[RetrievalResult]:
    scores: dict[str, float] = {}
    for result in semantic_results:
        scores[result.chunk_id] = max(scores.get(result.chunk_id, 0.0), max(0.0, result.score) * 0.7)
    lexical_max = max((score for _, score in lexical_results), default=0.0)
    for chunk_id, score in lexical_results:
        normalized = score / lexical_max if lexical_max else 0.0
        scores[chunk_id] = max(scores.get(chunk_id, 0.0), normalized * 0.3)
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return [
        RetrievalResult(chunk_id=chunk_id, score=score, rank=rank)
        for rank, (chunk_id, score) in enumerate(ranked, start=1)
        if score > 0
    ]


def get_qa_service() -> QAService:
    return QAService(get_settings())
    parse_model_qa_response,
