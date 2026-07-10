import json
import os
import tempfile
from pathlib import Path
from typing import Any

from pydantic import BaseModel


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as tmp:
            tmp.write(content)
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp_path = Path(tmp.name)
        os.replace(tmp_path, path)
        directory_fd = os.open(path.parent, os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except Exception:
        if tmp_path is not None and tmp_path.exists():
            tmp_path.unlink()
        raise


def atomic_write_json(path: Path, model_or_data: BaseModel | list[BaseModel] | dict[str, Any] | list[Any]) -> None:
    data: dict[str, Any] | list[Any]
    if isinstance(model_or_data, BaseModel):
        data = model_or_data.model_dump(mode="json")
    elif isinstance(model_or_data, list):
        data = [item.model_dump(mode="json") if isinstance(item, BaseModel) else item for item in model_or_data]
    else:
        data = model_or_data
    atomic_write_text(path, json.dumps(data, indent=2, sort_keys=True))
