import json
import re
from uuid import UUID

from pydantic import ValidationError

from app.schemas.chunks import CandidateChunk
from app.schemas.clauses import ExtractedClause


def _normalized_with_map(text: str) -> tuple[str, list[int]]:
    output: list[str] = []
    positions: list[int] = []
    pending_space = False
    for index, char in enumerate(text):
        if char.isspace():
            pending_space = bool(output)
            continue
        if pending_space and output:
            output.append(" ")
            positions.append(index)
        output.append(char)
        positions.append(index)
        pending_space = False
    return "".join(output), positions


def _source_match(source: str, candidate: str) -> tuple[str, int, int] | None:
    normalized_source, positions = _normalized_with_map(source)
    normalized_candidate = re.sub(r"\s+", " ", candidate).strip()
    if not normalized_candidate:
        return None
    start = normalized_source.casefold().find(normalized_candidate.casefold())
    if start < 0 or start >= len(positions):
        return None
    end_index = min(start + len(normalized_candidate) - 1, len(positions) - 1)
    original_start = positions[start]
    original_end = positions[end_index] + 1
    return source[original_start:original_end], original_start, original_end


def parse_clause_json(
    payload: str,
    document_id: UUID,
    chunks: list[CandidateChunk],
    warnings: list[str] | None = None,
) -> list[ExtractedClause]:
    data = json.loads(payload)
    chunk_by_id = {chunk.chunk_id: chunk for chunk in chunks}
    clauses: list[ExtractedClause] = []
    for index, item in enumerate(data.get("clauses", [])):
        requested_ids = item.get("source_chunk_ids") or []
        requested_chunks = [chunk_by_id[chunk_id] for chunk_id in requested_ids if chunk_id in chunk_by_id]
        search_chunks = requested_chunks or chunks
        grounded: list[tuple[CandidateChunk, str, int, int]] = []
        for chunk in search_chunks:
            match = _source_match(chunk.normalized_text, str(item.get("clause_text") or ""))
            if match:
                grounded.append((chunk, *match))
        if not grounded:
            if warnings is not None:
                warnings.append(f"clause {index}: discarded because clause_text was not found in source text")
            continue
        source_ids = [chunk.chunk_id for chunk, *_ in grounded]
        locators = []
        for chunk, _, start, end in grounded:
            for locator in chunk.source_locators:
                update = {"char_offset_start": start, "char_offset_end": end}
                locators.append(locator.model_copy(update=update))
        source_text = "\n\n".join(text for _, text, _, _ in grounded)
        try:
            clauses.append(
                ExtractedClause.model_validate(
                    {
                        **item,
                        "clause_id": f"clause_{index:04d}",
                        "document_id": document_id,
                        "source_chunk_ids": source_ids,
                        "source_locators": locators,
                        "clause_text": source_text,
                    }
                )
            )
        except ValidationError:
            if warnings is not None:
                warnings.append(f"clause {index}: discarded because the grounded result failed schema validation")
            continue
    return clauses
