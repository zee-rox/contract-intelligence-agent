from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.sources import SourceLocator

DocumentStatus = Literal[
    "registered",
    "parsing",
    "chunking",
    "indexing",
    "ready",
    "analysis_failed",
    "failed",
]


class DocumentRecord(BaseModel):
    document_id: UUID
    original_filename: str
    sanitized_filename: str
    source_type: Literal["pdf", "docx"]
    content_type: str
    file_size_bytes: int = Field(ge=0)
    sha256: str
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime
    parser_version: str
    error_code: str | None = None
    error_message: str | None = None


class ExtractedPage(BaseModel):
    page_number: int = Field(ge=1)
    width: float
    height: float
    raw_text: str
    normalized_text: str
    extraction_method: Literal["native", "ocr"]
    quality_score: float = Field(ge=0, le=1)
    ocr_reason: str | None = None
    warnings: list[str] = Field(default_factory=list)
    source_locator: SourceLocator


class ExtractedParagraph(BaseModel):
    paragraph_number: int = Field(ge=1)
    section_number: int | None = Field(default=None, ge=1)
    style_name: str | None = None
    raw_text: str
    normalized_text: str
    source_locator: SourceLocator


class ExtractionReport(BaseModel):
    document_id: UUID
    source_type: Literal["pdf", "docx"]
    parser_version: str
    extraction_warnings: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
