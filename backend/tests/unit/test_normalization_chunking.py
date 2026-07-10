from uuid import uuid4

from app.chunking.service import create_candidate_chunks
from app.ingestion.normalization import normalize_text
from app.schemas.documents import ExtractedParagraph
from app.schemas.sources import DocxSourceLocator


def test_normalization_preserves_meaningful_terms() -> None:
    text = "Payment   Terms\r\nThe Client shall not withhold $1,000.\x00"
    assert normalize_text(text) == "Payment Terms\nThe Client shall not withhold $1,000."


def test_candidate_chunks_are_deterministic() -> None:
    document_id = uuid4()
    paragraph = ExtractedParagraph(
        paragraph_number=1,
        section_number=1,
        style_name="Heading 1",
        raw_text="Termination\nEither party may terminate on thirty days notice.",
        normalized_text="Termination\nEither party may terminate on thirty days notice.",
        source_locator=DocxSourceLocator(section_number=1, paragraph_start=1, paragraph_end=1),
    )
    first = create_candidate_chunks(document_id, [], [paragraph])
    second = create_candidate_chunks(document_id, [], [paragraph])
    assert [chunk.chunk_id for chunk in first] == [chunk.chunk_id for chunk in second]
    assert first[0].detected_heading == "Termination\nEither party may terminate on thirty days notice."
