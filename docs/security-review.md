# Security Review

This review records the Phase 7 security and error-handling posture.

## Upload Safety

- Documents are identified by generated UUIDs, not user filenames.
- Original filenames are sanitized before persistence.
- File extension, content type, file signature, emptiness, upload size, corrupt PDFs, encrypted PDFs, invalid DOCX packages, and unsupported types are rejected with structured errors.
- `MAX_UPLOAD_SIZE_MB` is configurable and defaults to `25`.

## Storage Safety

- Backend storage paths are resolved under the configured `STORAGE_ROOT`.
- Critical artifacts are written atomically.
- Per-document locks protect operations that mutate document artifacts.
- Docker Compose stores artifacts in a named local volume instead of the image filesystem.

## Secret Handling

- No real secrets are present in `.env.example`.
- Provider credentials are read from environment variables.
- Only the active provider requires credentials.
- Settings summaries redact secret values.
- `.env` files are ignored by Docker build contexts.

## Network Surface

- Backend exposes `8000`.
- Frontend exposes `3000`.
- CORS origins are configured through `ALLOWED_ORIGINS`.
- Compose health checks call local service endpoints only.

## Model And Grounding Safety

- QA retrieves from the active document's own index.
- Citation IDs are created by application code.
- Unsupported questions are refused when evidence is insufficient.
- The app is informational and not legal advice.

## Remaining Risks

- Local Docker Compose is not hardened for internet exposure.
- There is no authentication or multi-user isolation; the project is intentionally scoped as a local portfolio application.
- OCR quality depends on system packages and source document quality.
- The frontend dependency audit currently reports upstream advisories; automatic forced remediation would require breaking dependency changes and was not applied in Phase 7.
