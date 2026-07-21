# codebase.md — go-peruri-lib API Reference

**Module**: `sipgn-git.bgn.go.id/harry.sitohang/go-peruri-lib`  
**Go**: `1.26.2`

---

## Interface → Implementations

| Interface | Implementations | Test double |
|-----------|----------------|-------------|
| `cache.Cache[V]` | `cache/redis`, `cache/memory`, `cache/couchbase` | `cache.Nop[V]()` |
| `repo.Repository[T,ID]` | `repo.BaseRepo[T,ID]`, `repo.CachedRepo[T,ID]` | pass `cache.Nop[*T]()` to `NewCached` |
| `pubsub.Publisher` | `pubsub/kafka`, `pubsub/rabbitmq`, `pubsub/redis` | mock via `go generate` |
| `pubsub.Consumer` | `pubsub/kafka`, `pubsub/rabbitmq`, `pubsub/redis` | mock via `go generate` |
| `distlock.Locker` | `distlock/redis` | mock via `go generate` |
| `storage.Storage` | `storage/obs` (Huawei OBS) | mock via `go generate` |
| `httpx/client.Doer` | `*http.Client` | mock `Doer` interface |

---

## `apierr/`

### Types
```go
type CodeErrEnum int // implements error

type CodeErr struct {
    Message    string
    Detail     string
    Code       string
    StatusCode int
} // implements error
```

### Built-in Constants

| Constant | HTTP Status | Built-in `Error()` string |
|----------|------------|--------------------------|
| `CodeErrGeneral` | 500 | `"something went wrong"` |
| `CodeErrNotFound` | 404 | `"not found"` |
| `CodeErrBadRequest` | 400 | `"bad request"` |
| `CodeErrValidation` | 422 | `"validation error"` |
| `CodeErrUnauthorized` | 401 | `"unauthorized"` |
| `CodeErrForbidden` | 403 | `"forbidden"` |
| `CodeErrConflict` | 409 | `"conflict"` |
| `CodeErrTooManyRequests` | 429 | `"rate limit exceeded. please try again later"` |
| `CodeErrUnprocessable` | 422 | `"unprocessable entity"` |

> **Note:** All built-in message strings are lowercase (Go error-string convention). If your service tests assert on the `"message"` field of an error response, use the lowercase form above.

### Signatures
```go
func AppendCodeErrMap(code CodeErrEnum, err CodeErr)       // MUST call in init(), never in handlers
func (e CodeErrEnum) GetCodeErr() CodeErr                  // lookup; falls back to CodeErrGeneral
func (e CodeErrEnum) WithDetail(err error) CodeErr         // copy with Detail = err.Error()
func (e CodeErrEnum) Error() string
```

### Canonical Usage
```go
// internal/apperr/errors.go
const (
    ErrOrderNotFound  apierr.CodeErrEnum = iota + 1000
    ErrOrderDuplicate
)

func init() {
    apierr.AppendCodeErrMap(ErrOrderNotFound, apierr.CodeErr{
        Message: "order not found", Code: "ERR404100", StatusCode: 404,
    })
    apierr.AppendCodeErrMap(ErrOrderDuplicate, apierr.CodeErr{
        Message: "order already exists", Code: "ERR409100", StatusCode: 409,
    })
}
```

### Do / Don't

| Do | Don't |
|----|-------|
| call `AppendCodeErrMap` in `init()` | call inside handlers or service methods |
| `ErrOrderNotFound.WithDetail(err)` to attach context | create a new `CodeErr` ad-hoc in handlers |

---

## `httpx/humaresponse/`

Generic JSON envelope wrappers for huma v2 handlers. Wire-identical to the
retired `httpx/response` builder so API consumers see no difference.

### Types
```go
type DataBody[T any] struct {
    Status  bool   `json:"status"`
    Message string `json:"message,omitempty"`
    Data    T      `json:"data,omitempty"`
}

type ListBody[T any] struct {
    Status           bool              `json:"status"`
    Message          string            `json:"message,omitempty"`
    Data             T                 `json:"data,omitempty"`
    CursorPagination *CursorPagination `json:"cursor_pagination,omitempty"`
    OffsetPagination *OffsetPagination `json:"offset_pagination,omitempty"`
}

type DataOutput[T any] struct{ Body DataBody[T] }
type ListOutput[T any] struct{ Body ListBody[T] }

type CursorPagination struct {
    NextCursor string `json:"next_cursor,omitempty"`
    HasNext    bool   `json:"has_next"`
    Limit      int    `json:"limit"`
}

type OffsetPagination struct {
    Total   int64 `json:"total"`
    Limit   int   `json:"limit"`
    Offset  int   `json:"offset"`
    HasNext bool  `json:"has_next"`
}

// ErrorBody implements huma.StatusError structurally — returned by the
// huma.NewError override in main so error responses stay on the same envelope.
type ErrorBody struct {
    Status    bool   `json:"status"` // always false
    Message   string `json:"message,omitempty"`
    ErrDetail string `json:"error_detail,omitempty"`
    ErrCode   string `json:"error_code,omitempty"`
}
```

### Signatures
```go
func Data[T any](data T) *DataOutput[T]
func List[T any](data T, opt ListOption[T]) *ListOutput[T]
func WithCursor[T any](p *CursorPagination) ListOption[T]
func WithOffset[T any](p *OffsetPagination) ListOption[T]
func NewError(c apierr.CodeErr) *ErrorBody  // for use inside huma.NewError override
```

### Canonical Usage
```go
// single-entity (find / create / update)
return humares.Data(entity), nil

// cursor-paginated list
return humares.List(entities, humares.WithCursor[[]*domain.Order](&humares.CursorPagination{
    NextCursor: page.NextCursor,
    HasNext:    page.HasNext,
    Limit:      page.Limit,
})), nil

// offset-paginated list
return humares.List(entities, humares.WithOffset[[]*domain.Order](&humares.OffsetPagination{
    Total:   total,
    Limit:   params.Limit,
    Offset:  params.Offset,
    HasNext: int64(params.Offset+params.Limit) < total,
})), nil

// delete — return nil, nil; set DefaultStatus: 204 on the operation
```

### Error Dispatch (huma.NewError override in main)

```go
huma.NewError = func(status int, msg string, errs ...error) huma.StatusError {
    detail := ""
    for i, e := range errs {
        if i > 0 { detail += "; " }
        detail += e.Error()
    }
    return humares.NewError(apierr.CodeErr{
        StatusCode: status,
        Message:    msg,
        Detail:     detail,
        Code:       fmt.Sprintf("ERR%d000", status),
    })
}
```

To return a typed error from a handler or service: `return apierr.CodeErrNotFound` (or `apierr.CodeErrXxx.WithDetail(err)`). Both `CodeErrEnum` and `CodeErr` implement `huma.StatusError` via `GetStatus()` so huma honors the registered status code. Raw errors default to 500.

---

## `httpx/server/`

### Signatures
```go
func Chain(h http.Handler, middleware ...func(http.Handler) http.Handler) http.Handler
func RequestID() func(http.Handler) http.Handler
func Logging(log *slog.Logger) func(http.Handler) http.Handler
func Recover(log *slog.Logger) func(http.Handler) http.Handler
```

### Middleware Order — MUST follow exactly
```go
handler := server.Chain(router,                // router is the underlying framework router
    server.Recover(log),                       // 1st — catches panics in all subsequent middleware
    server.RequestID(),                        // 2nd — injects X-Request-ID into ctx
    otelhttp.NewMiddleware(svcName),           // 3rd — starts OTel span
    server.Logging(log),                       // 4th — logs with span + request ID in scope
)
```

`server.Chain` wraps the underlying framework router. The huma adapter (`humagin`/`humachi`/`humaecho`/`humamux`/`humago`) sits on top of the router for route registration; middleware operates on the router below.

### Do / Don't

| Do | Don't |
|----|-------|
| `return nil, err` from huma handlers — huma renders via the `huma.NewError` override | construct response JSON manually in handlers |
| return `apierr.CodeErrEnum` from service for known errors | return raw `errors.New(...)` for domain errors that need a specific HTTP status |

---

## `httpx/client/`

### Types
```go
type Response[T any] struct {
    StatusCode int
    Header     http.Header
    Body       T
    Duration   time.Duration
}

type RequestError struct {
    StatusCode int
    Method     string
    URL        string
    Body       map[string]any
    Duration   time.Duration
} // implements error

type Doer interface {
    Do(*http.Request) (*http.Response, error)
}
```

### Signatures
```go
func NewClient(log *slog.Logger) *http.Client

func Get[T any](ctx context.Context, url string, opts ...Option) (Response[T], error)
func Post[T any](ctx context.Context, url string, body any, opts ...Option) (Response[T], error)
func Put[T any](ctx context.Context, url string, body any, opts ...Option) (Response[T], error)
func Delete[T any](ctx context.Context, url string, opts ...Option) (Response[T], error)
```

> **Default timeout:** `NewClient` sets a 30 s request timeout on the returned client. Override after construction when the upstream legitimately needs longer (e.g. file uploads): `c.Timeout = 2 * time.Minute`.

### Canonical Usage
```go
// NewClient auto-propagates OTel trace context; default timeout 30 s
c := client.NewClient(logger.FromContext(ctx))

type OrderResp struct { ID string `json:"id"` }
resp, err := client.Get[OrderResp](ctx, "https://api.example.com/orders/"+id)
if err != nil {
    // *client.RequestError carries the upstream status — wrap or convert
    // to apierr.CodeErr if the handler should surface that status.
    return fmt.Errorf("outbound: get order: %w", err)
}
```

---

## `logger/`

### Signatures
```go
func New(opts ...Option) *slog.Logger
func FromContext(ctx context.Context) *slog.Logger        // MUST use — never nil, returns Nop() if absent
func WithLogger(ctx context.Context, l *slog.Logger) context.Context
func WithRequestID(ctx context.Context, id string) context.Context
func WithTraceContext(ctx context.Context, traceID, spanID string) context.Context
func Nop() *slog.Logger
func IsNop(l *slog.Logger) bool
```

### Constructor Options

| Option | Effect |
|--------|--------|
| `WithServiceInfo(name, version, instanceID string)` | Attach service identity to every log line |
| `WithLevel(slog.Leveler)` | Minimum level to emit (default `LevelInfo`) |
| `WithDevelopment()` | Text encoding to stderr + source location |
| `WithSource()` | Adds source file/line in JSON output |
| `WithHandler(slog.Handler)` | Fan out every record to an additional handler |
| `WithOTelBridge(lp otellog.LoggerProvider, minLevel slog.Level)` | Stream records `>= minLevel` to OTLP via the supplied LoggerProvider; lower-severity records stay stdout-only |

### Field Key Constants

| Constant | String value |
|----------|-------------|
| `KeyRequestID` | `request_id` |
| `KeyTraceID` | `trace_id` |
| `KeySpanID` | `span_id` |
| `KeyHTTPMethod` | `http_method` |
| `KeyHTTPStatusCode` | `http_status_code` |
| `KeyHTTPURL` | `http_url` |
| `KeyURLPath` | `url_path` |
| `KeyError` | `error` |
| `KeyStack` | `stack` |
| `KeyDurationMS` | `duration_ms` |
| `KeyServiceName` | `service_name` |
| `KeyServiceVersion` | `service_version` |
| `KeyServiceInstanceID` | `service_instance_id` |
| `KeyUserID` | `user_id` |

### Canonical Usage
```go
// composition root
log := logger.New(logger.WithServiceInfo(cfg.ServiceName, cfg.Version, cfg.InstanceID))
ctx := logger.WithLogger(context.Background(), log)

// inside any method — retrieve, never inject
l := logger.FromContext(ctx)
l.Info("processing order", slog.String("id", id), slog.Any(logger.KeyError, err))
```

### Do / Don't

| Do | Don't |
|----|-------|
| `logger.FromContext(ctx)` inside every method | `type S struct { log *slog.Logger }` |
| `logger.WithLogger(ctx, log)` at composition root | pass `*slog.Logger` as function argument |
| `slog.Any(logger.KeyError, err)` for errors | `slog.String("err", err.Error())` |

---

## `telemetry/`

### Types
```go
type ShutdownFunc func(context.Context) error
```

### Signatures
```go
func Setup(ctx context.Context, opts ...Option) (trace.Tracer, log.LoggerProvider, ShutdownFunc, error)
```

### Constructor Options

| Option | Effect |
|--------|--------|
| `WithEndpoint(addr string)` | OTLP endpoint, `host:port` (default `localhost:4317`) |
| `WithProtocol(p string)` | OTLP wire protocol — `"grpc"` (default) or `"http/protobuf"` |
| `WithServiceInfo(name, version, instanceID string)` | OTel resource attributes |
| `WithHeaders(map[string]string)` | Per-request OTLP headers (e.g. SaaS auth `api-key`) |
| `WithInsecure()` | Disable TLS — local collector only |
| `WithGzipCompression()` | Enable gzip on the OTLP exporter |
| `WithSampler(sdktrace.Sampler)` | Override trace sampler (default `AlwaysSample`) |

### Canonical Usage
```go
otelOpts := []telemetry.Option{
    telemetry.WithEndpoint(cfg.OTelEndpoint),
    telemetry.WithProtocol(cfg.OTelProtocol),
    telemetry.WithServiceInfo(cfg.ServiceName, cfg.Version, cfg.InstanceID),
}
if cfg.OTelInsecure {
    otelOpts = append(otelOpts, telemetry.WithInsecure())
}
if len(cfg.OTelHeaders) > 0 {
    otelOpts = append(otelOpts, telemetry.WithHeaders(cfg.OTelHeaders))
}
_, lp, otelShutdown, err := telemetry.Setup(ctx, otelOpts...)
if err != nil {
    log.Warn("telemetry setup failed, continuing without tracing", slog.Any(logger.KeyError, err))
} else {
    defer otelShutdown(ctx) // MUST defer — flushes spans and logs on shutdown
}

// Optional: stream high-severity slog records to OTLP via the OTel log bridge.
if err == nil && cfg.OTelLogBridgeEnabled && lp != nil {
    log = logger.New(
        logger.WithServiceInfo(cfg.ServiceName, cfg.Version, cfg.InstanceID),
        logger.WithOTelBridge(lp, cfg.OTelLogMinSeverity),
    )
    ctx = logger.WithLogger(ctx, log)
}
```

---

## `db/`

### Signatures
```go
func Open(dialector gorm.Dialector, opts ...Option) (*gorm.DB, error)
func Close(db *gorm.DB)
```

### Constructor Options

| Option | Effect |
|--------|--------|
| `WithMaxOpenConns(n int)` | `sql.DB.SetMaxOpenConns(n)` |
| `WithSlowThreshold(d time.Duration)` | Log queries exceeding threshold |

---

## `db/repo/`

Generic GORM-backed repository with cursor pagination, composable filters, and an optional cache decorator.

### Interfaces
```go
// Model is implemented by each service's GORM model struct.
type Model[ID comparable] interface {
    TableName() string
    PrimaryKey() string        // column name, e.g. "id"
    GetPK() ID                 // actual PK value of this row
    CursorValues() map[string]any // values for all sortable columns
}

// Repository is the full interface satisfied by BaseRepo and CachedRepo.
// Services declare narrow subsets (OrderReader, OrderWriter) following ISP.
type Repository[T any, ID comparable] interface {
    FindByID(ctx context.Context, id ID) (*T, error)
    FindByIDs(ctx context.Context, ids []ID) ([]T, error)
    Create(ctx context.Context, entity *T) error
    Update(ctx context.Context, entity *T, columns []string) error
    Delete(ctx context.Context, id ID) error
    List(ctx context.Context, p CursorParams, filters ...Filter) ([]T, *CursorPage, error)
    ListIDs(ctx context.Context, p CursorParams, filters ...Filter) ([]ID, *CursorPage, error)
    DB(ctx context.Context) *gorm.DB
}

// CountStrategy performs a COUNT query on top of a pre-filtered scope. Opt-in only.
type CountStrategy interface {
    Count(db *gorm.DB) (int64, error)
}

// Filter applies a WHERE condition to a GORM query.
type Filter interface {
    Apply(db *gorm.DB) *gorm.DB
}

// Filterable is implemented by HTTP request structs that map params to filters.
type Filterable interface {
    ToFilters() []Filter
}
```

### Key Types
```go
type SortKey struct { Column string; Desc bool }
type CursorParams struct {
    Cursor  string
    Limit   int
    OrderBy []SortKey
}
type CursorPage struct {
    NextCursor string `json:"next_cursor,omitempty"`
    HasNext    bool   `json:"has_next"`
    Limit      int    `json:"limit"`
}
type FilterSet []Filter
```

### Signatures
```go
// BaseRepo
func New[T Model[ID], ID comparable](db *gorm.DB) *BaseRepo[T, ID]

// CachedRepo
func NewCached[T Model[ID], ID comparable](
    repo Repository[T, ID], c cache.Cache[*T], keyPrefix string, opts ...CachedOption,
) *CachedRepo[T, ID]

// SortKey constructors
func Asc(col string) SortKey
func Descending(col string) SortKey

// Filter constructors
func Eq(col string, val any) Filter
func Like(col string, val string) Filter       // wraps val in %%
func FullText(col string, val string) Filter   // MATCH(col) AGAINST (? IN BOOLEAN MODE)
func In(col string, vals ...any) Filter
func IsNull(col string) Filter
func NotNull(col string) Filter
func Raw(query string, args ...any) Filter

// FilterSet builder
func (fs *FilterSet) Add(f Filter) *FilterSet
func (fs *FilterSet) AddIf(condition bool, f Filter) *FilterSet
func (fs FilterSet) Build() []Filter

// Cursor helpers
func CursorParamsFromRequest(r *http.Request, defaultLimit int, defaultOrderBy ...SortKey) CursorParams

// CountStrategy
func ExactCount() CountStrategy              // SELECT COUNT(1) — MySQL + PostgreSQL
func ApproxCount(tableName string) CountStrategy // pg_class reltuples — PostgreSQL only
```

### CachedOption

| Option | Default | Effect |
|--------|---------|--------|
| `WithTTL(d time.Duration)` | 5 min | Base cache TTL |
| `WithJitter(factor float64)` | 0.1 | TTL jitter: effective = base + rand(0, base×factor) |
| `WithAtomicSet()` | off | SET NX via Lua — stampede protection on hot keys |
| `WithTwoPhaseList()` | off | ListIDs→MGet→IN→MSet; enable only if cache hit rate > ~70% |

### Error Sentinel
```go
var ErrNotFound = errors.New("not found")  // returned by FindByID on miss
```

### Three-layer error translation

| Layer | Error | Maps to |
|-------|-------|---------|
| `db/repo` | `repo.ErrNotFound` | returned on `gorm.ErrRecordNotFound` |
| `domain/` | `domain.ErrNotFound` | repo method wraps `repo.ErrNotFound` |
| `service/` | `apperr.ErrXxxNotFound` | service maps `domain.ErrNotFound` → CodeErrEnum |

### Canonical Usage
```go
// GORM model (adapter layer)
type orderModel struct {
    ID        string `gorm:"primaryKey;column:id"`
    Name      string `gorm:"column:name"`
    CreatedAt int64  `gorm:"column:created_at;autoCreateTime:milli"`
}
func (orderModel) TableName() string  { return "orders" }
func (orderModel) PrimaryKey() string { return "id" }
func (m orderModel) GetPK() string    { return m.ID }
func (m orderModel) CursorValues() map[string]any {
    return map[string]any{"id": m.ID, "created_at": m.CreatedAt}
}

// Repository struct (embed BaseRepo)
type Order struct{ *repo.BaseRepo[orderModel, string] }
func New(db *gorm.DB) *Order { return &Order{repo.New[orderModel, string](db)} }

// With cache (optional)
base   := repo.New[orderModel, string](db)
cached := repo.NewCached(base, redisCache, "order",
    repo.WithTTL(10*time.Minute))

// Handler — cursor params + Filterable pattern (huma)
params := repo.NewCursorParams(input.Cursor, input.Limit, repo.Descending("created_at"), repo.Asc("id"))
orders, page, err := h.svc.List(ctx, params, input.ToFilters()...)
if err != nil { return nil, err }
return humares.List(orders, humares.WithCursor[[]*domain.Order](&humares.CursorPagination{
    NextCursor: page.NextCursor, HasNext: page.HasNext, Limit: page.Limit,
})), nil

// Service — error translation
entity, err := s.repo.FindOrder(ctx, id)
if errors.Is(err, domain.ErrNotFound) {
    return nil, apperr.ErrOrderNotFound
}

// Opt-in total count (admin/reporting only)
var total int64
total, err = base.DB(ctx).Model(&orderModel{}).Scopes(...).Count(&total).Error // or ExactCount()
```

### Do / Don't

| Do | Don't |
|----|-------|
| `errors.Is(err, repo.ErrNotFound)` in repo adapter | return `apierr.CodeErrNotFound` from repo |
| `errors.Is(err, domain.ErrNotFound)` in service | let `repo.ErrNotFound` leak past the service layer |
| pass `[]string` of columns to `Update` for partial updates | call `Update` with empty columns to update only non-zero fields (GORM default) |
| `WithTwoPhaseList()` only after profiling (cache hit > ~70%) | enable two-phase list by default |

### Constructor Options

| Option | Effect |
|--------|--------|
| `WithMaxOpenConns(n int)` | `sql.DB.SetMaxOpenConns(n)` |
| `WithSlowThreshold(d time.Duration)` | Log queries exceeding threshold |

### Canonical Usage
```go
gormDB, err := db.Open(postgres.Open(cfg.DatabaseDSN),
    db.WithMaxOpenConns(cfg.DBMaxOpen),
    db.WithSlowThreshold(500*time.Millisecond),
)
if err != nil {
    log.Error("db open failed", slog.Any(logger.KeyError, err))
    os.Exit(1)
}
defer db.Close(gormDB) // MUST defer
```

---

## `distlock/`

### Interfaces
```go
type Locker interface {
    Acquire(ctx context.Context, key string, ttl time.Duration) (Lock, error)
}

type Lock interface {
    Release(ctx context.Context) error
    Token() string // fencing token — MUST pass to storage writes inside critical section
}
```

### Signatures
```go
func WithLock(ctx context.Context, l Locker, key string, ttl time.Duration, fn func() error) error
```

### Canonical Usage
```go
err := distlock.WithLock(ctx, locker, "order:"+id, 30*time.Second, func(lock distlock.Lock) error {
    // MUST pass lock.Token() as fencing token to every storage write inside this closure
    return repo.UpdateOrder(ctx, order, lock.Token())
})
if err != nil {
    return fmt.Errorf("acquire lock order %s: %w", id, err)
}
```

---

## `cache/`

### Interfaces
```go
type Getter[V any] interface {
    Get(ctx context.Context, key string) (V, bool, error)
}
type Setter[V any] interface {
    Set(ctx context.Context, key string, val V, ttl time.Duration) error
}
type Deleter interface {
    Delete(ctx context.Context, key string) error
}
type Cache[V any] interface {
    Getter[V]
    Setter[V]
    Deleter
}

// BatchGetter reads multiple keys in one round trip (e.g. Redis MGET).
// Implemented by cache/redis. Nil map value = cache miss.
type BatchGetter[V any] interface {
    MGet(ctx context.Context, keys []string) (map[string]V, error)
}

// BatchSetter writes multiple entries in one pipeline round trip (e.g. Redis pipelined SET).
// Implemented by cache/redis.
type BatchSetter[V any] interface {
    MSet(ctx context.Context, entries map[string]V, ttl time.Duration) error
}
```

### Signatures
```go
func Nop[V any]() Cache[V] // no-op — use in tests; miss on every Get, no-op on Set/Delete
```

### Constants

| Constant | Value | Meaning |
|----------|-------|---------|
| `NoTTL` | `0` | Entry never expires |

### Canonical Usage
```go
// Accept narrowest interface needed (ISP)
func LoadOrder(ctx context.Context, g cache.Getter[*Order], id string) (*Order, error) {
    v, ok, err := g.Get(ctx, id)
    if err != nil { return nil, fmt.Errorf("cache get order %s: %w", id, err) }
    if !ok { return nil, nil } // cache miss
    return v, nil
}

// Test double — no Redis required
svc := service.New(repo.NewCached(base, cache.Nop[*orderModel](), "order"))

// Batch read (Redis only — type-assert BatchGetter at construction)
if bg, ok := c.(cache.BatchGetter[*Order]); ok {
    hits, err := bg.MGet(ctx, []string{"order:1", "order:2"})
}
```

---

## `pubsub/`

### Interfaces
```go
type Publisher interface {
    Publish(ctx context.Context, topic string, msg Message) error
}

type Consumer interface {
    Subscribe(ctx context.Context, handler HandlerFunc) error
}
```

### Canonical Usage
```go
// publisher
err := pub.Publish(ctx, "orders.created", pubsub.Message{
    Key:  order.ID,
    Body: mustMarshal(order),
})
if err != nil {
    return fmt.Errorf("publish order created: %w", err)
}

// consumer — MUST use context.WithoutCancel so handler outlives request ctx
err := consumer.Subscribe(ctx, func(ctx context.Context, msg pubsub.Message) error {
    handlerCtx := context.WithoutCancel(ctx)
    return svc.ProcessOrder(handlerCtx, msg)
})
```

### Do / Don't

| Do | Don't |
|----|-------|
| `context.WithoutCancel(ctx)` inside subscriber handler | use parent ctx directly — cancelled when broker disconnects |

---

## `storage/`

### Interface
```go
type Storage interface {
    Put(ctx context.Context, key string, r io.Reader, size int64) error
    Get(ctx context.Context, key string) (io.ReadCloser, error)
    Delete(ctx context.Context, key string) error
}
```

### Canonical Usage
```go
// upload
f, _ := os.Open(filePath)
defer f.Close()
info, _ := f.Stat()
if err := store.Put(ctx, "invoices/"+id+".pdf", f, info.Size()); err != nil {
    return fmt.Errorf("storage put invoice %s: %w", id, err)
}

// download
rc, err := store.Get(ctx, "invoices/"+id+".pdf")
if err != nil {
    return fmt.Errorf("storage get invoice %s: %w", id, err)
}
defer rc.Close()
io.Copy(w, rc)
```

---

## Dependencies

| Package | Version | Used by |
|---------|---------|---------|
| `github.com/redis/go-redis/v9` | v9 | `cache/redis/`, `pubsub/redis/`, `distlock/redis/` |
| `github.com/couchbase/gocb/v2` | v2 | `cache/couchbase/` |
| `github.com/jackc/pgx/v5` | v5 | `db/` (via gorm) |
| `gorm.io/gorm` | v1.31.1 | `db/` |
| `gorm.io/driver/postgres` | v1.6.0 | `db/` |
| `github.com/segmentio/kafka-go` | v0.4 | `pubsub/kafka/` |
| `github.com/rabbitmq/amqp091-go` | v1 | `pubsub/rabbitmq/` |
| `github.com/huaweicloud/huaweicloud-sdk-go-obs` | v3 | `storage/obs/` |
| `github.com/go-playground/validator/v10` | v10 | `httpx/server/` (`ValidationErrors`) |
| `go.opentelemetry.io/otel` suite | v1.43.0 | `telemetry/`, `httpx/` |
| `go.uber.org/mock` | v0.6.0 | mock generation (`go generate`) |
| `go.uber.org/zap` | v1 | indirect (via couchbase) |
