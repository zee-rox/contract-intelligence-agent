import json
from threading import BoundedSemaphore

import httpx

from app.config import Settings
from app.llm.errors import LLMProviderError
from app.llm.interface import LLMMessage, LLMResponse


class OpenRouterProvider:
    provider_name = "openrouter"

    def __init__(self, settings: Settings) -> None:
        self.model = settings.llm_model
        self.api_key = settings.active_llm_api_key
        self.base_url = (settings.llm_base_url or settings.openrouter_base_url).rstrip("/")
        self.timeout = settings.llm_timeout_seconds
        self.max_retries = settings.llm_max_retries
        self.http_referer = settings.openrouter_http_referer
        self.app_title = settings.openrouter_app_title
        self._semaphore = BoundedSemaphore(settings.llm_max_concurrency)
        if not self.api_key:
            raise LLMProviderError("OPENROUTER_API_KEY or LLM_API_KEY is required for OpenRouter")

    def generate(self, messages: list[LLMMessage], *, temperature: float = 0.0) -> LLMResponse:
        payload = {
            "model": self.model,
            "messages": [message.model_dump() for message in messages],
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Title": self.app_title,
        }
        if self.http_referer:
            headers["HTTP-Referer"] = self.http_referer

        last_error: Exception | None = None
        with self._semaphore:
            for _attempt in range(self.max_retries + 1):
                try:
                    response = httpx.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        content=json.dumps(payload),
                        timeout=self.timeout,
                    )
                    break
                except httpx.TimeoutException as exc:
                    last_error = exc
            else:
                raise LLMProviderError("OpenRouter request timed out after bounded retries") from last_error
        if response.status_code >= 400:
            raise LLMProviderError(f"OpenRouter request failed with status {response.status_code}")
        data = response.json()
        return LLMResponse(content=data["choices"][0]["message"]["content"], provider=self.provider_name, model=self.model)
