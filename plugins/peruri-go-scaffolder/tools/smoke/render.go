package main

import (
	"bytes"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"text/template"
)

// FieldDef matches the SKILL.md schema for {{range .Fields}} loops.
type FieldDef struct {
	Name     string
	GoType   string
	JSONName string
	DBColumn string
	Validate string
}

// Fixture is the data passed to text/template for one combo. Mirrors the
// "Template Variables" table in .claude/skills/create-go-app/SKILL.md plus
// the new combo selectors used by `{{if}}` conditionals.
type Fixture struct {
	Name        string
	Module      string
	Entity      string
	EntityLower string
	ApperrBase  int
	Fields      []FieldDef

	Type          string
	HTTPFramework string
	Broker        string
	Database      string
	Cache         string
}

func fixtureFor(c Combo) Fixture {
	return Fixture{
		Name:        "smoke-" + c.ID,
		Module:      "smoke/" + c.ID,
		Entity:      "Order",
		EntityLower: "order",
		ApperrBase:  1000,
		Fields: []FieldDef{
			{Name: "ProductCode", GoType: "string", JSONName: "product_code", DBColumn: "product_code", Validate: "required,max=64"},
			{Name: "Quantity", GoType: "int64", JSONName: "quantity", DBColumn: "quantity", Validate: "required"},
			{Name: "InStock", GoType: "bool", JSONName: "in_stock", DBColumn: "in_stock", Validate: ""},
		},
		Type:          c.Type,
		HTTPFramework: c.HTTPFramework,
		Broker:        c.Broker,
		Database:      c.Database,
		Cache:         c.Cache,
	}
}

// outputPath maps a template basename to its destination path inside the
// scratch project for one combo.
func outputPath(basename string, fx Fixture) string {
	switch {
	case basename == "domain.go.tmpl":
		return filepath.Join("internal", "domain", fx.EntityLower+".go")
	case basename == "port.go.tmpl":
		return filepath.Join("internal", "port", fx.EntityLower+".go")
	case basename == "service.go.tmpl":
		return filepath.Join("internal", "service", fx.EntityLower+".go")
	case basename == "apperr.go.tmpl":
		return filepath.Join("internal", "apperr", fx.EntityLower+".go")
	case basename == "subscriber.go.tmpl":
		return filepath.Join("internal", "adapter", "inbound", "subscriber", "handler.go")
	case basename == "repository.go.tmpl":
		return filepath.Join("internal", "adapter", "outbound", "repository", fx.EntityLower+".go")
	case basename == "config.go.tmpl":
		return filepath.Join("config", "config.go")
	case basename == "httphandler.go.tmpl":
		return filepath.Join("internal", "adapter", "inbound", "httphandler", fx.EntityLower+".go")
	case basename == "httphandler_dto.go.tmpl":
		return filepath.Join("internal", "adapter", "inbound", "httphandler", fx.EntityLower+"_dto.go")
	case basename == "health.go.tmpl":
		return filepath.Join("internal", "adapter", "inbound", "httphandler", "health.go")
	case basename == "Dockerfile.tmpl":
		return "Dockerfile"
	case basename == ".gitignore.tmpl":
		return ".gitignore"
	case strings.HasPrefix(basename, "main_"):
		return filepath.Join("cmd", fx.Name, "main.go")
	}
	return ""
}

// readyCheck returns "" when basename is in the explicit b1Ready allowlist,
// otherwise a human-readable reason for skipping. Templates enter b1Ready
// only after manual conversion — see PROGRESS.md for the checklist.
func readyCheck(basename string) (skipReason string) {
	if b1Ready[basename] {
		return ""
	}
	return fmt.Sprintf("%s not yet B1-ready (see PROGRESS.md)", basename)
}

// funcMap registers the same custom template functions as tools/render-file so
// both tools evaluate identical template output for a given set of parameters.
func funcMap() template.FuncMap {
	return template.FuncMap{
		"seq": func(n int) []int {
			s := make([]int, n)
			for i := range s {
				s[i] = i
			}
			return s
		},
		"isRequired": func(validate string) bool {
			return strings.Contains(validate, "required")
		},
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
		"hasFieldType": func(goType string, fields []FieldDef) bool {
			for _, f := range fields {
				if f.GoType == goType || f.GoType == "*"+goType {
					return true
				}
			}
			return false
		},
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
			default:
				return `""`
			}
		},
		"dbOpen": func(database string) string {
			if database == "gorm-mysql" {
				return "mysql.Open(dsn)"
			}
			return "postgres.Open(dsn)"
		},
	}
}

// renderCombo writes all required files for combo c into outDir. Returns a
// skip reason if any required template isn't B1-ready, otherwise "" + nil.
func renderCombo(refsDir, outDir string, c Combo) (skipReason string, err error) {
	fx := fixtureFor(c)
	required := templatesFor(c)

	for _, t := range required {
		if reason := readyCheck(t); reason != "" {
			return reason, nil
		}
	}

	if err := os.RemoveAll(outDir); err != nil {
		return "", fmt.Errorf("clear scratch %s: %w", outDir, err)
	}
	if err := os.MkdirAll(outDir, 0o755); err != nil {
		return "", fmt.Errorf("mkdir %s: %w", outDir, err)
	}

	for _, t := range required {
		body, err := os.ReadFile(filepath.Join(refsDir, t))
		if err != nil {
			return "", fmt.Errorf("read %s: %w", t, err)
		}
		tmpl, err := template.New(t).Funcs(funcMap()).Parse(string(body))
		if err != nil {
			return "", fmt.Errorf("parse %s: %w", t, err)
		}
		var buf bytes.Buffer
		if err := tmpl.Execute(&buf, fx); err != nil {
			return "", fmt.Errorf("execute %s: %w", t, err)
		}
		dst := filepath.Join(outDir, outputPath(t, fx))
		if err := os.MkdirAll(filepath.Dir(dst), 0o755); err != nil {
			return "", fmt.Errorf("mkdir %s: %w", dst, err)
		}
		if err := os.WriteFile(dst, buf.Bytes(), 0o644); err != nil {
			return "", fmt.Errorf("write %s: %w", dst, err)
		}
	}

	return "", nil
}

// peruriGoModule returns the go-peruri-lib module path. Reads PERURI_GO_MODULE
// from the environment so a single edit to ../config.env can rehome the lib.
// The fallback matches today's go-peruri-lib go.mod declaration, so existing
// callers that don't source config.env keep working unchanged.
func peruriGoModule() string {
	if m := os.Getenv("PERURI_GO_MODULE"); m != "" {
		return m
	}
	return "sipgn-git.bgn.go.id/harry.sitohang/go-peruri-lib"
}

// peruriGoLibPath returns the local filesystem path of the go-peruri-lib
// clone. Reads PERURI_GO_LIB_PATH first (so callers that source ../config.env
// override correctly), falling back to ~/go/src/.../go-peruri-lib which
// matches the path used by the auto-sync script and the README's default.
func peruriGoLibPath() string {
	if p := os.Getenv("PERURI_GO_LIB_PATH"); p != "" {
		return p
	}
	home, err := os.UserHomeDir()
	if err != nil {
		return "/go/src/sipgn-git.bgn.go.id/harry.sitohang/go-peruri-lib"
	}
	return filepath.Join(home, "go", "src", "sipgn-git.bgn.go.id", "harry.sitohang", "go-peruri-lib")
}

// writeGoMod creates a go.mod that replaces the lib path with the local repo
// so `go build` resolves against the working tree, not a published version.
func writeGoMod(outDir, libPath, module string) error {
	libModule := peruriGoModule()
	body := fmt.Sprintf(`module %s

go 1.26.2

require %s v0.0.0

replace %s => %s
`, module, libModule, libModule, libPath)
	return os.WriteFile(filepath.Join(outDir, "go.mod"), []byte(body), 0o644)
}
