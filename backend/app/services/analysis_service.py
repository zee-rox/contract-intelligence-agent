import logging
from uuid import UUID

from app.agents.supervisor import AnalysisSupervisor
from app.config import Settings, get_settings
from app.schemas.analysis import ClauseAnalysisResult
from app.schemas.clauses import ClauseExtractionResult
from app.storage.locking import document_lock
from app.storage.repository import StorageRepository

logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.repository = StorageRepository(settings.storage_root)

    def get_or_run_analysis(self, document_id: UUID) -> ClauseAnalysisResult:
        with document_lock(document_id):
            try:
                manifest = self.repository.load_analysis_manifest(document_id)
                clause_result = self.repository.load_clause_result(document_id)
                risks = self.repository.load_risks(document_id)
                return ClauseAnalysisResult(
                    document_id=document_id,
                    clauses=clause_result.clauses,
                    risks=risks,
                    manifest=manifest,
                )
            except FileNotFoundError:
                chunks = self.repository.load_chunks(document_id)
                logger.info("analysis started document_id=%s chunks=%s", document_id, len(chunks))
                result = AnalysisSupervisor(self.settings).run(document_id, chunks)
                self.repository.save_clause_result(self._clause_result_from_analysis(result))
                self.repository.save_risks(document_id, result.risks)
                self.repository.save_analysis_manifest(result.manifest)
                logger.info(
                    "analysis persisted document_id=%s clauses=%s risks=%s",
                    document_id,
                    len(result.clauses),
                    len(result.risks),
                )
                return result

    def _clause_result_from_analysis(self, result: ClauseAnalysisResult) -> ClauseExtractionResult:
        return ClauseExtractionResult(
            document_id=result.document_id,
            clauses=result.clauses,
            provider=result.manifest.provider,
            model=result.manifest.model,
            prompt_version=result.manifest.prompt_version,
            fallback_used=bool(result.manifest.warnings),
            warnings=result.manifest.warnings,
        )


def get_analysis_service() -> AnalysisService:
    return AnalysisService(get_settings())
