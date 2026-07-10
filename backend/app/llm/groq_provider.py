import json

import httpx

from app.config import Settings
from app.llm.errors import LLMProviderError
from app.llm.interface import LLMMessage, LLMResponse


class GroqProvider:
    provider_name = "groq"

    def __init__(self, settings: Settings) -> None:
        self.model = settings.llm_model
        self.api_key = settings.active_llm_api_key
        self.base_url = settings.llm_base_url or "https://api.groq.com/openai/v1"
        self.timeout = settings.llm_timeout_seconds
        if not self.api_key:
            raise LLMProviderError("GROQ_API_KEY or LLM_API_KEY is required for Groq")

    def generate(self, messages: list[LLMMessage], *, temperature: float = 0.0) -> LLMResponse:
        payload = {
            "model": self.model,
            "messages": [message.model_dump() for message in messages],
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }
        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            content=json.dumps(payload),
            timeout=self.timeout,
        )
        if response.status_code >= 400:
            raise LLMProviderError(f"Groq request failed with status {response.status_code}")
        data = response.json()
        return LLMResponse(content=data["choices"][0]["message"]["content"], provider=self.provider_name, model=self.model)
