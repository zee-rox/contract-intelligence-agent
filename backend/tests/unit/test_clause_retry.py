import json
from uuid import uuid4

from app.agents import clause_extraction
from app.agents.clause_extraction import extract_clauses_single_pass
from app.config import Settings
from app.llm.interface import LLMMessage, LLMResponse
from app.schemas.chunks import CandidateChunk
from app.schemas.sources import DocxSourceLocator


class InvalidThenValidProvider:
    provider_name = "test"
    model = "retry-model"

    def __init__(self) -> None:
        self.calls = 0

    def generate(self, messages: list[LLMMessage], *, temperature: float = 0.0) -> LLMResponse:
        self.calls += 1
        if self.calls == 1:
            return LLMResponse(content="{not-json", provider=self.provider_name, model=self.model)
        return LLMResponse(
            content=json.dumps(
                {
                    "clauses": [
                        {
                            "clause_type": "confidentiality",
                            "clause_heading": "Confidentiality",
                            "clause_text": "Confidentiality. The parties shall protect information.",
                            "source_chunk_ids": ["chunk_0000"],
                            "confidence": "high",
                        }
                    ]
                }
            ),
            provider=self.provider_name,
            model=self.model,
        )


def test_invalid_llm_output_gets_one_correction_attempt(monkeypatch, tmp_path) -> None:
    provider = InvalidThenValidProvider()
    monkeypatch.setattr(clause_extraction, "build_llm_provider", lambda settings: provider)
    document_id = uuid4()
    chunk = CandidateChunk(
        chunk_id="chunk_0000",
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

    result = extract_clauses_single_pass(document_id, [chunk], Settings(storage_root=tmp_path))

    assert provider.calls == 2
    assert result.fallback_used is False
    assert result.clauses[0].confidence == "high"
