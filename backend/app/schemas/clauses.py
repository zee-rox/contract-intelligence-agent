from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.schemas.sources import SourceLocator

ClauseType = Literal[
    "termination",
    "liability",
    "indemnification",
    "payment_terms",
    "confidentiality",
    "governing_law",
    "force_majeure",
    "other",
]
Confidence = Literal["high", "medium", "low"]


class ExtractedClause(BaseModel):
    clause_id: str
    document_id: UUID
    clause_type: ClauseType
    clause_heading: str | None
    clause_text: str
    source_chunk_ids: list[str]
    source_locators: list[SourceLocator]
    confidence: Confidence
    extraction_notes: str | None = None

    @model_validator(mode="after")
    def require_traceability(self) -> "ExtractedClause":
        if not self.clause_text.strip():
            raise ValueError("clause_text must not be empty")
        if not self.source_chunk_ids:
            raise ValueError("source_chunk_ids must not be empty")
        if not self.source_locators:
            raise ValueError("source_locators must not be empty")
        return self


class ClauseExtractionResult(BaseModel):
    document_id: UUID
    clauses: list[ExtractedClause]
    provider: str
    model: str
    prompt_version: str
    fallback_used: bool = False
    warnings: list[str] = Field(default_factory=list)
