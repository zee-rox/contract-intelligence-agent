from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.sources import SourceLocator

SplitterStrategy = Literal["structural", "recursive_fallback", "ocr_structural", "ocr_fallback"]


class CandidateChunk(BaseModel):
    chunk_id: str
    document_id: UUID
    chunk_index: int = Field(ge=0)
    text: str
    normalized_text: str
    detected_heading: str | None
    source_locators: list[SourceLocator]
    char_count: int = Field(ge=0)
    token_count_estimate: int = Field(ge=0)
    splitter_strategy: SplitterStrategy
