# Backend API (DocuHub MVP)

## Base URL
- Prefix: `/api/v1`

## Response Contract (BaseResponse)
All endpoints return:

```json
{
  "success": true,
  "data": {},
  "error": null
}
```

On functional/system error:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "string",
    "message": "string",
    "details": {}
  }
}
```

## Error Codes (current)
- `validation_error`
- `internal_error`
- `unsupported_file_type`
- `upload_too_large`
- `invalid_url_scheme`
- `invalid_url`
- `blocked_host`
- `dns_resolution_failed`
- `blocked_private_network`
- `network_http_error`
- `network_url_error`
- `network_timeout`
- `file_not_found`
- `extract_timeout`
- `api_key_disabled`

## Endpoints
- `GET /health`
- `POST /upload`
- `POST /download-from-url`
- `POST /extract`
- `GET /sources`
- `GET /source/{file_id}`
- `POST /video-to-text`
- `POST /ai-assist`

## Frontend Integration Notes
- Use `success` as the canonical state flag.
- On `success=false`, read and render `error.message` for UI feedback.
- Optionally map `error.code` to localized frontend messages.
- Loading state should be driven per request lifecycle; clear on any response because contract is always returned.


## API Versioning Freeze
- Current public version: `v1` with strict prefix `/api/v1`.
- Future migration path: reserve `v2` namespace without breaking `v1` contracts.

## Observability
- Structured JSON logs are emitted for request lifecycle and service operations.
- `x-request-id` is accepted from client or auto-generated and returned in responses.
- Logged events include:
  - business errors (`service_error`)
  - system errors (`internal_error`)
  - extraction duration (`extract_done.elapsed_ms`)
  - upload/download size metadata (`upload_chars`, `bytes_previewed`)

## Resilience
- Configurable concurrency guard via `CONCURRENCY_LIMIT`.
- When capacity is exhausted, API returns contractual error with code `over_capacity` (HTTP 503).


## Product Layer (SoT-aligned)
Product domain entities introduced without breaking `/api/v1` contract:
- `Project`
- `Document` (project -> source linkage)
- `BatchRun` / `BatchItem` (multi-document extraction orchestration)

New additive endpoints:
- `POST /projects`
- `GET /projects`
- `POST /projects/{project_id}/documents`
- `GET /projects/{project_id}/documents`
- `POST /projects/{project_id}/batches/extract`

All responses remain wrapped in `BaseResponse`.


## Environment Strategy
- `local`: SQLite, `DEBUG=true` allowed.
- `staging`: PostgreSQL required, `DEBUG=false`.
- `production`: PostgreSQL required, `DEBUG=false`.

Environment files:
- `.env.local`
- `.env.staging`
- `.env.production`

## Deployment & Rollback
- CI blocks integration when backend/frontend tests fail.
- Staging deploy is branch-driven (`staging`).
- Production deploy is controlled by `main` or version tags (`v*`).
- Rollback strategy: redeploy previous stable image tag and keep DB migration trail in `schema_migrations`.
