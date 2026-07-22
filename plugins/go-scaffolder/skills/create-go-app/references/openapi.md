# OpenAPI / Swagger UI (api type only)

Generated `api` services use [huma v2](https://github.com/danielgtaylor/huma) — handler funcs are framework-agnostic; the OpenAPI 3.1 spec is derived from input/output struct types in `{entity}_dto.go` (no annotation drift). The framework adapter (`humagin`/`humachi`/`humaecho`/`humamux`/`humago`) is constructed in `cmd/{name}/main.go` based on the `http_framework` parameter.

## Endpoints

Gated by `DOCS_ENABLED=true` — default false, intended for dev/test only.

- `GET /openapi.json` — OpenAPI 3.1 spec (JSON)
- `GET /openapi.yaml` — OpenAPI 3.1 spec (YAML)
- `GET /docs` — Stoplight Elements UI (built into huma)

When `DOCS_ENABLED` is unset/false, those routes return 404. Production builds should leave it disabled.

## Validation

Request bodies use huma's native JSON Schema validation. Fields without `,omitempty` in the json tag are required; `maxLength:"N"` enforces length limits. No `go-playground/validator`, no `Resolve()` method, no `SkipValidateBody`. Validation failures appear in the response envelope's `error_detail` field.

## Response envelope

Defined in `httpx/humaresponse`:

- success: `{"status": true, "data": {...}, "cursor_pagination": {...}}`
- error:   `{"status": false, "message": "...", "error_detail": "...", "error_code": "ERR404000"}`

To return a typed error from a service or handler, use `apierr.CodeErr` / `apierr.CodeErrEnum` — both implement `huma.StatusError` so huma honors the `StatusCode`. Raw errors default to 500.
