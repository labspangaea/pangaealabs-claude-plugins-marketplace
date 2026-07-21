package main

import "slices"

// Combo describes one (type, framework, broker, database, cache) tuple
// the smoke runner verifies. Adding a new combo: append a row, update PROGRESS.md.
type Combo struct {
	ID            string
	Type          string // api · consumer · publisher
	HTTPFramework string // api: nethttp · gin · chi · mux · echo
	Broker        string // consumer/publisher: kafka · rabbitmq · redis
	Database      string // gorm-postgres · gorm-mysql · none
	Cache         string // none · redis · memory · couchbase
}

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
	"apperr.go.tmpl":     true,
	"domain.go.tmpl":     true,
	"port.go.tmpl":       true,
	"service.go.tmpl":    true,
	"subscriber.go.tmpl": true,

	// Converted templates.
	"repository.go.tmpl":              true,
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
}

// templatesFor returns the basenames of every template needed to render combo c.
func templatesFor(c Combo) []string {
	ts := []string{"domain.go.tmpl", "port.go.tmpl", "service.go.tmpl", "config.go.tmpl"}
	if c.Database != "none" && c.Type != "publisher" {
		ts = append(ts, "repository.go.tmpl", "apperr.go.tmpl")
	}
	switch c.Type {
	case "api":
		// apperr already added above when db != none; ensure it for db == none too.
		if c.Database == "none" {
			ts = append(ts, "apperr.go.tmpl")
		}
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
