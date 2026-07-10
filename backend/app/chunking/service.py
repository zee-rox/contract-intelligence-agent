import hashlib
from uuid import UUID

from app.chunking.fallback_splitter import split_long_text
from app.chunking.structure_detector import detect_heading
from app.schemas.chunks import CandidateChunk, SplitterStrategy
from app.schemas.documents import ExtractedPage, ExtractedParagraph
from app.schemas.sources import SourceLocator


def _stable_chunk_id(document_id: UUID, index: int, text: str) -> str:
    digest = hashlib.sha256(f"{document_id}:{index}:{text}".encode("utf-8")).hexdigest()[:16]
    return f"chunk_{index:04d}_{digest}"


def _estimate_tokens(text: str) -> int:
    return max(1, len(text.split()))


def _paragraph_units(pages: list[ExtractedPage], paragraphs: list[ExtractedParagraph]) -> list[tuple[str, str | None, list[SourceLocator], bool]]:
    units: list[tuple[str, str | None, list[SourceLocator], bool]] = []
    for page in pages:
        for para in [part.strip() for part in page.normalized_text.split("\n\n") if part.strip()]:
            first_line = para.splitlines()[0]
            units.append((para, detect_heading(first_line), [page.source_locator], page.extraction_method == "ocr"))
    for paragraph in paragraphs:
        heading = paragraph.normalized_text if (paragraph.style_name or "").lower().startswith("heading") else detect_heading(paragraph.normalized_text)
        units.append((paragraph.normalized_text, heading, [paragraph.source_locator], False))
    return units


def create_candidate_chunks(
    document_id: UUID,
    pages: list[ExtractedPage],
    paragraphs: list[ExtractedParagraph],
    max_chars: int = 1800,
) -> list[CandidateChunk]:
    units = _paragraph_units(pages, paragraphs)
    chunks: list[CandidateChunk] = []
    current_text: list[str] = []
    current_heading: str | None = None
    current_locators: list[SourceLocator] = []
    current_ocr = False

    def flush() -> None:
        nonlocal current_text, current_heading, current_locators, current_ocr
        if not current_text:
            return
        text = "\n\n".join(current_text).strip()
        for part in split_long_text(text, max_chars=max_chars):
            index = len(chunks)
            strategy: SplitterStrategy = "ocr_structural" if current_ocr else "structural"
            if len(text) > max_chars:
                strategy = "ocr_fallback" if current_ocr else "recursive_fallback"
            chunks.append(
                CandidateChunk(
                    chunk_id=_stable_chunk_id(document_id, index, part),
                    document_id=document_id,
                    chunk_index=index,
                    text=part,
                    normalized_text=part,
                    detected_heading=current_heading,
                    source_locators=current_locators,
                    char_count=len(part),
                    token_count_estimate=_estimate_tokens(part),
                    splitter_strategy=strategy,
                )
            )
        current_text = []
        current_heading = None
        current_locators = []
        current_ocr = False

    for text, heading, locators, is_ocr in units:
        starts_new = heading is not None and current_text
        would_exceed = sum(len(item) for item in current_text) + len(text) > max_chars
        if starts_new or would_exceed:
            flush()
        if heading and not current_heading:
            current_heading = heading
        current_text.append(text)
        current_locators.extend(locators)
        current_ocr = current_ocr or is_ocr
    flush()
    return chunks
