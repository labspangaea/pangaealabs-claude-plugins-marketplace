# Cache backend wiring

When `cache != none`, the repository exposes `newCached{Entity}Repository(...)`
and the composition root constructs the backend client + passes it in. The cache
value type is the **row type** (`{Entity}Row`), and the key prefix is owned by
`makeCachedRepository` — do NOT also prefix the backend (keys would double-prefix).

The library's `CachedRepo` (`@peruri/ts-lib/db/repo`) owns the cache-aside logic
(get→miss→load→set with TTL jitter, MGET/MSET batch fetch, invalidate-on-write,
optional two-phase list). The app only wires the backend.

## `cache = redis` (runtime-proven)

The repository template imports `createRedisCache` and the composition root passes
an `ioredis` client:

```ts
// index.ts
import { Redis } from 'ioredis';
const [host, port] = cfg.redisAddr.split(':');
const redis = new Redis({ host, port: Number(port), password: cfg.redisPassword || undefined,
  db: cfg.redisDb, lazyConnect: true, maxRetriesPerRequest: 1 });
const repo = newCached{Entity}Repository(db, redis, cfg.cacheTtlMs, cfg.cacheJitterFactor);

// repository/{entity}.ts (generated)
const cache = createRedisCache<{Entity}Row>(redis);
const cached = makeCachedRepository(base, cache, '{entityLower}', {
  getPK: (r) => r.id, options: [withTTL(ttlMs), withJitter(jitterFactor)],
});
```

`lazyConnect: true` so stub mode (no Redis) still boots. Redis implements
`BatchGetter`/`BatchSetter`, so `CachedRepo` uses MGET + pipelined SET.

## `cache = memory`

```ts
import { createMemoryCache } from '@peruri/ts-lib/cache';
const cache = createMemoryCache<{Entity}Row>({ capacity: cfg.memoryCacheCapacity });
const cached = makeCachedRepository(base, cache, '{entityLower}', {
  getPK: (r) => r.id, options: [withTTL(ttlMs), withJitter(jitterFactor)],
});
```

In-process LRU + lazy TTL; single-pod only. No batch methods, so `CachedRepo`
falls back to per-key get/set automatically.

## `cache = couchbase`

```ts
import { connect } from 'couchbase';
import { createCouchbaseCache } from '@peruri/ts-lib/cache';
const cluster = await connect(cfg.couchbaseUrl, { username: cfg.couchbaseUsername, password: cfg.couchbasePassword });
const col = cluster.bucket(cfg.couchbaseBucket).defaultCollection();
const cache = createCouchbaseCache<{Entity}Row>(col);
const cached = makeCachedRepository(base, cache, '{entityLower}', {
  getPK: (r) => r.id, options: [withTTL(ttlMs), withJitter(jitterFactor)],
});
```

No batch methods (per-key fallback). Native TTL via Upsert Expiry.

## `cache = none`

Use the direct repository — no cache imports, no `newCached…` constructor:

```ts
const repo = new{Entity}Repository(db);
```
