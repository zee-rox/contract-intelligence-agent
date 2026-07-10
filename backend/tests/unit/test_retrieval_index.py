from uuid import uuid4

from app.retrieval.embeddings import HashEmbeddingService
from app.retrieval.index import DocumentFaissIndex
from app.schemas.chunks import CandidateChunk
from app.schemas.sources import DocxSourceLocator
from app.storage.repository import StorageRepository


def _chunk(document_id, chunk_id: str, text: str) -> CandidateChunk:
    return CandidateChunk(
        chunk_id=chunk_id,
        document_id=document_id,
        chunk_index=0,
        text=text,
        normalized_text=text,
        detected_heading=None,
        source_locators=[DocxSourceLocator(section_number=1, paragraph_start=1, paragraph_end=1)],
        char_count=len(text),
        token_count_estimate=len(text.split()),
        splitter_strategy="structural",
    )


def test_faiss_index_is_document_local_and_reloads(tmp_path) -> None:
    repository = StorageRepository(tmp_path)
    embeddings = HashEmbeddingService("test-hash", 32)
    index = DocumentFaissIndex(repository, embeddings)
    first_id = uuid4()
    second_id = uuid4()

    index.build_and_persist(first_id, [_chunk(first_id, "first_chunk", "termination notice period")])
    index.build_and_persist(second_id, [_chunk(second_id, "second_chunk", "payment invoice deadline")])

    first_results = DocumentFaissIndex(repository, embeddings).search(first_id, "termination", top_k=1)
    second_results = DocumentFaissIndex(repository, embeddings).search(second_id, "payment", top_k=1)

    assert first_results[0].chunk_id == "first_chunk"
    assert second_results[0].chunk_id == "second_chunk"
    assert repository.paths.faiss_index(first_id) != repository.paths.faiss_index(second_id)
