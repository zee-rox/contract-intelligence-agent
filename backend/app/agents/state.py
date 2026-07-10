from typing import TypedDict
from uuid import UUID

from app.schemas.clauses import ClauseExtractionResult
from app.schemas.chunks import CandidateChunk
from app.schemas.risks import RiskAssessment


class AnalysisState(TypedDict, total=False):
    document_id: UUID
    clause_result: ClauseExtractionResult
    chunks: list[CandidateChunk]
    risks: list[RiskAssessment]
    warnings: list[str]
    stage: str
