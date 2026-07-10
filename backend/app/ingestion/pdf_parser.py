from pathlib import Path
from uuid import UUID

from app.config import Settings
from app.ingestion.normalization import normalize_text
from app.ingestion.ocr import OcrUnavailableError, ocr_pdf_page
from app.ingestion.quality import should_ocr, text_quality_score
from app.schemas.documents import ExtractedPage
from app.schemas.sources import BoundingBox, PdfSourceLocator


def parse_pdf(path: Path, document_id: UUID, settings: Settings) -> tuple[list[ExtractedPage], list[str]]:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PyMuPDF is required for PDF parsing") from exc

    warnings: list[str] = []
    pages: list[ExtractedPage] = []
    try:
        pdf = fitz.open(path)
    except Exception as exc:
        raise ValueError("corrupt_pdf") from exc
    if pdf.is_encrypted:
        raise ValueError("encrypted_pdf")

    for page_index, page in enumerate(pdf):
        page_number = page_index + 1
        raw_text = page.get_text("text")
        score = text_quality_score(raw_text)
        use_ocr, reason = should_ocr(raw_text, score)
        method: str = "native"
        if use_ocr and settings.ocr_enabled:
            try:
                ocr_text = ocr_pdf_page(path, page_index, settings.ocr_language, settings.ocr_dpi)
                if ocr_text.strip():
                    raw_text = ocr_text
                    score = text_quality_score(raw_text)
                    method = "ocr"
                else:
                    warnings.append(f"page {page_number}: OCR returned no text")
            except OcrUnavailableError as exc:
                warnings.append(f"page {page_number}: {exc}")

        normalized = normalize_text(raw_text)
        rect = page.rect
        pages.append(
            ExtractedPage(
                page_number=page_number,
                width=float(rect.width),
                height=float(rect.height),
                raw_text=raw_text,
                normalized_text=normalized,
                extraction_method="ocr" if method == "ocr" else "native",
                quality_score=score,
                ocr_reason=reason if method == "ocr" else None,
                warnings=[],
                source_locator=PdfSourceLocator(
                    page_number=page_number,
                    char_offset_start=0,
                    char_offset_end=len(normalized),
                    bounding_boxes=[BoundingBox(x0=0, y0=0, x1=float(rect.width), y1=float(rect.height))],
                ),
            )
        )
    if not any(page.normalized_text for page in pages):
        raise ValueError("no_extractable_content")
    return pages, warnings
