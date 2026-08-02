# Handoff — couchbase runtime coverage

Read this file, then work the task in "The task" below. Everything else is
context: why the surrounding test infrastructure looks the way it does, and
which decisions are already settled so you don't relitigate them.

Not shipped to users — `dev/` is the maintainer area, per the repo `CLAUDE.md`.

---

## The task

**Give `cache=couchbase` runtime coverage.** It is the last combination in the
go-scaffolder matrix that is compile-only: the templates render it and it
builds, but no test has ever started a generated service against a real
couchbase.

It is the lowest-value of the five gaps closed recently — one combo, the
heaviest image, the slowest boot — which is exactly why it was deferred rather
than dropped.

### What exists today

| | |
|---|---|
| Compile combo | `api-chi-mysql-couchbase` in `tools/smoke/combos.go` — passes |
| Runtime combo | none — `couchbase` is absent from `run.sh`'s `COMBOS` |
| Compose service | none — `plugins/go-scaffolder/docker-compose.yml` has postgres, mysql, redis, kafka, rabbitmq |
| Template wiring | `main_api_*.go.tmpl` under `{{- else if eq .Cache "couchbase" }}` — `gocb.Connect` → `cachecb.New[*{Entity}Model](col)` |
| Config fields | `CouchbaseURL`, `CouchbaseUsername`, `CouchbasePassword`, `CouchbaseBucket` in `config.go.tmpl` |

### Steps

1. **Add couchbase to `plugins/go-scaffolder/docker-compose.yml`.** This is the
   hard part and worth timeboxing. Unlike the other five services, couchbase
   does not come up ready to use: the image starts an uninitialised cluster, and
   a bucket has to be created before anything can connect. Expect to need a
   post-start init step (`couchbase-cli cluster-init` + `bucket-create`, or the
   REST API on :8091) and a healthcheck that waits for the *bucket*, not just
   the process. A healthcheck that only polls `/pools` will go green while the
   bucket still does not exist, and the generated service will fail to connect.
2. **Add a runtime combo** to `COMBOS` in
   `skills/integration-test-go-app/scripts/run.sh`. The existing entry format is
   `combo-id|driver|cache-mode`, and `cache-mode` already accepts `couchbase` —
   `test_api`'s step 9 currently only asserts cache keys for `redis`, so extend
   that branch rather than adding a new one.
3. **Assert the cache is actually used.** The redis path checks
   `KEYS *order*` after a read. The couchbase equivalent is a document lookup in
   the bucket. Without this the combo proves only that the service starts with
   couchbase configured, not that the cache layer works — which is most of the
   point.
4. **Canary it.** See "Non-negotiable" below.
5. **Add the service to the CI runtime job** in
   `.github/workflows/go-scaffolder.yml` (the `docker compose up -d --wait` step
   lists services explicitly) — and check what it does to job duration.
   Couchbase is heavy; if it pushes the runtime job past a few extra minutes,
   consider whether it belongs in the per-PR job or a scheduled one.

### Reasonable outcome if it fights back

Couchbase being awkward to containerise is a legitimate reason to stop. If the
init dance proves unreliable in CI, land the local-only version and open an
issue rather than making the whole runtime suite flaky — a suite that fails at
random teaches people to ignore it, which costs more than this combo is worth.

---

## Non-negotiable: canary every assertion

Break the thing the assertion checks and confirm the run **fails**. Do not skip
this.

Twice this session an assertion was written, passed, and was later found
incapable of failing:

- a consumer test passed while publishing to a topic nobody subscribed to,
  because log files were appended to and never truncated — it was matching the
  *previous* run's output;
- the OpenAPI assertion had been failing every combo for weeks and nobody knew,
  because nothing ran the suite.

An assertion that cannot fail is indistinguishable from one that always
succeeds. The only way to tell them apart is to make it fail on purpose.

---

## Settled decisions — do not relitigate

| Decision | Why |
|---|---|
| **`queue` was added alongside `pubsub`, not replacing it** | `pubsub`'s kafka/rabbitmq adapters already had competing-consumer semantics; only redis was true fan-out. `queue` makes the split explicit. The alternative (making `pubsub` genuinely fan-out everywhere) changes delivery semantics for anything already deployed, so it needs opting into. |
| **`database=bun-*` forces `cache=none`** | `repo.CachedRepo` is generic over a repository exposing `DB(ctx) *gorm.DB` and cannot decorate a bun repo. The skills skip the cache question for bun rather than collecting an answer they cannot honour. **This means couchbase will never pair with bun** — do not add such a combo. |
| **No local-checkout override in the smoke runner** | A runner able to build against an unfetchable working tree reports green for a combination no user can reproduce. To test against unreleased go-lib, push it and let `@latest` resolve. |
| **Pre-existing fixes get their own PR to `main`** | They merge independently instead of waiting behind a feature review. Applied consistently — eight defects were split out this way. |
| **Stub mode is gated by build tag, never by env alone** | `SERVICE_BACKEND=stub` is the default in a fresh `.env`. An env-only check would make a production binary skip its database whenever that line survived into a deployment. |
| **`pubsub` is still the default `messaging` value** | Backwards compatibility for existing scaffolds. The prompt recommends `queue`; the parameter default does not. |

---

## Gotchas that cost real time

- **Log files are appended to.** `run.sh` truncates `$log_file` at the start of
  each combo. Anything new that greps a log must run after that truncation, or
  it reads the previous run.
- **DSN format is per-ORM, not per-engine.** GORM's postgres driver takes
  `host=… port=…`; bun's `pgdriver` only parses `postgres://…`. `engine_of()`
  deliberately strips the ORM half, so **never** pick a DSN with it — use
  `$driver`. This exact mistake shipped once.
- **Kafka needs its topic created up front.** Auto-create fires on first
  produce, but the consumer subscribes first and kafka-go caches
  "topic does not exist" for the group — the subscription then sits idle through
  a message it should have received.
- **Shutdown is signal → wait for confirmation → reap.** `kill_pid` escalates to
  SIGKILL after 5s and leaving a kafka consumer group takes longer, so reaping
  first makes a clean shutdown look like a failure.
- **Redis wire format depends on the messaging model.** `pubsub` is `PUBLISH`
  with a base64 JSON envelope; `queue` is `XADD` with flat fields. Kafka and
  rabbitmq carry the same bytes either way.
- **Redis queue does not echo caller message IDs.** A Streams ID must be
  `<millis>-<seq>`, so redis assigns it and that value is what `XACK` needs. The
  id assertion is scoped to redis + pubsub only.
- **A partially-rendered scratch dir breaks `go build ./...`** in
  `tools/smoke/`. A failed render leaves `.go` files with no `go.mod`, and
  `./...` walks into them. `rm -rf scratch` before building the runner.

---

## Verify your work

```bash
# Compile matrix — every template rendered, both build modes
cd plugins/go-scaffolder/tools/smoke
rm -rf scratch && go build ./... && go vet ./... && go run . -all
# expect: 24 passed, 0 skipped, 0 failed

# Runtime suite — needs the docker stack
cd ../../
docker compose up -d --wait          # add couchbase to this
cd skills/integration-test-go-app/scripts && ./run.sh
# expect: 17 passed (18 once couchbase lands), 0 failed

# Single combo while iterating
./run.sh couchbase
```

Both suites also run in CI on any PR touching `plugins/go-scaffolder/**`.

---

## How the current state was reached

Context for why the infrastructure looks the way it does. Skip if you only need
the task.

Two features landed, and building test coverage for them surfaced eight
pre-existing defects:

**Features**
- `go-lib/db/bunrepo` — SQL-first repository on bun, plus `bun-postgres` /
  `bun-mysql` in the scaffolder
- `go-lib/httpx/client` resty surface — one constructor on the existing
  instrumented transport
- `go-lib/queue` — work-queue abstraction; redis rebuilt on Streams
- scaffolder `messaging` parameter — `pubsub` | `queue` for consumer/publisher

**Defects found by building coverage, not by reading code**

| | |
|---|---|
| smoke matrix failing every combo | `templatesFor` missing `port_service` — baseline 0/16 |
| `api database=none` didn't compile | unconditional `"os"` import |
| echo template broken | huma's `humaecho` moved to echo/v5; fix was `NewV4`, not a major bump |
| OpenAPI assertion asserting dead schemas | runtime suite fully red, unnoticed |
| **stub mode had never booted without a database** | contradicted `SKILL.md` and `.env` |
| log assertions readable from a previous run | tests that could not fail |
| broker picker misdescribed redis as Streams | it is Pub/Sub — opposite guarantees |
| broker picker misnamed the kafka library | `segmentio`, not `confluent` (cgo vs pure Go) |

**Coverage before → after**

| | before | after |
|---|---|---|
| Compile matrix | 0/16 passing | 24/24, 31/31 templates, both build modes |
| Runtime suite | 0/5 passing | 17/17 |
| CI | none | both repos |

Runtime now spans api / consumer / publisher × redis / kafka / rabbitmq × gorm /
bun × pubsub / queue. Couchbase is what's left.

---

## Known overlap, not a bug

`queue/kafka` and `queue/rabbitmq` closely resemble their `pubsub` siblings,
because those brokers were always competing-consumer — only the package name
was misleading. That is option A working as designed. If `pubsub` ever gains
true fan-out for those two (unique group per subscriber; fanout exchange with
exclusive queues), the duplication resolves and `pubsub` becomes honest for all
three backends. That is a breaking change and belongs in its own decision.
