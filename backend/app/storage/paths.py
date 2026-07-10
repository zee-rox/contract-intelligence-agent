from pathlib import Path
from uuid import UUID


class StoragePaths:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def document_dir(self, document_id: UUID) -> Path:
        path = (self.root / str(document_id)).resolve()
        if self.root not in path.parents and path != self.root:
            raise ValueError("resolved document path escapes storage root")
        return path

    def manifest(self, document_id: UUID) -> Path:
        return self.document_dir(document_id) / "manifest.json"

    def source_file(self, document_id: UUID, source_type: str) -> Path:
        return self.document_dir(document_id) / "source" / f"original.{source_type}"

    def pages(self, document_id: UUID) -> Path:
        return self.document_dir(document_id) / "extracted" / "pages.json"

    def paragraphs(self, document_id: UUID) -> Path:
        return self.document_dir(document_id) / "extracted" / "paragraphs.json"

    def extraction_report(self, document_id: UUID) -> Path:
        return self.document_dir(document_id) / "extracted" / "extraction-report.json"

    def chunks(self, document_id: UUID) -> Path:
        return self.document_dir(document_id) / "chunks" / "chunks.json"

    def clauses(self, document_id: UUID) -> Path:
        return self.document_dir(document_id) / "analysis" / "clauses.json"

    def risks(self, document_id: UUID) -> Path:
        return self.document_dir(document_id) / "analysis" / "risks.json"

    def analysis_manifest(self, document_id: UUID) -> Path:
        return self.document_dir(document_id) / "analysis" / "analysis-manifest.json"

    def faiss_index(self, document_id: UUID) -> Path:
        return self.document_dir(document_id) / "index" / "index.faiss"

    def index_metadata(self, document_id: UUID) -> Path:
        return self.document_dir(document_id) / "index" / "metadata.json"
