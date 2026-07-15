from uuid import uuid4

from app.agents.qa import create_citations, parse_model_qa_response, validate_or_repair_response
from app.schemas.chunks import CandidateChunk
from app.schemas.qa import ModelQAResponse
from app.schemas.retrieval import RetrievalResult
from app.schemas.sources import DocxSourceLocator


def test_citation_snippet_is_exact_source_substring() -> None:
    document_id = uuid4()
    chunk = CandidateChunk(
        chunk_id="chunk_0000",
        document_id=document_id,
        chunk_index=0,
        text="Termination. Either party may terminate with thirty days notice.",
        normalized_text="Termination. Either party may terminate with thirty days notice.",
        detected_heading="Termination",
        source_locators=[DocxSourceLocator(section_number=1, paragraph_start=1, paragraph_end=1)],
        char_count=64,
        token_count_estimate=8,
        splitter_strategy="structural",
    )
    citations = create_citations("How can a party terminate?", [chunk], [RetrievalResult(chunk_id=chunk.chunk_id, score=0.9, rank=1)])

    assert citations
    assert citations[0].quoted_snippet in chunk.normalized_text


def test_unknown_model_citation_ids_are_repaired() -> None:
    citation = create_citations(
        "When is payment due?",
        [
            CandidateChunk(
                chunk_id="chunk_0000",
                document_id=uuid4(),
                chunk_index=0,
                text="Payment. Invoices are due within thirty days.",
                normalized_text="Payment. Invoices are due within thirty days.",
                detected_heading="Payment",
                source_locators=[DocxSourceLocator(section_number=1, paragraph_start=1, paragraph_end=1)],
                char_count=44,
                token_count_estimate=7,
                splitter_strategy="structural",
            )
        ],
        [RetrievalResult(chunk_id="chunk_0000", score=0.8, rank=1)],
    )[0]
    repaired = validate_or_repair_response(
        ModelQAResponse(answer="Invoices are due within thirty days. [made_up]", citation_ids=["made_up"], confidence="high"),
        [citation],
        "Invoices are due within thirty days. [cit_0000]",
    )

    assert repaired.refused is False
    assert repaired.citations[0].citation_id == "cit_0000"


def test_model_qa_response_accepts_json_contract() -> None:
    response = parse_model_qa_response(
        '```json\n{"answer":"The term renews annually unless notice is given.","citation_ids":["cit_0000"],"confidence":"high"}\n```'
    )

    assert response.answer.startswith("The term renews")
    assert response.citation_ids == ["cit_0000"]
    assert response.confidence == "high"
