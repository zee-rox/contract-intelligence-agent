import json
from typing import Any, cast

from app.config import Settings
from app.llm.factory import build_llm_provider
from app.llm.interface import LLMMessage


def test_openrouter_provider_uses_openai_compatible_chat_endpoint(monkeypatch: Any) -> None:
    captured: dict[str, object] = {}

    class Response:
        status_code = 200

        def json(self) -> dict[str, list[dict[str, dict[str, str]]]]:
            return {"choices": [{"message": {"content": "{\"clauses\": []}"}}]}

    def fake_post(url: str, headers: dict[str, str], content: str, timeout: float) -> Response:
        captured["url"] = url
        captured["headers"] = headers
        captured["content"] = json.loads(content)
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr("app.llm.openrouter_provider.httpx.post", fake_post)
    provider = build_llm_provider(
        Settings(
            llm_provider="openrouter",
            openrouter_api_key="test-key",
            llm_model="openai/gpt-4o-mini",
            openrouter_http_referer="https://example.test",
        )
    )

    response = provider.generate([LLMMessage(role="user", content="hello")])

    headers = cast(dict[str, str], captured["headers"])
    content = cast(dict[str, object], captured["content"])
    assert captured["url"] == "https://openrouter.ai/api/v1/chat/completions"
    assert content["model"] == "openai/gpt-4o-mini"
    assert headers["Authorization"] == "Bearer test-key"
    assert headers["HTTP-Referer"] == "https://example.test"
    assert headers["X-Title"] == "Contract Intelligence Agent"
    assert response.provider == "openrouter"
