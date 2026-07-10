from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, Field


class IndexMetadata(BaseModel):
    artifact_version: str = "index-metadata-v1"
    document_id: UUID
    embedding_model: str
    embedding_dimension: int = Field(gt=0)
    index_type: str = "IndexFlatIP"
    chunk_ids: list[str]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RetrievalResult(BaseModel):
    chunk_id: str
    score: float
    rank: int
