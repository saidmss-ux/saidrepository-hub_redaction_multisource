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
