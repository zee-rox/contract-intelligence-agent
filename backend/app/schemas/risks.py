from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.clauses import Confidence

RiskLevel = Literal["low", "medium", "high"]


class RiskAssessment(BaseModel):
    clause_id: str
    risk_level: RiskLevel
    risk_reason: str
    observed_factors: list[str] = Field(default_factory=list)
    missing_expected_elements: list[str] = Field(default_factory=list)
    confidence: Confidence
    baseline_version: str

    @model_validator(mode="after")
    def require_reason(self) -> "RiskAssessment":
        if not self.risk_reason.strip():
            raise ValueError("risk_reason must not be empty")
        return self
