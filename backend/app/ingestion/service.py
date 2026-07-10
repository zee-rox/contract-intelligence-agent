import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.config import Settings
from app.ingestion.docx_parser import parse_docx
from app.ingestion.pdf_parser import parse_pdf
from app.schemas.documents import DocumentRecord, ExtractedPage, ExtractedParagraph, ExtractionReport
from app.storage.repository import StorageRepository


class IngestionError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class ParsedDocument:
    record: DocumentRecord
    pages: list[ExtractedPage]
    paragraphs: list[ExtractedParagraph]
    warnings: list[str]


def sanitize_filename(filename: str) -> str:
    base = Path(filename).name
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", base).strip("._")
    return base or "contract"


def detect_source_type(filename: str, content_type: str, payload: bytes) -> tuple[str, str]:
    lower = filename.lower()
    if lower.endswith(".pdf") and payload.startswith(b"%PDF"):
        return "pdf", "application/pdf"
    if lower.endswith(".docx") and payload.startswith(b"PK"):
        return "docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    if lower.endswith(".pdf") or lower.endswith(".docx"):
        raise IngestionError("unsupported_file_type", "file signature does not match extension")
    raise IngestionError("unsupported_file_type", f"unsupported content type: {content_type}")


def register_document(filename: str, content_type: str, payload: bytes, settings: Settings) -> DocumentRecord:
    if not filename:
        raise IngestionError("unsupported_file_type", "filename is required")
    if not payload:
        raise IngestionError("empty_file", "uploaded file is empty")
    if len(payload) > settings.max_upload_size_bytes:
        raise IngestionError("file_too_large", "uploaded file exceeds configured size limit")
    source_type, normalized_content_type = detect_source_type(filename, content_type, payload)
    now = datetime.now(timezone.utc)
    return DocumentRecord(
        document_id=uuid4(),
        original_filename=filename,
        sanitized_filename=sanitize_filename(filename),
        source_type=source_type,  # type: ignore[arg-type]
        content_type=normalized_content_type,
        file_size_bytes=len(payload),
        sha256=hashlib.sha256(payload).hexdigest(),
        status="registered",
        created_at=now,
        updated_at=now,
        parser_version=settings.parser_version,
    )


def parse_and_persist(record: DocumentRecord, payload: bytes, repository: StorageRepository, settings: Settings) -> ParsedDocument:
    repository.save_manifest(record)
    source_path = repository.save_source(record.document_id, record.source_type, payload)
    parsing_record = record.model_copy(update={"status": "parsing", "updated_at": datetime.now(timezone.utc)})
    repository.save_manifest(parsing_record)
    try:
        if record.source_type == "pdf":
            pages, warnings = parse_pdf(source_path, record.document_id, settings)
            paragraphs: list[ExtractedParagraph] = []
            repository.save_pages(record.document_id, pages)
        else:
            paragraphs, warnings = parse_docx(source_path, record.document_id)
            pages = []
            repository.save_paragraphs(record.document_id, paragraphs)
    except ValueError as exc:
        code = str(exc)
        failed = parsing_record.model_copy(
            update={"status": "failed", "error_code": code, "error_message": code, "updated_at": datetime.now(timezone.utc)}
        )
        repository.save_manifest(failed)
        raise IngestionError(code, code) from exc

    report = ExtractionReport(
        document_id=record.document_id,
        source_type=record.source_type,
        parser_version=settings.parser_version,
        extraction_warnings=warnings,
    )
    repository.save_extraction_report(report)
    return ParsedDocument(record=parsing_record, pages=pages, paragraphs=paragraphs, warnings=warnings)
