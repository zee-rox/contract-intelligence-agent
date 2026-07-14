import logging
from threading import BoundedSemaphore

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import Settings
from app.llm.errors import LLMProviderError
from app.llm.interface import LLMMessage, LLMResponse

logger = logging.getLogger(__name__)


class GeminiProvider:
    provider_name = "gemini"

    def __init__(self, settings: Settings) -> None:
        self.model = settings.llm_model
        self.api_key = settings.active_llm_api_key
        self.timeout = settings.llm_timeout_seconds
        self.max_retries = settings.llm_max_retries
        self.project = settings.google_cloud_project
        self.location = settings.google_cloud_location
        self.vertexai = settings.google_genai_use_vertexai
        self._semaphore = BoundedSemaphore(settings.llm_max_concurrency)
        if not self.api_key and not self.vertexai:
            raise LLMProviderError("GOOGLE_API_KEY, GEMINI_API_KEY, or LLM_API_KEY is required for Gemini")

    def generate(self, messages: list[LLMMessage], *, temperature: float = 0.0) -> LLMResponse:
        chat = self._build_chat_model(temperature)
        langchain_messages = [self._to_langchain_message(message) for message in messages]
        last_error: Exception | None = None
        with self._semaphore:
            for _attempt in range(self.max_retries + 1):
                try:
                    response = chat.invoke(langchain_messages)
                    break
                except TimeoutError as exc:
                    last_error = exc
            else:
                raise LLMProviderError("Gemini request timed out after bounded retries") from last_error
        content = self._response_text(response)
        logger.info("Gemini response received chars=%s", len(content))
        return LLMResponse(content=content, provider=self.provider_name, model=self.model)

    def _build_chat_model(self, temperature: float) -> ChatGoogleGenerativeAI:
        kwargs: dict[str, object] = {
            "model": self.model,
            "temperature": temperature,
            "timeout": self.timeout,
            "max_retries": 0,
            "vertexai": self.vertexai,
        }
        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.project:
            kwargs["project"] = self.project
        if self.location:
            kwargs["location"] = self.location
        return ChatGoogleGenerativeAI(**kwargs)

    def _to_langchain_message(self, message: LLMMessage) -> BaseMessage:
        if message.role == "system":
            return SystemMessage(content=message.content)
        return HumanMessage(content=message.content)

    def _response_text(self, response: object) -> str:
        text = getattr(response, "text", None)
        if isinstance(text, str) and text:
            return text
        content = getattr(response, "content", "")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(block.get("text", "") for block in content if isinstance(block, dict))
        return str(content)
