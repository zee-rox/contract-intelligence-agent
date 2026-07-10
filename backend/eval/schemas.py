from typing import Literal

from pydantic import BaseModel, Field


class EvalParagraph(BaseModel):
    heading: str
    text: str


class ExpectedClause(BaseModel):
    clause_type: str
    snippet: str
    risk_level: Literal["low", "medium", "high"]


class QuestionExpectation(BaseModel):
    question: str
    expected_refused: bool
    expected_answer_terms: list[str] = Field(default_factory=list)
    expected_citation_terms: list[str] = Field(default_factory=list)


class EvalDocument(BaseModel):
    document_id: str
    filename: str
    paragraphs: list[EvalParagraph]
    expected_clauses: list[ExpectedClause]
    questions: list[QuestionExpectation]
    ocr_expected_pages: int = 0


class EvaluationDataset(BaseModel):
    dataset_version: str
    description: str
    documents: list[EvalDocument]
