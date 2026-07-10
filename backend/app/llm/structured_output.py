import json
from uuid import UUID

from pydantic import ValidationError

from app.schemas.chunks import CandidateChunk
from app.schemas.clauses import ExtractedClause


def parse_clause_json(payload: str, document_id: UUID, chunks: list[CandidateChunk]) -> list[ExtractedClause]:
    data = json.loads(payload)
    chunk_by_id = {chunk.chunk_id: chunk for chunk in chunks}
    clauses: list[ExtractedClause] = []
    for index, item in enumerate(data.get("clauses", [])):
        source_ids = item.get("source_chunk_ids") or []
        if not source_ids:
            source_ids = [chunk.chunk_id for chunk in chunks if item.get("clause_heading", "").lower() in chunk.normalized_text.lower()]
        if not source_ids and chunks:
            source_ids = [chunks[0].chunk_id]
        locators = []
        for chunk_id in source_ids:
            locators.extend(chunk_by_id[chunk_id].source_locators)
        try:
            clauses.append(
                ExtractedClause.model_validate(
                    {
                        **item,
                        "clause_id": f"clause_{index:04d}",
                        "document_id": document_id,
                        "source_chunk_ids": source_ids,
                        "source_locators": locators,
                    }
                )
            )
        except ValidationError:
            continue
    return clauses
