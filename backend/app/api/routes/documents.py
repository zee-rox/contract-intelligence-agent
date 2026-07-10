from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.config import Settings, get_settings
from app.ingestion.service import IngestionError
from app.schemas.api import DocumentIngestionResponse
from app.schemas.clauses import ClauseExtractionResult
from app.schemas.documents import DocumentRecord
from app.services.document_service import DocumentService, get_document_service

router = APIRouter()


@router.post("", response_model=DocumentIngestionResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service),
) -> DocumentIngestionResponse:
    payload = await file.read()
    try:
        return service.ingest_upload(
            filename=file.filename or "",
            content_type=file.content_type or "application/octet-stream",
            payload=payload,
        )
    except IngestionError as exc:
        raise HTTPException(status_code=400, detail={"code": exc.code, "message": exc.message}) from exc


@router.get("/{document_id}", response_model=DocumentRecord)
def get_document(
    document_id: UUID,
    service: DocumentService = Depends(get_document_service),
) -> DocumentRecord:
    try:
        return service.repository.load_manifest(document_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="document not found") from exc


@router.post("/{document_id}/extract-clauses", response_model=ClauseExtractionResult)
def extract_clauses(
    document_id: UUID,
    settings: Settings = Depends(get_settings),
    service: DocumentService = Depends(get_document_service),
) -> ClauseExtractionResult:
    try:
        return service.extract_clauses(document_id=document_id, settings=settings)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="document not found") from exc
