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

Status: completed.

Scope:

- Question answering.
- Grounded citation validation.
- Refusal behavior.
- SSE streaming.

Completed work:

- Added QA request, response, and citation schemas.
- Added document-specific retrieval for question answering.
- Added retrieval score threshold and lexical evidence guard.
- Assigned citation IDs in application code from retrieved chunks.
- Validated citation snippets as exact substrings of normalized chunk text.
- Added one repair path for model responses that reference unknown citation IDs.
- Added refusal responses for insufficient evidence and retrieval failures.
- Added prompt-injection marker filtering before citation creation.
- Added structured `POST /documents/{document_id}/questions`.
- Added SSE `GET /documents/{document_id}/questions/stream`.
- Added API contract tests for answerable questions, absent information, prompt injection, document isolation, and SSE final events.

Validation commands:

```bash
cd backend
python -m ruff check .
python -m mypy app
pytest
```

Known limitations:

- The QA worker currently uses deterministic grounded synthesis over retrieved snippets rather than an external model prompt.
- SSE cancellation is handled by checking request disconnection before emitting each event; there is no long-running token stream yet.

## Phase 4

Status: completed.

Scope:

- Structured output hardening.
- Operational reliability.

Completed work:

- Added typed `AppError` handling and structured API error payloads.
- Added request ID middleware and request ID logging context.
- Hardened atomic writes with fsync and temporary-file cleanup.
- Added per-document in-process locks for ingestion, extraction, and analysis.
- Added index metadata artifact versioning and corrupt metadata detection.
- Added FAISS/index metadata consistency checks.
- Added bounded Groq timeout retries and concurrency limiting.
- Added secret-safe settings summaries for diagnostics.
- Ensured failed indexing leaves the document manifest in `failed`, not `ready`.
- Added tests for interrupted writes, provider timeouts, duplicate analysis requests, corrupt metadata, secret redaction, and partial indexing failure.

Validation commands:

```bash
cd backend
python -m ruff check .
python -m mypy app
pytest
```

Known limitations:

- Per-document locks are in-process and suitable for the current single-service local backend. A distributed deployment would need an external lock manager before running multiple backend workers against the same storage root.

## Phase 5

Status: completed.

Scope:

- Evaluation harness.

Completed work:

- Added versioned synthetic evaluation dataset `phase5-synthetic-v1`.
- Added human-readable annotation schemas for expected clauses, risks, questions, refusals, and OCR expectations.
- Added executable evaluation runner.
- Added clause precision/recall/F1 and boundary support metrics.
- Added risk accuracy metric.
- Added citation validity metric against cited source chunks.
- Added refusal accuracy metric.
- Added OCR metric reporting with explicit no-OCR-fixture status.
- Added performance timing.
- Added machine-readable output at `backend/eval/results/latest.json`.
- Added generated `EVAL.md` with actual results and issue details.
- Added Groq/fake/llama.cpp provider abstraction support and llama.cpp provider path test.
- Added provider comparison section that records skipped llama.cpp runs instead of inventing results.

Latest generated results:

- Clause precision: `0.8571`
- Clause recall: `0.8571`
- Clause F1: `0.8571`
- Boundary support rate: `0.8571`
- Risk accuracy: `1.0`
- Citation validity: `1.0`
- Refusal accuracy: `0.75`
- OCR evaluated pages: `0`

Validation commands:

```bash
cd backend
python -m ruff check .
python -m mypy app
pytest
python -m eval.runner
```

Known limitations:

- The current dataset is intentionally small and synthetic.
- OCR degradation is not measured yet because the Phase 5 dataset does not include a scanned fixture.
- llama.cpp comparison is skipped unless `EVAL_RUN_LLAMA_CPP=true` and `LLAMACPP_BASE_URL` are configured.

## Phase 6

Status: completed.

Scope:

- Frontend.

Completed work:

- Added Next.js App Router frontend service.
- Added typed backend API client.
- Added upload workflow with processing states.
- Added PDF viewer via React PDF with citation page highlight support.
- Added DOCX extracted-text viewer with paragraph navigation and highlight support.
- Added clause and risk summary panel.
- Added grounded chat panel using SSE.
- Added citation chips for source navigation.
- Added distinct refused-answer rendering.
- Added backend error rendering.
- Added dark mode.
- Added keyboard-accessible controls.
- Added frontend tests for upload, major UI states, supported and refused questions, citation navigation, backend errors, keyboard dark mode, and critical accessibility violations.

Validation commands:

```bash
cd frontend
npm run lint
npm run typecheck
npm test
npm run build
```

Known limitations:

- Frontend tests mock backend responses and EventSource streams; end-to-end browser tests against a live backend are deferred.
- `npm audit --omit=dev` reports a remaining moderate Next/PostCSS advisory whose suggested automatic fix is a breaking downgrade.

## Phase 7

Status: completed.

Scope:

- Docker.
- Documentation.
- Final polish.

Completed work:

- Added backend Dockerfile with OCR system dependencies (`tesseract-ocr`, `tesseract-ocr-eng`, `poppler-utils`).
- Added frontend Dockerfile with production Next.js startup.
- Added Docker Compose with backend and frontend services, health checks, and a persistent `backend-storage` volume.
- Added Docker build ignores for backend and frontend.
- Updated `.env.example` with CORS and frontend API settings.
- Rewrote the root README as a traditional GitHub project README.
- Added architecture documentation.
- Added evaluation documentation.
- Added final security review documentation.
- Included design screenshots as README project screenshots.

Validation commands:

```bash
cd backend
python -m ruff check .
python -m mypy app
pytest
python -m eval.runner

cd ../frontend
npm run lint
npm run typecheck
npm test
npm run build

cd ..
docker compose config
docker compose build
```

Known limitations:

- Docker Compose is intended for local portfolio/demo use and is not hardened for public internet deployment.
- Frontend dependency audit advisories remain documented; forced automatic remediation would require breaking dependency changes.
