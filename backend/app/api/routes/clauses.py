from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.analysis import ClauseAnalysisResult
from app.services.analysis_service import AnalysisService, get_analysis_service

router = APIRouter()


@router.get("/documents/{document_id}/clauses", response_model=ClauseAnalysisResult, tags=["clauses"])
def get_document_clauses(
    document_id: UUID,
    service: AnalysisService = Depends(get_analysis_service),
) -> ClauseAnalysisResult:
    try:
        return service.get_or_run_analysis(document_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="document not found") from exc
