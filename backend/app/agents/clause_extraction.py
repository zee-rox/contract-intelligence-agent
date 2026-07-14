import json
import logging
from uuid import UUID

from app.config import Settings
from app.llm.factory import build_llm_provider
from app.llm.interface import LLMMessage
from app.llm.structured_output import parse_clause_json
from app.schemas.chunks import CandidateChunk
from app.schemas.clauses import ClauseExtractionResult, ClauseType, ExtractedClause

logger = logging.getLogger(__name__)

KEYWORDS: list[tuple[str, ClauseType]] = [
    ("termination", "termination"),
    ("liability", "liability"),
    ("indemnification", "indemnification"),
    ("payment", "payment_terms"),
    ("confidentiality", "confidentiality"),
    ("governing law", "governing_law"),
    ("force majeure", "force_majeure"),
]


def _heuristic_extract(document_id: UUID, chunks: list[CandidateChunk]) -> list[ExtractedClause]:
    clauses: list[ExtractedClause] = []
    for chunk in chunks:
        text = chunk.normalized_text
        lowered = text.lower()
        clause_type: ClauseType | None = None
        for keyword, candidate_type in KEYWORDS:
            if keyword in lowered:
                clause_type = candidate_type
                break
        if not clause_type and chunk.detected_heading:
            clause_type = "other"
        if clause_type:
            clauses.append(
                ExtractedClause(
                    clause_id=f"clause_{len(clauses):04d}",
                    document_id=document_id,
                    clause_type=clause_type,
                    clause_heading=chunk.detected_heading,
                    clause_text=text,
                    source_chunk_ids=[chunk.chunk_id],
                    source_locators=chunk.source_locators,
                    confidence="medium" if clause_type != "other" else "low",
                    extraction_notes="heuristic fallback extraction",
                )
            )
    return clauses


def extract_clauses_single_pass(document_id: UUID, chunks: list[CandidateChunk], settings: Settings) -> ClauseExtractionResult:
    provider = build_llm_provider(settings)
    prompt = (
        "Extract contractual clauses as JSON with key clauses. "
        "Each clause needs clause_type, clause_heading, clause_text, source_chunk_ids, confidence, extraction_notes."
    )
    context = "\n\n".join(f"[{chunk.chunk_id}]\n{chunk.normalized_text}" for chunk in chunks)
    fallback_used = False
    warnings: list[str] = []
    clauses: list[ExtractedClause]
    response_provider = provider.provider_name
    response_model = provider.model
    try:
        logger.info("clause extraction started chunks=%s provider=%s", len(chunks), provider.provider_name)
        response = provider.generate(
            [LLMMessage(role="system", content=prompt), LLMMessage(role="user", content=context)],
            temperature=0.0,
        )
        response_provider = response.provider
        response_model = response.model
        try:
            clauses = parse_clause_json(response.content, document_id, chunks)
            logger.info("clause extraction parsed clauses=%s", len(clauses))
        except json.JSONDecodeError:
            correction = provider.generate(
                [
                    LLMMessage(role="system", content="Return only valid JSON with a top-level clauses array."),
                    LLMMessage(role="user", content=response.content),
                ],
                temperature=0.0,
            )
            response_provider = correction.provider
            response_model = correction.model
            clauses = parse_clause_json(correction.content, document_id, chunks)
            logger.info("clause extraction correction parsed clauses=%s", len(clauses))
        if not clauses:
            raise ValueError("provider returned no valid clauses")
    except (json.JSONDecodeError, ValueError) as exc:
        warnings.append(f"primary extraction fallback: {exc}")
        fallback_used = True
        clauses = _heuristic_extract(document_id, chunks)
    return ClauseExtractionResult(
        document_id=document_id,
        clauses=clauses,
        provider=response_provider,
        model=response_model,
        prompt_version=settings.clause_prompt_version,
        fallback_used=fallback_used,
        warnings=warnings,
    )
