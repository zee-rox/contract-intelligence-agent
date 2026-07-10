import re

from app.schemas.chunks import CandidateChunk
from app.schemas.qa import Citation, ModelQAResponse, QAResponse
from app.schemas.retrieval import RetrievalResult

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "does",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "what",
    "when",
    "who",
    "with",
}

PROMPT_INJECTION_MARKERS = (
    "ignore previous instructions",
    "ignore all previous instructions",
    "system prompt",
    "developer message",
    "you are chatgpt",
)


def question_terms(question: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", question.lower()) if token not in STOPWORDS and len(token) > 2}


def lexical_overlap(question: str, text: str) -> int:
    return len(question_terms(question) & set(re.findall(r"[a-z0-9]+", text.lower())))


def has_prompt_injection_marker(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in PROMPT_INJECTION_MARKERS)


def create_citations(question: str, chunks: list[CandidateChunk], results: list[RetrievalResult]) -> list[Citation]:
    by_id = {chunk.chunk_id: chunk for chunk in chunks}
    citations: list[Citation] = []
    for result in results:
        chunk = by_id[result.chunk_id]
        snippet = choose_snippet(question, chunk.normalized_text)
        if not snippet or snippet not in chunk.normalized_text:
            continue
        citations.append(
            Citation(
                citation_id=f"cit_{len(citations):04d}",
                chunk_id=chunk.chunk_id,
                source_locator=chunk.source_locators[0],
                quoted_snippet=snippet,
            )
        )
    return citations


def choose_snippet(question: str, text: str) -> str:
    terms = question_terms(question)
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", text) if part.strip()]
    best = max(sentences or [text.strip()], key=lambda sentence: len(terms & set(re.findall(r"[a-z0-9]+", sentence.lower()))))
    return best[:280].strip()


def build_grounded_answer(question: str, citations: list[Citation]) -> str:
    if not citations:
        return "The document does not provide enough information to answer that question."
    citation_refs = ", ".join(f"[{citation.citation_id}]" for citation in citations)
    return f"Based on the cited contract text, {summarize_evidence(question, citations)} {citation_refs}"


def summarize_evidence(question: str, citations: list[Citation]) -> str:
    snippet = citations[0].quoted_snippet.rstrip(".")
    lowered_question = question.lower()
    if "terminate" in lowered_question or "termination" in lowered_question:
        return f"the termination provision states: {snippet}."
    if "payment" in lowered_question or "invoice" in lowered_question:
        return f"the payment provision states: {snippet}."
    if "confidential" in lowered_question:
        return f"the confidentiality provision states: {snippet}."
    return f"the contract states: {snippet}."


def validate_or_repair_response(
    draft: ModelQAResponse,
    allowed_citations: list[Citation],
    fallback_answer: str,
) -> QAResponse:
    allowed = {citation.citation_id: citation for citation in allowed_citations}
    valid_citations = [allowed[citation_id] for citation_id in draft.citation_ids if citation_id in allowed]
    if valid_citations:
        return QAResponse(
            answer=draft.answer,
            citations=valid_citations,
            confidence=draft.confidence,
            refused=False,
        )
    if allowed_citations:
        return QAResponse(
            answer=fallback_answer,
            citations=allowed_citations[:1],
            confidence="medium",
            refused=False,
        )
    return QAResponse(
        answer="The document does not provide enough information to answer that question.",
        citations=[],
        confidence="low",
        refused=True,
        refusal_reason="invalid_citations",
    )
