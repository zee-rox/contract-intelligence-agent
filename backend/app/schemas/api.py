from app.schemas.chunks import CandidateChunk
from app.schemas.documents import DocumentRecord

from pydantic import BaseModel


class DocumentIngestionResponse(BaseModel):
    document: DocumentRecord
    chunks: list[CandidateChunk]
    warnings: list[str] = []
