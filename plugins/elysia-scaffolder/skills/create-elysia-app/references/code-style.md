# Code style

Local style baked into the templates. Read before authoring or hand-tweaking
generated TS.

## Style

| Rule | Do | Don't |
|---|---|---|
| Module system | ESM (`"type": "module"`), `.ts` extensions in imports | CommonJS `require` (except Bun-only dynamic cases) |
| Imports | `node:*` builtins → external → `@labspangaea/ts-lib/*` → relative, blank-line separated; `import type` for type-only | mixed groups, value imports of types |
| Naming | `MixedCaps` types, `camelCase` values, files `kebab-or-lower.ts` | `snake_case` identifiers, `I`-prefixed interfaces |
| Interfaces | narrow ports (1–3 methods); `{Entity}Repository`, `{Entity}Service` | one fat interface; stutter like `order.OrderService` |
| Constructors | `new{Entity}Repository(...)` factory functions returning the port type | exposing concrete classes across layers |
| Compile checks | `class X implements Port` (or `satisfies`) for the real + stub | duck-typing without the contract assertion |
| Async | `async`/`await`; return `Promise<T>` from I/O | floating promises (`void shutdown(...)` when intentional) |
| Comments | doc-comment exported symbols + the package header; explain *why* | comment obvious mechanics |

## Wire vs domain

- **Domain** types are camelCase (`customerId`, `createdAt: Date`).
- **Wire** (request bodies + responses) is snake_case (`customer_id`, `created_at`
  as ISO string), matching the Go service's json tags.
- The DTO layer (`bodyToInput` / `toResponse`) maps between them — never serialize
  the camelCase domain object straight to the wire.

## Errors

```ts
// throw a typed, registered error — never construct response JSON
throw new ApiError(ErrOrderNotFound);
// repository: map the repo sentinel, don't leak it
if (e === ErrNotFound) return new ApiError(ErrOrderNotFound);
```

| Anti-pattern | Correct |
|---|---|
| `throw new Error('not found')` in a handler | `throw new ApiError(ErrXxxNotFound)` |
| building `{status:false,…}` by hand | let the `serverPlugin` `onError` render it |
| swallowing errors (`catch {}`) | log via `fromContext()` and rethrow/return mapped |

## Timestamps

- Stored as `bigint` epoch-ms; the driver returns them as **strings**.
- Always coerce: `new Date(Number(row.created_at))` — a bare `new Date(string)`
  yields `Invalid Date` and throws at `toISOString()`.
