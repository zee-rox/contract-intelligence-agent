import json
from uuid import uuid4

from app.llm.structured_output import parse_clause_json
from app.schemas.chunks import CandidateChunk
from app.schemas.sources import DocxSourceLocator


def test_parse_clause_json_discards_unknown_model_chunk_ids() -> None:
    document_id = uuid4()
    chunk = CandidateChunk(
        chunk_id="chunk_0000_abc123",
        document_id=document_id,
        chunk_index=0,
        text="Confidentiality. The parties shall protect information.",
        normalized_text="Confidentiality. The parties shall protect information.",
        detected_heading="Confidentiality",
        source_locators=[DocxSourceLocator(section_number=1, paragraph_start=1, paragraph_end=1)],
        char_count=56,
        token_count_estimate=6,
        splitter_strategy="structural",
    )
    payload = json.dumps(
        {
            "clauses": [
                {
                    "clause_type": "confidentiality",
                    "clause_heading": "Confidentiality",
                    "clause_text": "Confidentiality. The parties shall protect information.",
                    "source_chunk_ids": ["0000"],
                    "confidence": "high",
                }
            ]
        }
    )

    clauses = parse_clause_json(payload, document_id, [chunk])

    assert clauses
    assert clauses[0].source_chunk_ids == [chunk.chunk_id]
    assert clauses[0].source_locators[0].char_offset_start == 0
    assert clauses[0].source_locators[0].char_offset_end == len(chunk.normalized_text)
