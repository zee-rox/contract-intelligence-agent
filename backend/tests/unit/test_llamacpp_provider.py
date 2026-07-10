import json

from app.config import Settings
from app.llm.factory import build_llm_provider
from app.llm.interface import LLMMessage


def test_llamacpp_provider_uses_openai_compatible_chat_endpoint(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class Response:
        status_code = 200

        def json(self):
            return {"choices": [{"message": {"content": "{\"clauses\": []}"}}]}

    def fake_post(url, headers, content, timeout):
        captured["url"] = url
        captured["headers"] = headers
        captured["content"] = json.loads(content)
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr("app.llm.llamacpp_provider.httpx.post", fake_post)
    provider = build_llm_provider(
        Settings(llm_provider="llamacpp", llamacpp_base_url="http://localhost:8080/v1", llm_model="local-model")
    )

    response = provider.generate([LLMMessage(role="user", content="hello")])

    assert captured["url"] == "http://localhost:8080/v1/chat/completions"
    assert captured["content"]["model"] == "local-model"
    assert response.provider == "llamacpp"
