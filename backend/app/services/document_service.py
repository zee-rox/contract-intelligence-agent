from uuid import UUID
from datetime import datetime, timezone

from app.agents.clause_extraction import extract_clauses_single_pass
from app.chunking.service import create_candidate_chunks
from app.config import Settings, get_settings
from app.ingestion.service import parse_and_persist, register_document
from app.retrieval.embeddings import HashEmbeddingService
from app.retrieval.index import DocumentFaissIndex
from app.schemas.api import DocumentIngestionResponse
from app.schemas.clauses import ClauseExtractionResult
from app.storage.repository import StorageRepository
from app.storage.locking import document_lock


class DocumentService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.repository = StorageRepository(settings.storage_root)

    def ingest_upload(self, filename: str, content_type: str, payload: bytes) -> DocumentIngestionResponse:
        record = register_document(filename, content_type, payload, self.settings)
        with document_lock(record.document_id):
            try:
                parsed = parse_and_persist(record, payload, self.repository, self.settings)
                chunks = create_candidate_chunks(record.document_id, parsed.pages, parsed.paragraphs)
                chunking_record = parsed.record.model_copy(update={"status": "chunking", "updated_at": datetime.now(timezone.utc)})
                self.repository.save_manifest(chunking_record)
                self.repository.save_chunks(record.document_id, chunks)
                indexing_record = chunking_record.model_copy(update={"status": "indexing", "updated_at": datetime.now(timezone.utc)})
                self.repository.save_manifest(indexing_record)
                index = DocumentFaissIndex(
                    self.repository,
                    HashEmbeddingService(self.settings.embedding_model, self.settings.embedding_dimension),
                )
                index.build_and_persist(record.document_id, chunks)
                ready = indexing_record.model_copy(update={"status": "ready", "updated_at": datetime.now(timezone.utc)})
                self.repository.save_manifest(ready)
                return DocumentIngestionResponse(document=ready, chunks=chunks, warnings=parsed.warnings)
            except Exception:
                failed = record.model_copy(
                    update={
                        "status": "failed",
                        "error_code": "ingestion_failed",
                        "error_message": "document ingestion did not complete",
                        "updated_at": datetime.now(timezone.utc),
                    }
                )
                self.repository.save_manifest(failed)
                raise

    def extract_clauses(self, document_id: UUID, settings: Settings | None = None) -> ClauseExtractionResult:
        with document_lock(document_id):
            chunks = self.repository.load_chunks(document_id)
            result = extract_clauses_single_pass(document_id, chunks, settings or self.settings)
            self.repository.save_clause_result(result)
            return result


def get_document_service() -> DocumentService:
    return DocumentService(get_settings())
