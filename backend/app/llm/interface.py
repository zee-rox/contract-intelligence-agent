from typing import Protocol

from pydantic import BaseModel


class LLMMessage(BaseModel):
    role: str
    content: str


class LLMResponse(BaseModel):
    content: str
    provider: str
    model: str


class LLMProvider(Protocol):
    provider_name: str
    model: str

    def generate(self, messages: list[LLMMessage], *, temperature: float = 0.0) -> LLMResponse:
        ...
