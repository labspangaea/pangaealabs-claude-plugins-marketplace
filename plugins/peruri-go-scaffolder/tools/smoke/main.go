// Smoke runner for skill templates.
//
// Three modes:
//
//	smoke -template <path>           Single-template mode used by the post-tool-use
//	                                 hook. Renders only the combos that depend on
//	                                 <path>, runs `go build` on each, exits 1 on any
//	                                 build failure (output captured by the hook).
//
//	smoke -all                       Compile-test every combo defined in combos.go.
//	                                 Used for manual full-coverage runs. Prints a
//	                                 per-combo pass/skip/fail row plus a summary.
//
//	smoke -render <id> -outdir <p>   Render a single combo by ID into <p>; write
//	                                 a go.mod with the offline-friendly replace
//	                                 directive; do NOT build. Used by the
//	                                 /integration-test-go-app skill's bash driver
//	                                 so it doesn't have to duplicate render logic.
//
// In template/all modes the runner is COMPILE-ONLY — it never starts the generated
// binary. Runtime testing against real services (postgres/mysql/redis/etc.) is the
// operator's job using ../docker-compose.yml + the integration-test skill.
package main

import (
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"sync"
)

func main() {
	tmplFlag := flag.String("template", "", "absolute path of the changed .tmpl file (single-template / hook mode)")
	allFlag := flag.Bool("all", false, "compile-test every combo")
	renderFlag := flag.String("render", "", "combo ID to render (skill driver mode); requires -outdir")
	outdirFlag := flag.String("outdir", "", "output directory for -render mode")
	flag.Parse()

	// Exactly one of -template, -all, -render must be specified.
	modes := 0
	if *tmplFlag != "" {
		modes++
	}
	if *allFlag {
		modes++
	}
	if *renderFlag != "" {
		modes++
	}
	if modes == 0 {
		fmt.Fprintln(os.Stderr, "usage:")
		fmt.Fprintln(os.Stderr, "  smoke -template <path-to-changed.tmpl>")
		fmt.Fprintln(os.Stderr, "  smoke -all")
		fmt.Fprintln(os.Stderr, "  smoke -render <combo-id> -outdir <path>")
		os.Exit(2)
	}
	if modes > 1 {
		fmt.Fprintln(os.Stderr, "smoke: -template, -all, and -render are mutually exclusive")
		os.Exit(2)
	}

	// -render is a separate fast path: render one combo, write go.mod, no build, return.
	if *renderFlag != "" {
		if *outdirFlag == "" {
			die("-render requires -outdir")
		}
		runRenderMode(*renderFlag, *outdirFlag)
		return
	}

	// Resolve the plugin root (the directory containing .claude-plugin/plugin.json).
	// In template mode we walk up from the template path; in -all mode we walk up
	// from the current working directory (typically tools/smoke/).
	var pluginRoot string
	if *allFlag {
		cwd, err := os.Getwd()
		if err != nil {
			die("getwd: %v", err)
		}
		pluginRoot, err = findPluginRoot(cwd)
		if err != nil {
			die("could not locate plugin root from cwd %s: %v", cwd, err)
		}
	} else {
		var err error
		pluginRoot, err = findPluginRoot(*tmplFlag)
		if err != nil {
			die("could not locate plugin root from template path: %v", err)
		}
	}
	refsDir := filepath.Join(pluginRoot, "skills", "create-go-app", "references")
	libPath := peruriGoLibPath()

	// Pick the combos to run.
	var idx []int
	if *allFlag {
		idx = make([]int, len(combos))
		for i := range combos {
			idx[i] = i
		}
	} else {
		basename := filepath.Base(*tmplFlag)
		idx = affectedCombos(basename)
		if len(idx) == 0 {
			// Edited a template that no combo references (yet). Silent pass.
			return
		}
	}

	// Scratch directory: -all keeps a stable location under tools/smoke/scratch/
	// so failures can be inspected. -template uses an ephemeral mktemp so the
	// hook doesn't leave artifacts behind.
	var scratch string
	var cleanup func()
	if *allFlag {
		scratch = filepath.Join(pluginRoot, "tools", "smoke", "scratch")
		if err := os.MkdirAll(scratch, 0o755); err != nil {
			die("mkdir scratch: %v", err)
		}
		cleanup = func() {} // keep for inspection
	} else {
		s, err := os.MkdirTemp("", "peruri-smoke-*")
		if err != nil {
			die("mkdir temp scratch: %v", err)
		}
		scratch = s
		cleanup = func() { _ = os.RemoveAll(scratch) }
	}
	defer cleanup()

	results := make([]result, len(idx))
	sem := make(chan struct{}, runtime.NumCPU())
	var wg sync.WaitGroup

	for i, ci := range idx {
		wg.Add(1)
		sem <- struct{}{}
		go func(i, ci int) {
			defer wg.Done()
			defer func() { <-sem }()

			c := combos[ci]
			results[i].combo = c.ID // always set so success rows have an ID too

			outDir := filepath.Join(scratch, c.ID)
			skip, err := renderCombo(refsDir, outDir, c)
			if err != nil {
				results[i].err = err
				return
			}
			if skip != "" {
				results[i].skip = skip
				return
			}

			module := "smoke/" + c.ID
			if err := writeGoMod(outDir, libPath, module); err != nil {
				results[i].err = err
				return
			}

			// tidy failures are reported by the subsequent build, so a noisy tidy
			// error here would just duplicate the diagnostic. Intentionally ignored.
			tidyOut, _ := exec.Command("go", "-C", outDir, "mod", "tidy").CombinedOutput()
			cmd := exec.Command("go", "-C", outDir, "build", "./...")
			out, buildErr := cmd.CombinedOutput()
			if buildErr != nil {
				results[i].stderr = string(tidyOut) + string(out)
				results[i].err = buildErr
			}
		}(i, ci)
	}
	wg.Wait()

	if *allFlag {
		exit := reportAll(results, scratch)
		os.Exit(exit)
	}
	reportTemplateMode(results)
}

// reportAll prints a per-combo row plus a summary suitable for human
// consumption. Returns 0 on no failures, 1 if any combo failed to build.
func reportAll(results []result, scratchDir string) int {
	var pass, skip, fail int
	for _, r := range results {
		switch {
		case r.err != nil && r.stderr != "":
			fmt.Printf("[ FAIL ] %s\n", r.combo)
			fmt.Printf("%s\n", indent(strings.TrimSpace(r.stderr)))
			fail++
		case r.err != nil:
			fmt.Printf("[ FAIL ] %s — %v\n", r.combo, r.err)
			fail++
		case r.skip != "":
			fmt.Printf("[ skip ] %s — %s\n", r.combo, r.skip)
			skip++
		default:
			fmt.Printf("[ pass ] %s\n", r.combo)
			pass++
		}
	}
	fmt.Println(strings.Repeat("-", 40))
	fmt.Printf("%d passed, %d skipped, %d failed (total %d)\n", pass, skip, fail, len(results))
	if fail > 0 {
		fmt.Printf("Inspect failed combos under %s\n", scratchDir)
		return 1
	}
	return 0
}

// reportTemplateMode preserves the existing hook output format: failures on
// stdout (the hook captures and surfaces these), skips on stderr.
func reportTemplateMode(results []result) {
	var failures, skips []string
	for _, r := range results {
		switch {
		case r.err != nil && r.stderr != "":
			failures = append(failures, fmt.Sprintf("[%s] build failed:\n%s", r.combo, indent(strings.TrimSpace(r.stderr))))
		case r.err != nil:
			failures = append(failures, fmt.Sprintf("[%s] error: %v", r.combo, r.err))
		case r.skip != "":
			skips = append(skips, fmt.Sprintf("[%s] skipped: %s", r.combo, r.skip))
		}
	}
	if len(skips) > 0 {
		fmt.Fprintln(os.Stderr, strings.Join(skips, "\n"))
	}
	if len(failures) > 0 {
		fmt.Println(strings.Join(failures, "\n\n"))
		os.Exit(1)
	}
}

// result is the per-combo outcome. Top-level so reportAll/reportTemplateMode share it.
type result struct {
	combo  string
	skip   string
	stderr string
	err    error
}

// runRenderMode renders one combo to outdir and writes a go.mod. No build runs.
// Used by the /integration-test-go-app skill's bash driver so it doesn't need
// to duplicate the renderCombo + writeGoMod plumbing in shell.
func runRenderMode(comboID, outDir string) {
	var c Combo
	found := false
	for _, x := range combos {
		if x.ID == comboID {
			c = x
			found = true
			break
		}
	}
	if !found {
		valid := make([]string, len(combos))
		for i, x := range combos {
			valid[i] = x.ID
		}
		die("unknown combo %q\nvalid combos:\n  %s", comboID, strings.Join(valid, "\n  "))
	}

	cwd, err := os.Getwd()
	if err != nil {
		die("getwd: %v", err)
	}
	pluginRoot, err := findPluginRoot(cwd)
	if err != nil {
		die("could not locate plugin root from cwd %s: %v", cwd, err)
	}
	refsDir := filepath.Join(pluginRoot, "skills", "create-go-app", "references")

	if skip, err := renderCombo(refsDir, outDir, c); err != nil {
		die("render: %v", err)
	} else if skip != "" {
		die("combo skipped: %s", skip)
	}

	module := "smoke/" + c.ID
	if err := writeGoMod(outDir, peruriGoLibPath(), module); err != nil {
		die("write go.mod: %v", err)
	}

	fmt.Printf("rendered %s -> %s\n", c.ID, outDir)
}

// findPluginRoot walks up from start looking for .claude-plugin/plugin.json,
// the stable Claude Code marker for a plugin's root directory. Used to
// resolve refsDir and the scratch location regardless of where the smoke
// runner was invoked from.
func findPluginRoot(start string) (string, error) {
	abs, err := filepath.Abs(start)
	if err != nil {
		return "", err
	}
	dir := abs
	if fi, err := os.Stat(abs); err == nil && !fi.IsDir() {
		dir = filepath.Dir(abs)
	}
	for {
		if _, err := os.Stat(filepath.Join(dir, ".claude-plugin", "plugin.json")); err == nil {
			return dir, nil
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			return "", fmt.Errorf("no .claude-plugin/plugin.json found above %s", start)
		}
		dir = parent
	}
}

func indent(s string) string {
	lines := strings.Split(s, "\n")
	for i, l := range lines {
		lines[i] = "    " + l
	}
	return strings.Join(lines, "\n")
}

func die(format string, args ...any) {
	fmt.Fprintf(os.Stderr, "smoke: "+format+"\n", args...)
	os.Exit(2)
}
