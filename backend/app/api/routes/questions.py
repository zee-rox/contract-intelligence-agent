from uuid import UUID
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.schemas.qa import QAResponse, QuestionRequest
from app.services.qa_service import QAService, get_qa_service

router = APIRouter()


@router.post("/documents/{document_id}/questions", response_model=QAResponse, tags=["questions"])
def answer_question(
    document_id: UUID,
    request: QuestionRequest,
    service: QAService = Depends(get_qa_service),
) -> QAResponse:
    try:
        return service.answer_question(document_id, request.question)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="document not found") from exc


@router.get("/documents/{document_id}/questions/stream", tags=["questions"])
async def stream_question(
    document_id: UUID,
    question: str,
    request: Request,
    service: QAService = Depends(get_qa_service),
) -> StreamingResponse:
    async def events() -> AsyncIterator[str]:
        for event in service.stream_answer(document_id, question):
            if await request.is_disconnected():
                break
            yield event

    return StreamingResponse(events(), media_type="text/event-stream")
