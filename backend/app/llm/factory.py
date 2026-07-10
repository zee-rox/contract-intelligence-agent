import json

from app.config import Settings
from app.llm.groq_provider import GroqProvider
from app.llm.interface import LLMMessage, LLMProvider, LLMResponse


class FakeProvider:
    provider_name = "fake"
    model = "deterministic-clause-heuristic"

    def generate(self, messages: list[LLMMessage], *, temperature: float = 0.0) -> LLMResponse:
        text = "\n".join(message.content for message in messages)
        clauses = []
        for heading, clause_type in [
            ("Termination", "termination"),
            ("Confidentiality", "confidentiality"),
            ("Payment", "payment_terms"),
            ("Governing Law", "governing_law"),
            ("Liability", "liability"),
            ("Indemnification", "indemnification"),
            ("Force Majeure", "force_majeure"),
        ]:
            if heading.lower() in text.lower():
                clauses.append(
                    {
                        "clause_type": clause_type,
                        "clause_heading": heading,
                        "clause_text": heading,
                        "source_chunk_ids": [],
                        "confidence": "low",
                        "extraction_notes": "detected by deterministic fake provider",
                    }
                )
        return LLMResponse(content=json.dumps({"clauses": clauses}), provider=self.provider_name, model=self.model)


def build_llm_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "groq":
        return GroqProvider(settings)
    return FakeProvider()
