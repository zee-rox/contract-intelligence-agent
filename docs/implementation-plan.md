# Implementation Plan

## Phase 1

Status: completed.

Scope:

- Backend FastAPI skeleton.
- Typed settings.
- Storage layout.
- PDF and DOCX ingestion.
- Selective OCR fallback.
- Text normalization.
- Clause-aware candidate chunking.
- Provider-independent LLM interface.
- Groq provider.
- Structured clause extraction with deterministic fallback.
- Unit and integration tests.

Validation commands:

```bash
cd backend
python -m ruff check .
python -m mypy app
pytest
```

## Phase 2

Status: completed.

Scope:

- Embeddings.
- One FAISS index per document.
- Retrieval metadata.
- LangGraph analysis flow.
- Risk assessment.
- Clause API.

Completed work:

- Added deterministic embedding service and per-document FAISS persistence.
- Persisted index metadata mapping FAISS positions to chunk IDs.
- Built index during document ingestion before setting documents to `ready`.
- Added LangGraph supervisor with extraction followed by risk assessment.
- Added risk baseline v1 with explicit observed and missing factors.
- Persisted clauses, risks, and analysis manifests.
- Added `GET /documents/{document_id}/clauses`.
- Added tests for index reload, document isolation, analysis persistence, and risk output.

Validation commands:

```bash
cd backend
python -m ruff check .
python -m mypy app
pytest
```

Known limitations:

- Embeddings are deterministic hash embeddings for reproducible local development; Sentence Transformers is pinned for later model-backed embedding work.
- The local fake LLM provider is deterministic and intended for tests/demos, not production-quality extraction.
- Risk assessment is a conservative baseline, not jurisdiction-specific legal analysis.

## Phase 3

Status: not started.

Scope:

- Question answering.
- Grounded citation validation.
- Refusal behavior.
- SSE streaming.
