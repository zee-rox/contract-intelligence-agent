# Contract Intelligence Agent

Contract Intelligence Agent is a production-oriented portfolio project for clause-aware contract analysis. It is intended to ingest PDF and DOCX contracts, preserve source locations, identify contractual clauses, assess potential risk, build a document-specific semantic index, and answer questions only when the uploaded contract provides enough evidence.

This is not legal advice software. Risk summaries are informational, should be treated as automated review assistance, and must not replace review by a qualified legal professional.

## Product Goals

The finished application will transform each uploaded contract into:

- A normalized document representation with traceable source locations.
- Candidate text spans for retrieval and clause extraction.
- Authoritative extracted clauses using a fixed clause taxonomy.
- Clause-level risk assessments with observed and missing factors.
- A per-document FAISS semantic search index.
- Grounded question-answering responses with exact citations.
- Refusals when the contract does not support an answer.
- A polished web interface for upload, analysis, citation browsing, and streamed QA.
- A reproducible evaluation harness with measured results.

The project is intentionally more than a basic "chat with PDF" app. Its defining behaviors are clause-aware processing, structured validation, risk reasoning, citation validation, refusal handling, document isolation, visible error states, and measured evaluation.

## Core Architecture

The system is planned as two separate services:

- `backend/`: FastAPI, Pydantic v2, PyMuPDF, python-docx, OCR fallback, Sentence Transformers, FAISS, LangGraph orchestration, structured logging, and pytest.
- `frontend/`: Next.js App Router, TypeScript, Tailwind CSS, shadcn/ui, React PDF, Framer Motion, Lucide React, typed HTTP clients, and SSE for streamed responses.

Backend and frontend communicate through documented HTTP and SSE contracts. The application must not be implemented as Streamlit, Gradio, or a single-process demo.

## Processing Flow

Upload and ingestion:

```text
File upload
  -> file validation
  -> document registration
  -> source persistence
  -> PDF or DOCX parsing
  -> per-page OCR fallback when required
  -> text normalization
  -> candidate span generation
  -> embedding generation
  -> document-specific FAISS index
  -> persisted document artifacts
  -> ready status
```

Clause analysis:

```text
Ready document
  -> LangGraph analysis supervisor
  -> clause extraction worker
  -> structured validation
  -> one correction attempt when invalid
  -> validated extracted clauses
  -> risk assessment worker
  -> structured validation
  -> result aggregation
  -> persisted clause analysis
```

Question answering:

```text
User question
  -> request validation
  -> question embedding
  -> document-specific retrieval
  -> retrieval confidence check
  -> QA worker
  -> citation validation
  -> streamed answer events
  -> final structured response
```

## Fixed Design Decisions

- Use one FAISS index per document. There is no shared global vector index.
- The chunking module creates candidate spans; the clause extraction worker owns authoritative clause boundaries.
- Risk assessment runs after validated clause extraction. It must not run concurrently with extraction for the same clause.
- OCR is a fallback for failed or low-quality native PDF extraction, not a default path for every page.
- All LLM providers must be accessed through a common internal interface. The initial default provider is Groq, and a llama.cpp-compatible provider is required before final evaluation.
- Retrieval thresholds start as configurable constants and are tuned through the evaluation harness.
- Evaluation claims must be produced by the repository's evaluation harness. Do not invent accuracy, citation, or refusal metrics.

## Implemented Backend Capabilities

Phases 1 and 2 are implemented for the backend:

- FastAPI application skeleton with `/health`.
- Typed environment configuration through Pydantic settings.
- Atomic per-document storage rooted at `STORAGE_ROOT`.
- PDF upload parsing with PyMuPDF and selective per-page OCR fallback hooks.
- DOCX upload parsing with paragraph locators and table row text.
- Text normalization that preserves raw extracted text separately.
- Deterministic clause-aware candidate chunking.
- Provider-independent LLM interface with a Groq provider and deterministic local provider.
- Structured clause extraction with one validation retry and heuristic fallback.
- Deterministic embedding service.
- One FAISS index per document with persisted metadata.
- LangGraph analysis supervisor that runs clause extraction before risk assessment.
- Versioned risk baseline with persisted risk explanations.
- Clause analysis API that reloads persisted analysis results on repeat requests.
- Document-specific question answering with retrieval thresholds.
- Application-owned citation IDs and exact snippet validation.
- Refusal behavior for unsupported questions.
- Prompt-injection marker filtering before citation use.
- SSE streaming for structured QA responses.
- Unit and integration tests for ingestion, chunking, extraction, indexing, and analysis.

Evaluation harnesses, frontend, Docker, structured output hardening, operational reliability work, and llama.cpp support are intentionally not implemented yet.

## Repository Structure

```text
contract-intelligence-agent/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── ingestion/
│   │   ├── chunking/
│   │   ├── retrieval/
│   │   ├── agents/
│   │   ├── llm/
│   │   ├── schemas/
│   │   ├── storage/
│   │   ├── services/
│   │   └── observability/
│   ├── tests/
│   ├── pyproject.toml
│   └── requirements.txt
└── docs/
    ├── implementation-plan.md
    └── decisions/
```

Directories should be added when their phase is implemented, not as empty placeholders.

## Backend Setup

```bash
cd backend
python -m pip install -e '.[dev]'
uvicorn app.main:app --reload
```

The API will start on `http://127.0.0.1:8000` by default.

Useful endpoints:

- `GET /health`
- `POST /documents` with a `file` upload field
- `GET /documents/{document_id}`
- `POST /documents/{document_id}/extract-clauses`
- `GET /documents/{document_id}/clauses`
- `POST /documents/{document_id}/questions`
- `GET /documents/{document_id}/questions/stream?question=...`

The default `.env.example` uses `LLM_PROVIDER=fake` so local tests and demos do not require external credentials. To use Groq, set `LLM_PROVIDER=groq` and provide `GROQ_API_KEY` or `LLM_API_KEY`.

OCR support requires system OCR tools in addition to Python packages:

- Tesseract OCR.
- Poppler utilities for `pdf2image`.

Without those system tools, native PDF extraction still works and OCR fallback records a warning instead of silently pretending OCR succeeded.

## Validation

Run the backend checks from the `backend/` directory:

```bash
python -m ruff check .
python -m mypy app
pytest
```

Current local validation:

- `python -m ruff check .`: passed.
- `python -m mypy app`: passed for 55 source files.
- `pytest`: 21 passed.

## Data And Citation Rules

- Document IDs are generated UUIDs. Storage paths must never be derived from user filenames.
- PDF page numbers are 1-based. DOCX citations use paragraph and section locators, not fake pages.
- Character offsets are 0-based half-open ranges.
- Raw source text and normalized text remain distinguishable.
- Every derived object must be traceable to the document, source span, processing stage, prompt version, model provider, and model where applicable.
- Citation snippets must be exact contiguous substrings of normalized source text, allowing only documented whitespace normalization.
- QA responses must refuse when supporting evidence is insufficient.

## Configuration Expectations

Runtime configuration will be loaded from typed environment settings. Required settings include application host/port, storage root, upload limits, CORS origins, active LLM provider and model, provider credentials, embedding model/device, retrieval thresholds, and OCR settings.

Provider-specific credentials are required only for the active provider. Secrets must never be committed; `.env.example` should contain safe placeholders.

## Development Status

Current phase: Phase 3 complete.

Future phases should leave the repository runnable and testable before moving on, and each completed phase should be committed locally and pushed to the configured remote. The next planned phase is structured output hardening and operational reliability.

## Git Workflow

Commit messages must use Conventional Commits:

```text
type(scope): subject
```

Allowed types are `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `build`, `ci`, and `revert`. Subjects should be imperative, lower than 72 characters, and must not end with a period.
