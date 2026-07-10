from uuid import uuid4

from app.agents.clause_extraction import extract_clauses_single_pass
from app.config import Settings
from app.schemas.chunks import CandidateChunk
from app.schemas.sources import DocxSourceLocator


def test_clause_extraction_falls_back_to_heuristics(tmp_path) -> None:
    document_id = uuid4()
    settings = Settings(storage_root=tmp_path, llm_provider="fake")
    chunk = CandidateChunk(
        chunk_id="chunk_0000",
        document_id=document_id,
        chunk_index=0,
        text="Termination. Either party may terminate on thirty days notice.",
        normalized_text="Termination. Either party may terminate on thirty days notice.",
        detected_heading="Termination",
        source_locators=[DocxSourceLocator(section_number=1, paragraph_start=1, paragraph_end=1)],
        char_count=61,
        token_count_estimate=9,
        splitter_strategy="structural",
    )
    result = extract_clauses_single_pass(document_id, [chunk], settings)
    assert result.clauses
    assert result.clauses[0].clause_type == "termination"
    assert result.clauses[0].source_chunk_ids == ["chunk_0000"]
