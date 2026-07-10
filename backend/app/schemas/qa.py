from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.clauses import Confidence
from app.schemas.sources import SourceLocator


class Citation(BaseModel):
    citation_id: str
    chunk_id: str
    source_locator: SourceLocator
    quoted_snippet: str


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class ModelQAResponse(BaseModel):
    answer: str
    citation_ids: list[str] = Field(default_factory=list)
    confidence: Confidence = "low"


class QAResponse(BaseModel):
    answer: str
    citations: list[Citation]
    confidence: Confidence
    refused: bool = False
    refusal_reason: Literal["insufficient_evidence", "invalid_citations", "retrieval_failed"] | None = None

    @model_validator(mode="after")
    def validate_refusal_shape(self) -> "QAResponse":
        if self.refused and self.refusal_reason is None:
            raise ValueError("refusal_reason is required when refused is true")
        if self.refused and self.citations:
            raise ValueError("refused responses must not include citations")
        return self
