from uuid import UUID

from app.agents.clause_extraction import extract_clauses_single_pass
from app.chunking.service import create_candidate_chunks
from app.config import Settings, get_settings
from app.ingestion.service import parse_and_persist, register_document
from app.schemas.api import DocumentIngestionResponse
from app.schemas.clauses import ClauseExtractionResult
from app.storage.repository import StorageRepository


class DocumentService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.repository = StorageRepository(settings.storage_root)

    def ingest_upload(self, filename: str, content_type: str, payload: bytes) -> DocumentIngestionResponse:
        record = register_document(filename, content_type, payload, self.settings)
        parsed = parse_and_persist(record, payload, self.repository, self.settings)
        chunks = create_candidate_chunks(record.document_id, parsed.pages, parsed.paragraphs)
        chunking_record = parsed.record.model_copy(update={"status": "chunking"})
        self.repository.save_manifest(chunking_record)
        self.repository.save_chunks(record.document_id, chunks)
        ready = chunking_record.model_copy(update={"status": "ready"})
        self.repository.save_manifest(ready)
        return DocumentIngestionResponse(document=ready, chunks=chunks)

    def extract_clauses(self, document_id: UUID, settings: Settings | None = None) -> ClauseExtractionResult:
        chunks = self.repository.load_chunks(document_id)
        result = extract_clauses_single_pass(document_id, chunks, settings or self.settings)
        self.repository.save_clause_result(result)
        return result


def get_document_service() -> DocumentService:
    return DocumentService(get_settings())
