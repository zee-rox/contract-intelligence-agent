from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app


def test_health_endpoint() -> None:
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_rejects_invalid_file(tmp_path, monkeypatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
    client = TestClient(create_app())
    response = client.post("/documents", files={"file": ("bad.txt", b"hello", "text/plain")})
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "unsupported_file_type"
    get_settings.cache_clear()
