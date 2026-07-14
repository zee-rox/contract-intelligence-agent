# Architecture

Contract Intelligence Agent is a two-service application:

- `backend`: FastAPI API for ingestion, storage, analysis, retrieval, and grounded QA.
- `frontend`: Next.js App Router UI for upload, document review, clause/risk browsing, and streamed questions.

The services communicate over documented HTTP and SSE contracts. Docker Compose runs them together and persists backend artifacts in a named local volume.

## Runtime Flow

```text
Upload
  -> validation
  -> source persistence
  -> PDF/DOCX parsing
  -> selective OCR fallback
  -> normalization
  -> candidate chunking
  -> document-specific embeddings
  -> document-specific FAISS index
  -> ready document
```

```text
Ready document
  -> LangGraph analysis supervisor
  -> clause extraction
  -> structured validation and repair attempt
  -> risk assessment
  -> persisted clause analysis
```

```text
Question
  -> request validation
  -> document-specific retrieval
  -> evidence threshold checks
  -> grounded answer or refusal
  -> application-created citations
  -> HTTP or SSE response
```

## Backend Modules

- `app/api`: FastAPI routers and structured error handling.
- `app/ingestion`: file validation, PDF/DOCX parsing, OCR fallback, normalization, and quality reports.
- `app/chunking`: deterministic candidate span generation.
- `app/retrieval`: deterministic embeddings, FAISS persistence, metadata validation, and search.
- `app/agents`: clause extraction, risk assessment, QA, and LangGraph supervision.
- `app/llm`: provider-independent LLM interface plus fake, Groq, OpenRouter, and llama.cpp-compatible providers.
- `app/storage`: deterministic paths, atomic writes, repository loading, and per-document locks.
- `eval`: versioned dataset, metrics, runner, and report generation.

## Frontend Modules

- `app`: Next.js root layout and route.
- `features/workspace`: contract workspace controller, document viewer, analysis pane, chat, citations, skeletons, and upload states.
- `lib/api.ts`: typed backend client and SSE URL helper.
- `types/api.ts`: TypeScript mirrors of backend API models.
- `components/ui`: small shared button, badge, and panel primitives.

## Persistence

Backend artifacts live under `STORAGE_ROOT/{document_id}`:

```text
manifest.json
source/original.pdf|docx
extracted/pages.json|paragraphs.json
chunks/chunks.json
index/index.faiss
index/metadata.json
analysis/clauses.json
analysis/risks.json
analysis/analysis-manifest.json
```

All critical JSON writes go through atomic write helpers. The Compose stack maps `/app/storage` to a named Docker volume.

## Fixed Design Decisions

- One FAISS index per document.
- Chunking proposes candidate spans; clause extraction owns final clause boundaries.
- Risk assessment runs only after validated clause extraction.
- OCR runs only for low-quality PDF pages or extraction failures.
- Business logic depends on an internal LLM interface, not provider SDK response objects.
- Unsupported answers are refused instead of guessed.

## Deployment Shape

`docker-compose.yml` builds:

- `backend` on port `8000`, with OCR system dependencies and `/health` health checks.
- `frontend` on port `3000`, built with `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`.
- `backend-storage` named volume for persisted documents, chunks, indexes, and analysis outputs.
