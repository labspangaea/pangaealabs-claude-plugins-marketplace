# OpenAPI / Scalar UI

Generated `api` services derive their OpenAPI 3.1 spec from the **TypeBox DTO
schemas** — the same `t.Object({...})` that drives runtime request validation
(single source of truth, the Elysia-native analog of Go huma's struct-derived
spec). There is no annotation drift: the validated shape *is* the documented shape.

## Wiring (`@elysiajs/openapi`)

Add the plugin in the composition root, gated by `DOCS_ENABLED`:

```ts
import { openapi } from '@elysiajs/openapi';

const app = new Elysia().use(serverPlugin({ logger, serviceName: cfg.serviceName }));
if (cfg.docsEnabled) {
  app.use(openapi({ path: '/docs' })); // Scalar UI at /docs, spec at /docs/json
}
app.use(healthController(cfg.version)).use({entityLower}Controller(svc));
```

- **UI**: Scalar at `/docs` (configurable). **Spec**: `/docs/json`.
- Gate on `DOCS_ENABLED` (default `false`) — enable in dev/test, leave off in prod.
- The controller's `body:` TypeBox schema and the response builders' shapes flow
  into the spec automatically; annotate operations with Elysia's `detail` field
  for summaries/tags when needed.

> v1 note: the proven slice ships CRUD without the OpenAPI plugin wired by
> default. Adding `@elysiajs/openapi` is a one-line opt-in (above); pin a version
> compatible with the project's Elysia.

## Validation → error envelope

TypeBox validation failures are caught by the `serverPlugin` `onError` hook and
returned as the canonical error envelope with HTTP 422:

```json
{ "status": false, "message": "unprocessable entity",
  "error_detail": "<TypeBox failure detail>", "error_code": "ERR422000" }
```

Fields without `t.Optional(...)` are required; `t.String({ maxLength: N })`
enforces length. No `Resolve()`, no second validator, no manual checks.

## Response envelope (from `@peruri/ts-lib/response`)

- success single: `{ "status": true, "data": {…} }`
- success list: `{ "status": true, "data": […], "cursor_pagination": { "next_cursor"?, "has_next", "limit" } }`
- error: `{ "status": false, "message"?, "error_detail"?, "error_code"? }`

To return a typed error: `throw new ApiError(ErrXxx)` — the HTTP status comes from
the registered `CodeErr.statusCode`. Raw thrown errors default to 500 (General).
