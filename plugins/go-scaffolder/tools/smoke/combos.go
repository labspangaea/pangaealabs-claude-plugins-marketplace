package main

import (
	"slices"
	"strings"
)

// Combo describes one (type, framework, broker, database, cache) tuple
// the smoke runner verifies. Adding a new combo: append a row, update PROGRESS.md.
type Combo struct {
	ID            string
	Type          string // api · consumer · publisher
	HTTPFramework string // api: nethttp · gin · chi · mux · echo
	Broker        string // consumer/publisher: kafka · rabbitmq · redis
	Database      string // gorm-postgres · gorm-mysql · bun-postgres · bun-mysql · none
	Cache         string // none · redis · memory · couchbase
}

// isBunDB mirrors the isBun template function. Kept in sync by hand — the
// template funcMap lives in render.go and cannot be called from combo routing.
func isBunDB(database string) bool { return strings.HasPrefix(database, "bun-") }

// golibBunVersion pins go-lib for bun combos.
//
// db/bunrepo is on go-lib main, so `go mod tidy` against @latest would now
// resolve it. This stays pinned so a smoke run and a scaffolded project agree
// on one go-lib rather than drifting apart as main moves — the matrix should
// fail because a template changed, not because an unrelated go-lib commit
// landed between two runs.
//
// Keep identical to the pin quoted in create-go-app/SKILL.md's post-generation
// step. To move it: `go get github.com/labspangaea/go-lib@<sha>` in a scratch
// module and copy the version `go.mod` records.
const golibBunVersion = "v0.0.0-20260802024135-5c4f756eb258"

var combos = []Combo{
	{ID: "api-nethttp-postgres-none", Type: "api", HTTPFramework: "nethttp", Database: "gorm-postgres", Cache: "none"},
	{ID: "api-nethttp-postgres-redis", Type: "api", HTTPFramework: "nethttp", Database: "gorm-postgres", Cache: "redis"},
	{ID: "api-gin-postgres-memory", Type: "api", HTTPFramework: "gin", Database: "gorm-postgres", Cache: "memory"},
	{ID: "api-chi-mysql-couchbase", Type: "api", HTTPFramework: "chi", Database: "gorm-mysql", Cache: "couchbase"},
	{ID: "api-mux-postgres-none", Type: "api", HTTPFramework: "mux", Database: "gorm-postgres", Cache: "none"},
	{ID: "api-echo-postgres-redis", Type: "api", HTTPFramework: "echo", Database: "gorm-postgres", Cache: "redis"},
	{ID: "api-nethttp-nodb-none", Type: "api", HTTPFramework: "nethttp", Database: "none", Cache: "none"},
	{ID: "consumer-kafka-postgres-none", Type: "consumer", Broker: "kafka", Database: "gorm-postgres", Cache: "none"},
	{ID: "consumer-rabbitmq-postgres-redis", Type: "consumer", Broker: "rabbitmq", Database: "gorm-postgres", Cache: "redis"},
	{ID: "consumer-redis-postgres-none", Type: "consumer", Broker: "redis", Database: "gorm-postgres", Cache: "none"},
	{ID: "publisher-kafka-nodb-none", Type: "publisher", Broker: "kafka", Database: "none", Cache: "none"},
	{ID: "publisher-rabbitmq-nodb-none", Type: "publisher", Broker: "rabbitmq", Database: "none", Cache: "none"},
	{ID: "publisher-redis-nodb-none", Type: "publisher", Broker: "redis", Database: "none", Cache: "none"},

	// Coverage-extension combos (paths not exercised by the representative 13).
	{ID: "api-nethttp-mysql-none", Type: "api", HTTPFramework: "nethttp", Database: "gorm-mysql", Cache: "none"},
	{ID: "consumer-kafka-postgres-memory", Type: "consumer", Broker: "kafka", Database: "gorm-postgres", Cache: "memory"},
	{ID: "consumer-rabbitmq-nodb-none", Type: "consumer", Broker: "rabbitmq", Database: "none", Cache: "none"},

	// bun (SQL-first) combos. Cache is always none — go-lib's cache decorator
	// wraps a GORM repository and cannot decorate a bun one, so the skills force
	// cache=none whenever database is bun-*. A bun+cache combo here would be
	// testing a configuration the scaffolder refuses to emit.
	//
	// nethttp is covered because its composition root is the one that differs
	// (numbered step comments), so it takes a separate patch from the other four.
	{ID: "api-gin-bunpg-none", Type: "api", HTTPFramework: "gin", Database: "bun-postgres", Cache: "none"},
	{ID: "api-nethttp-bunpg-none", Type: "api", HTTPFramework: "nethttp", Database: "bun-postgres", Cache: "none"},
	{ID: "api-chi-bunmysql-none", Type: "api", HTTPFramework: "chi", Database: "bun-mysql", Cache: "none"},
	{ID: "consumer-kafka-bunpg-none", Type: "consumer", Broker: "kafka", Database: "bun-postgres", Cache: "none"},
}

// b1Ready is the explicit allowlist of templates safe for the smoke runner.
// A template enters this set only after its SCAFFOLD-style conditionals (the
// LLM-interpreted prose comments and per-framework hardcoding) have been
// converted to deterministic Go `{{if}}` directives that text/template can
// render correctly. See PROGRESS.md for the conversion checklist.
//
// Combos depending on any non-listed template are skipped by the runner.
var b1Ready = map[string]bool{
	// Pure substitution — no combo conditionals needed.
	"apperr.go.tmpl":                  true,
	"domain.go.tmpl":                  true,
	"port.go.tmpl":                    true,
	"port_service.go.tmpl":            true,
	"service.go.tmpl":                 true,
	"service_factory_default.go.tmpl": true,
	"subscriber.go.tmpl":              true,

	// Converted templates.
	"repository.go.tmpl":              true,
	"repository_bun.go.tmpl":          true, // bun flavour of the same output path
	"config.go.tmpl":                  true,
	"main_api_nethttp.go.tmpl":        true,
	"main_api_gin.go.tmpl":            true,
	"main_api_chi.go.tmpl":            true,
	"main_api_mux.go.tmpl":            true,
	"main_api_echo.go.tmpl":           true,
	"health.go.tmpl":                  true, // standalone health+version handler
	"httphandler.go.tmpl":             true, // framework-agnostic huma handler
	"httphandler_dto.go.tmpl":         true, // huma input/output structs, huma-native validation
	"main_consumer_kafka.go.tmpl":     true,
	"main_consumer_rabbitmq.go.tmpl":  true,
	"main_consumer_redis.go.tmpl":     true,
	"main_publisher_kafka.go.tmpl":    true,
	"main_publisher_rabbitmq.go.tmpl": true,
	"main_publisher_redis.go.tmpl":    true,

	// Stub mode. Rendered for every api combo and exercised by the
	// `go build -tags=stub` pass — see runBuilds in main.go.
	"service_stub.go.tmpl":         true,
	"service_factory_stub.go.tmpl": true,

	// Dev-environment files. seed is real Go and compiles with the rest;
	// the rest are non-Go, so rendering them IS the check — it catches the
	// template-execution failures (missing funcMap entry, renamed field,
	// bad conditional) that are the whole reason this runner exists.
	"seed.go.tmpl":            true,
	".env.tmpl":               true,
	".gitignore.tmpl":         true,
	"Dockerfile.tmpl":         true,
	"docker-compose.yml.tmpl": true,
}

// buildTagsFor returns the build-tag sets combo c must compile under. "" means
// no tags (the production build).
//
// Only api scaffolds ship a stub backend, so only they get the second pass.
func buildTagsFor(c Combo) []string {
	if c.Type == "api" {
		return []string{"", "stub"}
	}
	return []string{""}
}

// templatesFor returns the basenames of every template needed to render combo c.
func templatesFor(c Combo) []string {
	// port_service is unconditional: service.go carries a compile-time assertion
	// that *{Entity} satisfies port.{Entity}Service, for every service type.
	ts := []string{
		"domain.go.tmpl",
		"port.go.tmpl",
		"port_service.go.tmpl",
		"service.go.tmpl",
		"config.go.tmpl",
		// Dev-environment files. Every scaffold emits these, so every combo
		// renders them — a broken conditional here ships a project that cannot
		// be started even though every .go file compiles.
		".env.tmpl",
		".gitignore.tmpl",
		"Dockerfile.tmpl",
		"docker-compose.yml.tmpl",
	}
	if c.Database != "none" && c.Type != "publisher" {
		// Both repository templates render to the same path; the database param
		// picks which one. They are never generated together.
		if isBunDB(c.Database) {
			ts = append(ts, "repository_bun.go.tmpl", "apperr.go.tmpl")
		} else {
			ts = append(ts, "repository.go.tmpl", "apperr.go.tmpl")
		}
		// cmd/seed is real Go and builds with everything else.
		ts = append(ts, "seed.go.tmpl")
	}
	switch c.Type {
	case "api":
		// apperr already added above when db != none; ensure it for db == none too.
		if c.Database == "none" {
			ts = append(ts, "apperr.go.tmpl")
		}
		// The three service-wiring files. factory_default (//go:build !stub)
		// supplies New{Entity}Service for production builds; factory_stub and the
		// stub package (//go:build stub) supply it under -tags=stub.
		//
		// Rendering the stub package does not disturb the production build:
		// `go build ./...` skips a package whose files are all excluded by build
		// constraints rather than erroring, so both passes work off one render.
		ts = append(ts,
			"service_factory_default.go.tmpl",
			"service_factory_stub.go.tmpl",
			"service_stub.go.tmpl",
		)
		// Handler templates are framework-agnostic (huma derives the spec from
		// Go types); only main_api_*.go.tmpl varies per framework adapter.
		ts = append(ts,
			"main_api_"+c.HTTPFramework+".go.tmpl",
			"health.go.tmpl",
			"httphandler.go.tmpl",
			"httphandler_dto.go.tmpl",
		)
	case "consumer":
		ts = append(ts,
			"subscriber.go.tmpl",
			"main_consumer_"+c.Broker+".go.tmpl",
		)
	case "publisher":
		ts = append(ts, "main_publisher_"+c.Broker+".go.tmpl")
	}
	return ts
}

// affectedCombos returns indices of combos whose template set includes basename.
// Empty slice means the changed template is not in any combo (no work to do).
func affectedCombos(basename string) []int {
	var out []int
	for i, c := range combos {
		if slices.Contains(templatesFor(c), basename) {
			out = append(out, i)
		}
	}
	return out
}
