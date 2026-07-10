import json
from pathlib import Path
from uuid import UUID

from app.schemas.chunks import CandidateChunk
from app.schemas.analysis import AnalysisManifest
from app.schemas.clauses import ClauseExtractionResult
from app.schemas.documents import DocumentRecord, ExtractedPage, ExtractedParagraph, ExtractionReport
from app.schemas.retrieval import IndexMetadata
from app.schemas.risks import RiskAssessment
from app.storage.atomic import atomic_write_json
from app.storage.paths import StoragePaths


class StorageRepository:
    def __init__(self, root: Path) -> None:
        self.paths = StoragePaths(root)

    def save_source(self, document_id: UUID, source_type: str, payload: bytes) -> Path:
        path = self.paths.source_file(document_id, source_type)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_bytes(payload)
        tmp.replace(path)
        return path

    def save_manifest(self, record: DocumentRecord) -> None:
        atomic_write_json(self.paths.manifest(record.document_id), record)

    def load_manifest(self, document_id: UUID) -> DocumentRecord:
        data = json.loads(self.paths.manifest(document_id).read_text(encoding="utf-8"))
        return DocumentRecord.model_validate(data)

    def save_pages(self, document_id: UUID, pages: list[ExtractedPage]) -> None:
        atomic_write_json(self.paths.pages(document_id), pages)

    def load_pages(self, document_id: UUID) -> list[ExtractedPage]:
        path = self.paths.pages(document_id)
        if not path.exists():
            return []
        return [ExtractedPage.model_validate(item) for item in json.loads(path.read_text(encoding="utf-8"))]

    def save_paragraphs(self, document_id: UUID, paragraphs: list[ExtractedParagraph]) -> None:
        atomic_write_json(self.paths.paragraphs(document_id), paragraphs)

    def load_paragraphs(self, document_id: UUID) -> list[ExtractedParagraph]:
        path = self.paths.paragraphs(document_id)
        if not path.exists():
            return []
        return [ExtractedParagraph.model_validate(item) for item in json.loads(path.read_text(encoding="utf-8"))]

    def save_extraction_report(self, report: ExtractionReport) -> None:
        atomic_write_json(self.paths.extraction_report(report.document_id), report)

    def save_chunks(self, document_id: UUID, chunks: list[CandidateChunk]) -> None:
        atomic_write_json(self.paths.chunks(document_id), chunks)

    def load_chunks(self, document_id: UUID) -> list[CandidateChunk]:
        return [CandidateChunk.model_validate(item) for item in json.loads(self.paths.chunks(document_id).read_text(encoding="utf-8"))]

    def save_clause_result(self, result: ClauseExtractionResult) -> None:
        atomic_write_json(self.paths.clauses(result.document_id), result)

    def load_clause_result(self, document_id: UUID) -> ClauseExtractionResult:
        data = json.loads(self.paths.clauses(document_id).read_text(encoding="utf-8"))
        return ClauseExtractionResult.model_validate(data)

    def save_risks(self, document_id: UUID, risks: list[RiskAssessment]) -> None:
        atomic_write_json(self.paths.risks(document_id), risks)

    def load_risks(self, document_id: UUID) -> list[RiskAssessment]:
        return [RiskAssessment.model_validate(item) for item in json.loads(self.paths.risks(document_id).read_text(encoding="utf-8"))]

    def save_analysis_manifest(self, manifest: AnalysisManifest) -> None:
        atomic_write_json(self.paths.analysis_manifest(manifest.document_id), manifest)

    def load_analysis_manifest(self, document_id: UUID) -> AnalysisManifest:
        data = json.loads(self.paths.analysis_manifest(document_id).read_text(encoding="utf-8"))
        return AnalysisManifest.model_validate(data)

    def save_index_metadata(self, metadata: IndexMetadata) -> None:
        atomic_write_json(self.paths.index_metadata(metadata.document_id), metadata)

    def load_index_metadata(self, document_id: UUID) -> IndexMetadata:
        data = json.loads(self.paths.index_metadata(document_id).read_text(encoding="utf-8"))
        return IndexMetadata.model_validate(data)
