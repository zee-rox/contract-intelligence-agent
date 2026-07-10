import json
import os
import tempfile
from pathlib import Path
from typing import Any

from pydantic import BaseModel


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)


def atomic_write_json(path: Path, model_or_data: BaseModel | list[BaseModel] | dict[str, Any] | list[Any]) -> None:
    data: dict[str, Any] | list[Any]
    if isinstance(model_or_data, BaseModel):
        data = model_or_data.model_dump(mode="json")
    elif isinstance(model_or_data, list):
        data = [item.model_dump(mode="json") if isinstance(item, BaseModel) else item for item in model_or_data]
    else:
        data = model_or_data
    atomic_write_text(path, json.dumps(data, indent=2, sort_keys=True))
