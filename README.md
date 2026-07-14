# Contract Intelligence Agent

Contract Intelligence Agent is a clause-aware contract review workspace for PDF and DOCX agreements. It ingests a contract, preserves source locations, extracts contractual clauses, assesses clause-level risk, builds a document-specific FAISS retrieval index, and answers questions using only evidence found in the uploaded document.

This is a production-oriented portfolio project, not legal advice software. Risk summaries are informational and should not replace qualified legal review.

## Highlights

- Upload PDF and DOCX contracts through a polished two-pane web workspace.
- Preserve PDF page and DOCX paragraph citations for every material answer.
- Extract clauses into a fixed taxonomy, then run clause-level risk assessment.
- Use one FAISS index per document to avoid cross-document leakage.
- Refuse unsupported questions instead of guessing.
- Stream grounded question-answering responses over Server-Sent Events.
- Run a reproducible evaluation harness with actual measured results.
- Start the full stack with Docker Compose using a persistent local storage volume.

## Screenshots

<p>
  <img src="docs/designs/Desktop%20%E2%80%A2%20Ready.png" alt="Ready contract review workspace" width="31%" />
  <img src="docs/designs/Desktop%20%E2%80%A2%20Processing.png" alt="Processing state" width="31%" />
  <img src="docs/designs/Desktop%20%E2%80%A2%20Empty.png" alt="Empty upload state" width="31%" />
</p>

## How It Works

The backend is a FastAPI service that validates uploads, extracts text with source locations, selectively falls back to OCR for weak PDF pages, chunks candidate spans, creates a per-document FAISS index, extracts clauses, assesses risks, and answers grounded questions.

The frontend is a Next.js App Router application with a responsive document viewer, clause summary, risk badges, streamed chat, citation chips, and mobile document/analysis tabs.

The default local model provider is `fake`, which makes the project runnable and testable without external credentials. Gemini, OpenRouter, and llama.cpp-compatible OpenAI-style providers are supported through configuration.

## Quick Start With Docker

Prerequisites:

- Docker and Docker Compose.
- Optional: a Google Gemini or OpenRouter API key, or a running llama.cpp-compatible server, if you want a real LLM provider.

Start the full stack:

```bash
cp .env.example .env
docker compose up --build
```

Open the app:

- Frontend: http://localhost:3000
- Backend health check: http://localhost:8000/health
- Backend OpenAPI docs: http://localhost:8000/docs

Uploaded documents and generated artifacts are stored in the named Docker volume `contract_intelligence_agent_backend-storage`.

To stop the stack:

```bash
docker compose down
```

To remove persisted uploaded documents and indexes:

```bash
docker compose down -v
```

## Local Development

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e ".[dev]"
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev -- --hostname 127.0.0.1 --port 3000
```

For local OCR outside Docker, install system packages:

- `tesseract-ocr`
- `tesseract-ocr-eng`
- `poppler-utils`

## Configuration

Copy `.env.example` to `.env` before running Docker Compose.

Important settings:

| Variable | Purpose |
| --- | --- |
| `LLM_PROVIDER` | `fake`, `gemini`, `openrouter`, or `llamacpp`. |
| `GOOGLE_API_KEY` / `GEMINI_API_KEY` / `LLM_API_KEY` | Secret used when `LLM_PROVIDER=gemini`. |
| `GOOGLE_GENAI_USE_VERTEXAI` | Set to `true` to use Gemini through Vertex AI. |
| `GOOGLE_CLOUD_PROJECT` | Google Cloud project used for Vertex AI. |
| `GOOGLE_CLOUD_LOCATION` | Google Cloud region for Vertex AI, defaulting to `us-central1`. |
| `OPENROUTER_API_KEY` | OpenRouter key used when `LLM_PROVIDER=openrouter`. |
| `OPENROUTER_BASE_URL` | OpenRouter OpenAI-compatible API base URL. |
| `LLAMACPP_BASE_URL` | OpenAI-compatible llama.cpp base URL. |
| `STORAGE_ROOT` | Backend artifact storage location. Compose overrides this to `/app/storage`. |
| `ALLOWED_ORIGINS` | JSON array of frontend origins allowed by CORS. |
| `NEXT_PUBLIC_API_BASE_URL` | Browser-visible backend URL for the frontend. |
| `OCR_ENABLED` | Enables selective OCR fallback. |

Do not commit real secrets. `.env.example` contains safe placeholders only.

Gemini example:

```env
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-flash
GOOGLE_API_KEY=your_google_ai_api_key_here
```

Vertex AI example:

```env
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-flash
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
```

OpenRouter example:

```env
LLM_PROVIDER=openrouter
LLM_MODEL=openai/gpt-4o-mini
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

## API Overview

Core endpoints:

- `GET /health`
- `POST /documents`
- `GET /documents/{document_id}`
- `POST /documents/{document_id}/extract-clauses`
- `GET /documents/{document_id}/clauses`
- `POST /documents/{document_id}/questions`
- `GET /documents/{document_id}/questions/stream?question=...`

HTTP responses use typed Pydantic schemas. Streamed answers use Server-Sent Events for answer deltas, citations, refusals, final payloads, and errors.

## Evaluation

Run the reproducible evaluation harness:

```bash
cd backend
python -m eval.runner
```

The command writes:

- Human-readable results: generated locally with `python -m eval.runner`.
- Machine-readable results: `backend/eval/results/latest.json`

Latest checked-in results from dataset `phase5-synthetic-v1`:

| Metric | Value |
| --- | ---: |
| Clause F1 | 0.8571 |
| Risk accuracy | 1.0 |
| Citation validity | 1.0 |
| Refusal accuracy | 0.75 |
| OCR evaluated pages | 0 |

See [docs/evaluation.md](docs/evaluation.md) for details and known limitations.

## Validation

Backend:

```bash
cd backend
python -m ruff check .
python -m mypy app
pytest
python -m eval.runner
```

Frontend:

```bash
cd frontend
npm run lint
npm run typecheck
npm test
npm run build
```

Docker:

```bash
cp .env.example .env
docker compose up --build
docker compose ps
```

## Architecture Notes

- Backend and frontend are separate services.
- Each document gets its own FAISS index.
- Chunking creates candidate spans; clause extraction owns final clause boundaries.
- Risk assessment runs after validated clause extraction.
- OCR is a fallback, not the default path for every PDF.
- LLM integrations go through a provider abstraction.
- Stored artifacts are written atomically under a per-document storage layout.

Read more in [docs/architecture.md](docs/architecture.md).

## Security And Data Handling

- Uploaded filenames are sanitized; storage paths are generated from UUIDs.
- Upload size, file type, file signature, corrupt files, encrypted PDFs, and invalid DOCX files are validated.
- Secrets are loaded from environment variables and redacted from settings summaries.
- CORS origins are explicit.
- The default `fake` provider avoids requiring credentials for local demos.
- Docker uses a named local volume for persistent artifacts.

See [docs/security-review.md](docs/security-review.md) for the final Phase 7 review.

## Project Status

Completed phases:

- Phase 1: backend ingestion foundation.
- Phase 2: embeddings, FAISS, analysis flow, risk, and clauses API.
- Phase 3: grounded QA, citations, refusal handling, and SSE.
- Phase 4: structured-output hardening and reliability.
- Phase 5: evaluation harness.
- Phase 6: frontend workspace.
- Phase 7: Docker, documentation, and final polish.

## License

No license has been declared yet. Treat the code as all rights reserved until a license is added.
