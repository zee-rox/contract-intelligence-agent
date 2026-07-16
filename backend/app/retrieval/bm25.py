import math
import re
from collections import Counter

from app.schemas.chunks import CandidateChunk


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.casefold())


def rank_chunks(question: str, chunks: list[CandidateChunk], top_k: int) -> list[tuple[str, float]]:
    """Return a deterministic lexical ranking to complement dense retrieval."""
    query = _tokens(question)
    if not query or not chunks:
        return []
    documents = [_tokens(chunk.normalized_text) for chunk in chunks]
    document_frequency = Counter(token for tokens in documents for token in set(tokens))
    average_length = sum(len(tokens) for tokens in documents) / len(documents)
    scored: list[tuple[str, float]] = []
    for chunk, tokens in zip(chunks, documents):
        frequencies = Counter(tokens)
        score = 0.0
        for token in query:
            frequency = frequencies[token]
            if not frequency:
                continue
            inverse_frequency = math.log(1 + (len(documents) - document_frequency[token] + 0.5) / (document_frequency[token] + 0.5))
            length_norm = 1 - 0.75 + 0.75 * len(tokens) / max(average_length, 1)
            score += inverse_frequency * (frequency * 2.2) / (frequency + 1.2 * length_norm)
        scored.append((chunk.chunk_id, score))
    return sorted(scored, key=lambda item: item[1], reverse=True)[:top_k]
