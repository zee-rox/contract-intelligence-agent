# Implementation Plan

## Phase 1

Status: in progress.

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
pytest
```

## Phase 2

Status: not started.

Scope:

- Embeddings.
- One FAISS index per document.
- Retrieval metadata.
- LangGraph analysis flow.
- Risk assessment.
- Clause API.
