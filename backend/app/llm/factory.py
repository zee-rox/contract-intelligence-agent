import json
import re

from app.config import Settings
from app.llm.gemini_provider import GeminiProvider
from app.llm.interface import LLMMessage, LLMProvider, LLMResponse
from app.llm.llamacpp_provider import LlamaCppProvider
from app.llm.openrouter_provider import OpenRouterProvider


class FakeProvider:
    provider_name = "fake"
    model = "deterministic-clause-heuristic"

    def generate(self, messages: list[LLMMessage], *, temperature: float = 0.0) -> LLMResponse:
        text = "\n".join(message.content for message in messages)
        chunk_blocks = re.findall(r"\[(chunk_[^\]]+)\]\n(.*?)(?=\n\n\[chunk_|\Z)", text, flags=re.DOTALL)
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
            matching_block = next(
                ((chunk_id, chunk_text.strip()) for chunk_id, chunk_text in chunk_blocks if heading.lower() in chunk_text.lower()),
                None,
            )
            if matching_block:
                chunk_id, chunk_text = matching_block
                clauses.append(
                    {
                        "clause_type": clause_type,
                        "clause_heading": heading,
                        "clause_text": chunk_text,
                        "source_chunk_ids": [chunk_id],
                        "confidence": "medium",
                        "extraction_notes": "detected by deterministic fake provider",
                    }
                )
        return LLMResponse(content=json.dumps({"clauses": clauses}), provider=self.provider_name, model=self.model)


def build_llm_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "gemini":
        return GeminiProvider(settings)
    if settings.llm_provider == "openrouter":
        return OpenRouterProvider(settings)
    if settings.llm_provider == "llamacpp":
        return LlamaCppProvider(settings)
    return FakeProvider()
