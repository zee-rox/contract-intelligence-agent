import hashlib
from typing import cast

import numpy as np
from numpy.typing import NDArray


class HashEmbeddingService:
    def __init__(self, model_name: str, dimension: int) -> None:
        self.model_name = model_name
        self.dimension = dimension

    def embed_texts(self, texts: list[str]) -> NDArray[np.float32]:
        vectors = np.zeros((len(texts), self.dimension), dtype=np.float32)
        for row, text in enumerate(texts):
            for token in text.lower().split():
                digest = hashlib.sha256(token.encode("utf-8")).digest()
                index = int.from_bytes(digest[:4], "big") % self.dimension
                sign = 1.0 if digest[4] % 2 == 0 else -1.0
                vectors[row, index] += sign
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return cast(NDArray[np.float32], vectors / norms)

    def embed_query(self, text: str) -> NDArray[np.float32]:
        return self.embed_texts([text])
