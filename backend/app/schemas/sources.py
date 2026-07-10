from typing import Annotated, Literal

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float


class PdfSourceLocator(BaseModel):
    source_type: Literal["pdf"] = "pdf"
    page_number: int = Field(ge=1)
    char_offset_start: int | None = Field(default=None, ge=0)
    char_offset_end: int | None = Field(default=None, ge=0)
    bounding_boxes: list[BoundingBox] = Field(default_factory=list)


class DocxSourceLocator(BaseModel):
    source_type: Literal["docx"] = "docx"
    section_number: int | None = Field(default=None, ge=1)
    paragraph_start: int = Field(ge=1)
    paragraph_end: int = Field(ge=1)
    char_offset_start: int | None = Field(default=None, ge=0)
    char_offset_end: int | None = Field(default=None, ge=0)


SourceLocator = Annotated[PdfSourceLocator | DocxSourceLocator, Field(discriminator="source_type")]
