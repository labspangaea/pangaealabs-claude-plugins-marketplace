# codebase.md — @labspangaea/ts-lib API Reference

Source: <https://github.com/labspangaea/ts-lib>

TypeScript/Bun port of `go-lib`. Every package is importable via a subpath
(`@labspangaea/ts-lib/<pkg>`) or from the root barrel (`@labspangaea/ts-lib`). Durations are
**milliseconds** everywhere. Timestamps stored in the DB as `bigint` epoch-ms.

> Convention: domain types are camelCase; the HTTP/broker **wire** is snake_case
> (matching the Go services' JSON tags). The DTO layer maps between them.

---

## `@labspangaea/ts-lib/apperr`

```ts
enum CodeErrEnum { General=0, NotFound, BadRequest, Validation, Unauthorized,
                   Forbidden, Conflict, TooManyRequests, Unprocessable }
interface CodeErr { message: string; detail?: string; code: string; statusCode: number }
class ApiError extends Error { code; statusCode; detail?; constructor(c: CodeErrEnum, detail?: string|Error); toJSON() }

appendCodeErrMap(code: CodeErrEnum, err: CodeErr): void   // call at module load (init() analogue)
getCodeErr(code: CodeErrEnum): CodeErr                     // fallback to General
withDetail(code: CodeErrEnum, err: Error): CodeErr
isApiError(e: unknown): e is ApiError
```

Per-entity codes start at a base offset (scan existing + 1000). Wire shape:
`{ "status": false, "message": "...", "error_detail": "...", "error_code": "ERR404100" }`.

```ts
// src/apperr/order.ts
export const ErrOrderNotFound = (1000 + 0) as CodeErrEnum;
appendCodeErrMap(ErrOrderNotFound, { message: 'order not found', code: 'ERR404100', statusCode: 404 });
// throw it: throw new ApiError(ErrOrderNotFound);
```

---

## `@labspangaea/ts-lib/response`

```ts
data<T>(d: T, message?: string): { status:true; message?; data:T }
list<T>(items: T[], ...opts): { status:true; data:T[]; cursor_pagination?; offset_pagination? }
withCursor<T>(p: { next_cursor?:string; has_next:boolean; limit:number }): ListOption<T>
withOffset<T>(p: { total:number; limit:number; offset:number; has_next:boolean }): ListOption<T>
errorBody(ce: CodeErr): ErrorBodyShape
// TypeBox schema factories for Elysia route `response`:
DataBody(schema), ListBody(schema), ErrorBody
```

---

## `@labspangaea/ts-lib/logger`

pino + AsyncLocalStorage (the context.Context analogue).

```ts
createLogger(opts: { serviceName?; version?; instanceId?; level? }): pino.Logger
fromContext(): pino.Logger                                  // NEVER throws — base logger if no scope
runWithLogger(logger, fn): R                                // run fn with logger as the active one
bindRequest(base, { requestId?; traceId?; spanId? }): pino.Logger
nop(): pino.Logger
loggerContext: AsyncLocalStorage<{ logger }>
// field-key constants: KEY_REQUEST_ID, KEY_TRACE_ID, KEY_SPAN_ID, KEY_HTTP_METHOD,
//   KEY_HTTP_STATUS_CODE, KEY_URL_PATH, KEY_DURATION_MS, KEY_ERROR, KEY_STACK, ...
```

---

## `@labspangaea/ts-lib/server`

Elysia plugin wiring requestId + logging + recover (+ ApiError/validation/404 → envelope).

```ts
serverPlugin(opts: { logger: pino.Logger; serviceName: string }): Elysia   // .as('global')
HEADER_REQUEST_ID = 'x-request-id'
```

`onError` mapping: `ApiError`→its status+envelope · `VALIDATION`→422 · `NOT_FOUND`→404 ·
everything else→500 (logged with stack). Use as the FIRST `.use(...)` on the app.

---

## `@labspangaea/ts-lib/client`

fetch wrapper with W3C traceparent propagation + status-leveled logging (30s timeout).

```ts
get<ResT>(url, opts?: RequestOptions): Promise<HttpResponse<ResT>>
post<ReqT,ResT>(url, payload, opts?): Promise<HttpResponse<ResT>>
put<ReqT,ResT>(url, payload, opts?) ; del<ResT>(url, opts?)
newClient(opts?: { timeoutMs? }): Doer        // the default logging+OTel client
class RequestError extends Error { statusCode; method; url; body?; durationMs }
isRequestError(e): e is RequestError
interface RequestOptions { client?; queries?; headers?; signal?; timeoutMs? }
```

Non-2xx rejects with `RequestError` (parsed body); 204 → `body` undefined.

---

## `@labspangaea/ts-lib/db`

```ts
openPostgres(dsn, opts?: OpenOptions): Database          // Bun SQL + drizzle pg-proxy (lazy)
openMysql(dsn, opts?): MysqlDatabase                     // mysql2 + drizzle mysql-proxy (lazy)
closeDb(db: AnyDatabase): Promise<void>
type AnyDatabase = Database | MysqlDatabase
interface OpenOptions { maxOpenConns?; connMaxIdleTimeMs?; connMaxLifetimeMs?; slowThresholdMs?; logLevel? }
```

---

## `@labspangaea/ts-lib/db/repo`

Generic repository: cursor + offset pagination, filters, cache-aside decorator.

```ts
interface ModelMeta<T,ID> { table; primaryKey; columns: string[]; getPK(row): ID; cursorValues?(row) }
interface Repository<T,ID> { findById; findByIds; create; update(e, cols); del; list; listIds; db }
makeRepository<T,ID>(db: AnyDatabase, meta: ModelMeta<T,ID>): BaseRepo<T,ID>
makeCachedRepository<T,ID>(repo, cache: Cache<T>, keyPrefix, { getPK; options?; rng? }): CachedRepo<T,ID>

// cursor
type CursorParams = { cursor; limit; orderBy: SortKey[] }
asc(col), desc(col), newCursorParams(cursor, limit, ...sorts), cursorParamsFromQuery(q, defLimit, ...defOrderBy)
encodeCursor(values), decodeCursor(s)         // base64url(JSON), BigInt-safe int64
class InvalidCursorError ; isInvalidCursorError(e)   // map to HTTP 400
// offset
type OffsetParams = { offset; limit } ; offsetParamsFromQuery(q, defLimit) ; exactCount / approxCount
// filters
eq, like, fullText, inList, isNull, notNull, raw ; FilterSet ; interface Filterable { toFilters() }
// cached options
withTTL(ms), withJitter(factor), withAtomicSet(), withTwoPhaseList()
// errors
ErrNotFound  // returned by findById on miss; the adapter maps it to ApiError
```

CachedRepo: cache-aside findById (get→miss→load→set, TTL jitter `ttl + rand*ttl*factor`, key
`"<prefix>:<id>"`); findByIds MGET→IN→MSET→reorder; update/del invalidate; list two-phase opt-in.

---

## `@labspangaea/ts-lib/cache`

```ts
interface Cache<V> { get(key): Promise<{value:V; hit:boolean}>; set(key, val, ttlMs); del(key) }
interface BatchGetter<V> { mget(keys): Promise<Map<string,V>> } ; BatchSetter<V> { mset(entries, ttlMs) }
nop<V>(): Cache<V>
createRedisCache<V>(client: RedisLike, opts?): RedisCache<V>     // MGET + pipeline MSET
createMemoryCache<V>(opts?: { capacity? }): MemoryCache<V>        // LRU + lazy TTL
createCouchbaseCache<V>(collection, opts?): CouchbaseCache<V>
aside<V>(c, key, ttlMs, loader): Promise<V|null>                 // read-through helper
```

---

## `@labspangaea/ts-lib/distlock`

```ts
interface Locker { newLock(key, ttlMs, opts?): Lock }
interface Lock { tryLock(): Promise<boolean>; lock(signal?): Promise<void>; unlock(); refresh(); token(); key() }
createRedisLocker(client): RedisLocker            // SET NX PX + Lua compare-and-del/pexpire
withLock(lock, fn, signal?): Promise<T>           // fencing token via lock.token()
ErrNotHeld, ErrNotAcquired, isErrNotHeld, isErrNotAcquired
```

---

## `@labspangaea/ts-lib/pubsub` (+ `/kafka` `/rabbitmq` `/redis`)

```ts
interface Message { id?; key?; payload: Uint8Array|string|Buffer; headers? }
type Handler = (msg: Message) => Promise<void>           // resolve = ack, throw = nack/requeue
interface Publisher { publish(topic, msg); close() }
interface Consumer  { subscribe(topic, group, handler); close() }
// backends (import from the subpath so only the chosen SDK is pulled):
newKafkaPublisher(kafka: Kafka, ...opts) / newKafkaConsumer(kafka, ...opts)        // '@labspangaea/ts-lib/pubsub/kafka'
newRabbitMQPublisher(conn, exchange, ...opts) / newRabbitMQConsumer(conn, exchange, ...opts) // '/rabbitmq'
newRedisPublisher(client) / newRedisConsumer(client)                               // '/redis'
```

Subscriber handlers are NOT tied to a shutdown signal — `close()` stops the receive
loop but in-flight handlers run to completion (the `context.WithoutCancel` analogue).

---

## `@labspangaea/ts-lib/telemetry`

OTLP/**HTTP** traces + logs (gRPC unreliable on Bun) + a pino→OTel-logs bridge.

```ts
setup(opts?: SetupOptions): { tracer; loggerProvider; shutdown }   // never throws; degrades to no-op
builder()                                                          // fluent SetupOptions builder
createOtelPinoStream(loggerProvider, { minLevel }): PinoOtelStream // otelslog analogue
// SetupOptions: endpoint, protocol, insecure, gzip, headers, serviceName/version/instanceId, sampler
```

---

## `@labspangaea/ts-lib/storage`

```ts
interface Storage { put(bucket,key,body,opts?); get(bucket,key); del/delete; stat; presignGet; presignPut }
createS3Storage({ endpoint; region; accessKeyId; secretAccessKey; forcePathStyle? }): S3Storage  // OBS S3-compat
StorageErrNotFound, isErrNotFound
// native Huawei-OBS V2 signer:
obsSign, obsStringToSign, obsAuthorizationHeader, obsPresign
```

---

## `@labspangaea/ts-lib/ptr`

```ts
of<T>(v: T): T ; deref<T>(p: T|null|undefined, fallback: T): T   // nullish helpers
```

---

## Parity caveats (documented reductions)

- **telemetry**: OTLP/HTTP only (no gRPC on Bun); the logs SDK is beta.
- **storage**: S3-compat path verified by unit tests; the native OBS V2 signer is
  unit-pinned against known vectors but not exercised against a live OBS bucket.
- **stub mode**: excluded from the production binary via `bun build --define SERVICE_STUB`
  tree-shaking (a softer guarantee than Go's `//go:build` tag, functionally equal).
