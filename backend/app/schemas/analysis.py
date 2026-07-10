from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.clauses import ExtractedClause
from app.schemas.risks import RiskAssessment


class AnalysisManifest(BaseModel):
    document_id: UUID
    status: Literal["completed", "partial_failure", "failed"]
    prompt_version: str
    risk_baseline_version: str
    provider: str
    model: str
    graph_version: str = "analysis-graph-v1"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    warnings: list[str] = Field(default_factory=list)


class ClauseAnalysisResult(BaseModel):
    document_id: UUID
    clauses: list[ExtractedClause]
    risks: list[RiskAssessment]
    manifest: AnalysisManifest
