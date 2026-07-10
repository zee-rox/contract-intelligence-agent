import tempfile
from pathlib import Path
from uuid import UUID

import faiss
import numpy as np

from app.retrieval.embeddings import HashEmbeddingService
from app.schemas.chunks import CandidateChunk
from app.schemas.retrieval import IndexMetadata, RetrievalResult
from app.storage.errors import ArtifactValidationError
from app.storage.repository import StorageRepository


class DocumentFaissIndex:
    def __init__(self, repository: StorageRepository, embedding_service: HashEmbeddingService) -> None:
        self.repository = repository
        self.embedding_service = embedding_service

    def build_and_persist(self, document_id: UUID, chunks: list[CandidateChunk]) -> IndexMetadata:
        texts = [chunk.normalized_text for chunk in chunks]
        vectors = self.embedding_service.embed_texts(texts)
        index = faiss.IndexFlatIP(self.embedding_service.dimension)
        index.add(vectors)
        index_path = self.repository.paths.faiss_index(document_id)
        index_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=index_path.parent, suffix=".faiss", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        faiss.write_index(index, str(tmp_path))
        tmp_path.replace(index_path)
        metadata = IndexMetadata(
            document_id=document_id,
            embedding_model=self.embedding_service.model_name,
            embedding_dimension=self.embedding_service.dimension,
            chunk_ids=[chunk.chunk_id for chunk in chunks],
        )
        self.repository.save_index_metadata(metadata)
        return metadata

    def search(self, document_id: UUID, query: str, top_k: int) -> list[RetrievalResult]:
        metadata = self.repository.load_index_metadata(document_id)
        index_path = self.repository.paths.faiss_index(document_id)
        if not index_path.exists():
            raise ArtifactValidationError("FAISS index artifact is missing")
        index = faiss.read_index(str(index_path))
        if index.d != metadata.embedding_dimension:
            raise ArtifactValidationError("FAISS index dimension does not match metadata")
        query_vector = self.embedding_service.embed_query(query)
        scores, positions = index.search(query_vector, min(top_k, len(metadata.chunk_ids)))
        results: list[RetrievalResult] = []
        for rank, (score, position) in enumerate(zip(scores[0], positions[0]), start=1):
            if position < 0:
                continue
            results.append(
                RetrievalResult(
                    chunk_id=metadata.chunk_ids[int(position)],
                    score=float(np.float32(score)),
                    rank=rank,
                )
            )
        return results
