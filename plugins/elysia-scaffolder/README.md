# elysia-scaffolder

Scaffold production-ready **ElysiaJS services on Bun** wired to `@labspangaea/ts-lib` (the
TypeScript port of `go-lib`). Generates domain types, ports, Drizzle
repositories with optional caching, services, and TypeBox HTTP controllers — or
message-broker consumers/publishers across 3 brokers.

The TypeScript/Bun counterpart of [`go-scaffolder`](../go-scaffolder).

## Skills

| Skill | Use when you want to… |
|---|---|
| `/elysia-scaffolder:create-elysia-app` | Scaffold a complete service from scratch (orchestrates the 3 layered skills, then adds `src/index.ts`, `config/`, `package.json`, `tsconfig`, `drizzle.config`). |
| `/elysia-scaffolder:create-elysia-repository` | Add an entity's data layer (domain + port + Drizzle repository + schema + apperr). Owns the schema-parsing rules. |
| `/elysia-scaffolder:create-elysia-service` | Add the use-case/service layer (real + stub + factory) for an existing port. |
| `/elysia-scaffolder:create-elysia-handler` | Add the thin Elysia controller + TypeBox DTO for an existing service. |
| `/elysia-scaffolder:integration-test-elysia-app` | Boot the generated service against real postgres + redis and assert CRUD / cursor / cache / OpenAPI. |

## Parameters

- `type`: `api` · `consumer` · `publisher`
- `database`: `drizzle-postgres` · `drizzle-mysql` · `none`
- `cache`: `none` · `redis` · `memory` · `couchbase`
- `broker`: `kafka` · `rabbitmq` · `redis`

> No `http_framework` axis — Elysia *is* the framework (the Go plugin's 5-framework
> parameter collapses to one). The matrix is `type × database × cache × broker`.

## Architecture (hybrid hexagonal)

```
src/index.ts                              composition root: Elysia + ALS + OTel + middleware + graceful stop
config/config.ts                          env-driven config (Bun.env)
src/domain/{entity}.ts                    business types
src/port/{entity}.ts                      {Entity}Repository interface (driven port)
src/port/{entity}-service.ts              (api) {Entity}Service interface
src/service/{entity}.ts                   real use-cases (`satisfies {Entity}Service`)
src/service/stub/{entity}.ts              (api) canned stub — tree-shaken from the prod build
src/service/factory.ts                    SERVICE_BACKEND switch (stub branch DCE'd in prod)
src/apperr/{entity}.ts                    CodeErr registry, base offset
src/db/schema/{entity}.ts                 Drizzle table
src/adapter/inbound/http/{entity}.ts      (api) THIN Elysia controller + TypeBox DTO
src/adapter/inbound/subscriber/handler.ts (consumer) message handler
src/adapter/outbound/repository/{entity}.ts  Drizzle repo (BaseRepo/CachedRepo)
src/adapter/outbound/publisher/publisher.ts  (publisher) message publisher
```

Strict hexagonal **core** (domain/port/service/repository/apperr) with a **thin,
idiomatic Elysia controller** as the inbound adapter — keeping Elysia's TypeBox
inference + OpenAPI autogen while decoupling business logic from HTTP (DIP).

## Prerequisites

- **Bun 1.1+** on `PATH`.
- **Network access** — `@labspangaea/ts-lib` (the TypeScript port of `go-lib`) is a **public**
  npm package. Generated services depend on it directly; `bun install` fetches it from the public
  registry. No registry token, no `.npmrc` auth, no `file:` sibling path, no config store.
- **`mcp__ts-lsp__ts_diagnose`** MCP tool — called after every generated file to catch
  type errors before reporting done (the `go_diagnose` analogue).

See `skills/create-elysia-app/references/preflight.md`.

## Usage

```
/elysia-scaffolder:create-elysia-app type=api name=order-service
```

The skill asks any unspecified parameters one at a time, then the entity schema
(JSON example, SQL `CREATE TABLE`, OpenAPI `properties:`, or Postman body), then
generates the project as a standalone directory at the path you name.

## Stub mode (FE/BE parallel development)

Default `.env` ships `SERVICE_BACKEND=stub`. Boot without postgres/redis and serve
canned, shape-correct responses (OpenAPI + Scalar UI at `/docs`):

```bash
SERVICE_BACKEND=stub bun run src/index.ts        # FE points at http://localhost:8080/docs
```

When backend logic is ready: `SERVICE_BACKEND=real bun run src/index.ts`. The
production build (`bun build`) tree-shakes the stub out of the binary.

## Runtime tests

`/elysia-scaffolder:integration-test-elysia-app` renders the api+postgres+redis
combo from the live templates, brings up docker (postgres + redis), seeds 25 rows,
boots the binary, and asserts CRUD → cursor (no-overlap) → offset → redis cache key →
`request_id` logs → OpenAPI `/docs` + spec → invalid-cursor 400 → unknown-route 404.

Compile-only matrix checking is `tools/smoke` (maintainer tool).

## What's bundled

```
elysia-scaffolder/
├── .claude-plugin/plugin.json
├── README.md                          # this file
├── references/codebase.md             # @labspangaea/ts-lib API reference
├── skills/
│   ├── create-elysia-app/             # orchestrator — owns the templates
│   │   └── references/*.tmpl + *.md   # 26 templates + wiring-rules/cache-backends/preflight/openapi/
│   │                                  #   dev-bootstrap/code-style
│   ├── create-elysia-repository/SKILL.md
│   ├── create-elysia-service/SKILL.md
│   ├── create-elysia-handler/SKILL.md
│   └── integration-test-elysia-app/   # SKILL.md + scripts/run.sh
└── tools/
    ├── render-file/                   # zero-dep Bun template renderer
    └── smoke/                         # compile-only matrix runner (maintainer)
```

### Dependency on `@labspangaea/ts-lib`

`@labspangaea/ts-lib` is a **public** npm package. Every generated `package.json`
depends on it at a fixed version (`"@labspangaea/ts-lib": "^0.1.0"`) and `bun install`
fetches it from the public registry — no registry token, no `.npmrc` auth, no `file:`
sibling path, no config store.
