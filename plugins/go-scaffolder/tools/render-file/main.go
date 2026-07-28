// render-file renders a single go-lib scaffold template to a file (or
// stdout) using the real Go text/template engine. Use this instead of mentally
// evaluating {{if}} conditionals — the LLM constructs the JSON params once,
// then delegates every conditional to this tool.
//
// Usage:
//
//	go run ./tools/render-file \
//	  -template  <path-to-.tmpl>     \
//	  -params    '<json-params>'      \
//	  [-output   <destination-path>]
//
// When -output is omitted the rendered content is written to stdout.
//
// The -params JSON shape mirrors the Fixture struct used by tools/smoke — same
// field names, same types. Required top-level keys:
//
//	Name, Module, Entity, EntityLower, ApperrBase, Type, HTTPFramework,
//	Broker, Database, Cache, Fields
//
// Example:
//
//	PARAMS='{"Name":"order-service","Module":"github.com/labspangaea/order-service",
//	  "Entity":"Order","EntityLower":"order","ApperrBase":1000,
//	  "Type":"api","HTTPFramework":"gin","Broker":"kafka",
//	  "Database":"gorm-postgres","Cache":"redis",
//	  "Fields":[{"Name":"CustomerID","GoType":"string","JSONName":"customer_id","DBColumn":"customer_id","Validate":"required"}]}'
//
//	go run ./tools/render-file \
//	  -template skills/create-go-app/references/config.go.tmpl \
//	  -params   "$PARAMS" \
//	  -output   config/config.go
package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"text/template"
)

// FieldDef mirrors the SKILL.md schema for {{range .Fields}} loops.
// Must stay in sync with tools/smoke/render.go FieldDef.
type FieldDef struct {
	Name     string
	GoType   string
	JSONName string
	DBColumn string
	Validate string
}

// Params is the data passed to text/template. Mirrors tools/smoke/render.go
// Fixture (same field names/types so the LLM only needs to know one shape).
type Params struct {
	Name          string
	Module        string
	Entity        string
	EntityLower   string
	ApperrBase    int
	Fields        []FieldDef
	Type          string
	HTTPFramework string
	Broker        string
	Database      string
	Cache         string
}

func main() {
	tmplPath := flag.String("template", "", "path to .tmpl file (required)")
	paramsRaw := flag.String("params", "", "JSON-encoded Params (required)")
	outputPath := flag.String("output", "", "destination file path (default: stdout)")
	flag.Parse()

	if *tmplPath == "" || *paramsRaw == "" {
		fmt.Fprintln(os.Stderr, "usage: render-file -template <path> -params <json> [-output <path>]")
		fmt.Fprintln(os.Stderr, "")
		fmt.Fprintln(os.Stderr, "Required JSON keys: Name Module Entity EntityLower ApperrBase Type HTTPFramework Broker Database Cache Fields")
		os.Exit(2)
	}

	body, err := os.ReadFile(*tmplPath)
	if err != nil {
		die("read template %s: %v", *tmplPath, err)
	}

	tmpl, err := template.New(filepath.Base(*tmplPath)).Funcs(funcMap()).Parse(string(body))
	if err != nil {
		die("parse template %s: %v", *tmplPath, err)
	}

	var p Params
	if err := json.Unmarshal([]byte(*paramsRaw), &p); err != nil {
		die("parse params JSON: %v", err)
	}

	var buf bytes.Buffer
	if err := tmpl.Execute(&buf, p); err != nil {
		die("execute template %s: %v", *tmplPath, err)
	}

	if *outputPath == "" {
		fmt.Print(buf.String())
		return
	}

	if err := os.MkdirAll(filepath.Dir(*outputPath), 0o755); err != nil {
		die("mkdir %s: %v", filepath.Dir(*outputPath), err)
	}
	if err := os.WriteFile(*outputPath, buf.Bytes(), 0o644); err != nil {
		die("write %s: %v", *outputPath, err)
	}
	fmt.Fprintf(os.Stderr, "rendered %s -> %s\n", filepath.Base(*tmplPath), *outputPath)
}

// funcMap registers custom template functions used by scaffold templates.
func funcMap() template.FuncMap {
	return template.FuncMap{
		// seq returns a []int of length n (values 0..n-1).
		// Used in seed.go.tmpl: {{range $i, $_ := (seq 25)}}
		"seq": func(n int) []int {
			s := make([]int, n)
			for i := range s {
				s[i] = i
			}
			return s
		},

		// seedValue returns a type-appropriate placeholder value for seed data.
		// idx is the loop index (0-based) so consecutive records differ.
		"seedValue": func(goType string, idx int) string {
			switch goType {
			case "string":
				return fmt.Sprintf(`"sample-%d"`, idx+1)
			case "*string":
				return fmt.Sprintf(`ptr.Of("sample-%d")`, idx+1)
			case "int64":
				return fmt.Sprintf("int64(%d)", (idx+1)*10)
			case "*int64":
				return fmt.Sprintf("ptr.Of(int64(%d))", (idx+1)*10)
			case "float64":
				return fmt.Sprintf("float64(%d)*9.99", idx+1)
			case "*float64":
				return fmt.Sprintf("ptr.Of(float64(%d)*9.99)", idx+1)
			case "bool":
				if idx%2 == 0 {
					return "true"
				}
				return "false"
			case "*bool":
				if idx%2 == 0 {
					return "ptr.Of(true)"
				}
				return "ptr.Of(false)"
			case "time.Time":
				return "time.Now().UTC()"
			case "*time.Time":
				return "ptr.Of(time.Now().UTC())"
			default:
				return `""`
			}
		},

		// hasFieldType returns true when any FieldDef in fields has the given GoType.
		// Used for conditional imports in seed.go.tmpl.
		"hasFieldType": func(goType string, fields []FieldDef) bool {
			for _, f := range fields {
				if f.GoType == goType || f.GoType == "*"+goType {
					return true
				}
			}
			return false
		},

		// hasNullableField returns true when any FieldDef in fields has a pointer
		// (nullable) Go type. Used in seed.go.tmpl to gate the `ptr` import — the
		// `ptr.Of(...)` helper is only emitted by seedValue for *T fields, so the
		// import is dead weight (and a compile error) when no field is nullable.
		"hasNullableField": func(fields []FieldDef) bool {
			for _, f := range fields {
				if strings.HasPrefix(f.GoType, "*") {
					return true
				}
			}
			return false
		},

		// isRequired returns true when the validate string contains "required".
		// Used in DTO templates: fields without required get ,omitempty in their json tag.
		"isRequired": func(validate string) bool {
			return strings.Contains(validate, "required")
		},

		// parseMaxLength extracts the N from "max=N" inside a validate string.
		// Returns 0 when no max constraint is present (falsy in {{if}} blocks).
		"parseMaxLength": func(validate string) int {
			for _, part := range strings.Split(validate, ",") {
				if v, ok := strings.CutPrefix(part, "max="); ok {
					if n, err := strconv.Atoi(v); err == nil {
						return n
					}
				}
			}
			return 0
		},

		// dbDriver returns the gorm driver import path for the given database param.
		"dbDriver": func(database string) string {
			switch database {
			case "gorm-mysql":
				return "gorm.io/driver/mysql"
			default:
				return "gorm.io/driver/postgres"
			}
		},

		// dbOpen returns the driver Open call for the given database param.
		"dbOpen": func(database string) string {
			switch database {
			case "gorm-mysql":
				return "mysql.Open(dsn)"
			default:
				return "postgres.Open(dsn)"
			}
		},
	}
}

func die(format string, args ...any) {
	fmt.Fprintf(os.Stderr, "render-file: "+format+"\n", args...)
	os.Exit(1)
}
