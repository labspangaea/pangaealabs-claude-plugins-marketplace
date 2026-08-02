# Cache backend wiring (api / consumer)

Inject the per-backend block into `cmd/{name}/main.go` between the DB-open block and the `repository.NewCached` call.

The cache value type is **the GORM model pointer** (`*repository.{{.Entity}}Model`), not the domain type — `CachedRepo` caches the SQL row; mapping to the domain happens in the repository's entity-suffixed methods.

`{{.EntityLower}}` = lowercase entity (e.g. `order`). Below assumes the active entity; swap the import + constructor for `memory` / `couchbase` as shown.

## `cache=redis`

```go
import (
    goredis "github.com/redis/go-redis/v9"
    cacheredis "github.com/labspangaea/go-lib/cache/redis"
    "github.com/labspangaea/go-lib/db/repo"
)

redisClient := goredis.NewClient(&goredis.Options{
    Addr:     cfg.RedisAddr,
    Password: cfg.RedisPassword,
    DB:       cfg.RedisDB,
})
defer redisClient.Close()
{{.EntityLower}}Cache := cacheredis.New[*repository.{{.Entity}}Model](redisClient)

// CachedRepo handles namespacing via the "{{.EntityLower}}" prefix arg passed to NewCached.
// Two-phase list: only enable after profiling confirms cache hit rate > ~70%.
{{.EntityLower}}Repo := repository.NewCached(gormDB, {{.EntityLower}}Cache,
    repo.WithTTL(cfg.CacheTTL),
    repo.WithJitter(cfg.CacheJitterFactor),
    repo.WithTwoPhaseList(),
)
```

## `cache=memory`

```go
import (
    cachemem "github.com/labspangaea/go-lib/cache/memory"
    "github.com/labspangaea/go-lib/db/repo"
)

{{.EntityLower}}Cache := cachemem.New[*repository.{{.Entity}}Model](
    cachemem.WithCapacity[*repository.{{.Entity}}Model](cfg.MemoryCacheCapacity),
)
{{.EntityLower}}Repo := repository.NewCached(gormDB, {{.EntityLower}}Cache,
    repo.WithTTL(cfg.CacheTTL),
    repo.WithJitter(cfg.CacheJitterFactor),
    // memory backend has no MGet/MSet — CachedRepo falls back to per-key loops automatically.
    repo.WithTwoPhaseList(),
)
```

## `cache=couchbase`

```go
import (
    "github.com/couchbase/gocb/v2"
    cachecb "github.com/labspangaea/go-lib/cache/couchbase"
    "github.com/labspangaea/go-lib/db/repo"
)

cluster, err := gocb.Connect(cfg.CouchbaseURL, gocb.ClusterOptions{
    Username: cfg.CouchbaseUsername,
    Password: cfg.CouchbasePassword,
})
if err != nil {
    log.Error("couchbase connect failed", slog.Any(logger.KeyError, err))
    os.Exit(1)
}
defer cluster.Close(nil)

col := cluster.Bucket(cfg.CouchbaseBucket).DefaultCollection()
{{.EntityLower}}Cache := cachecb.New[*repository.{{.Entity}}Model](col)

{{.EntityLower}}Repo := repository.NewCached(gormDB, {{.EntityLower}}Cache,
    repo.WithTTL(cfg.CacheTTL),
    repo.WithJitter(cfg.CacheJitterFactor),
    // couchbase backend has no MGet/MSet — CachedRepo falls back to per-key loops automatically.
    repo.WithTwoPhaseList(),
)
```

## Not available on the bun path

Everything in this file requires `database` to be `gorm-*`. `repo.CachedRepo` is
generic over a repository that exposes `DB(ctx) *gorm.DB`, so it cannot decorate a
repository built on `go-lib/db/bunrepo` — there is no bun equivalent of
`NewCached`. Both scaffolding skills therefore force `cache=none` whenever
`database` is `bun-postgres` or `bun-mysql`, and skip the cache question entirely.

A service that needs both a cache wrapper and bun has to choose one today. If that
comes up often enough to be worth building, the missing piece is a `CachedRepo` in
`db/bunrepo` reimplementing TTL, jitter, and invalidate-on-write over
`go-lib/cache.Cache[T]`.

## `cache=none`

Use `repository.New(gormDB)` directly — or `repository.New(bunDB)` on the bun path,
where this is the only option. No cache imports, no `NewCached` constructor in the
generated `repository.go`, no `Cache*`/`Redis*`/`Memory*`/`Couchbase*` fields in
`Config`. Then pass to the service:

```go
svc := service.New({{.EntityLower}}Repo) // works for both New(...) and NewCached(...)
```

`/go-scaffolder:create-go-repository` Step 7 points readers here for the same wiring snippets when adding a single repository to an existing project. The `main_api_*` template's `NewCached` wiring renders the canonical form; this file is the human-readable index.
