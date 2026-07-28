#!/usr/bin/env bash
# Self-test for the smoke runner. Validates 4 paths:
#   1. clean template, runner direct → exit 0, no stdout
#   2. broken template, runner direct → exit 1, "build failed" on stdout
#   3. clean template, smoke.sh wrapper → exit 0, no stdout
#   4. broken template, smoke.sh wrapper → exit 0, JSON with hookSpecificOutput on stdout
#
# Uses httphandler_echo.go.tmpl as the canary because it's required by exactly
# one combo (api-echo-postgres-redis), so the test runs fast.
#
# Run: bash .claude/hooks/smoke/self_test.sh
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SMOKE_DIR="$REPO_ROOT/.claude/hooks/smoke"
WRAPPER="$REPO_ROOT/.claude/hooks/smoke.sh"
TMPL="$REPO_ROOT/.claude/skills/create-go-app/references/httphandler_echo.go.tmpl"

if [ ! -f "$TMPL" ]; then
    echo "FAIL: canary template missing: $TMPL"
    exit 2
fi

BACKUP=$(mktemp)
cp "$TMPL" "$BACKUP"
trap 'cp "$BACKUP" "$TMPL"; rm -f "$BACKUP"' EXIT INT TERM

fail=0
pass() { printf '  \033[32mok\033[0m %s\n' "$1"; }
warn() { printf '  \033[31mFAIL\033[0m %s\n' "$1"; fail=1; }

inject_break() {
    # Append an obviously-broken Go declaration outside any template directive.
    # text/template renders it as-is; gc rejects it.
    printf '\nfunc brokenSyntax {\n' >> "$TMPL"
}

# Test 1
echo "Test 1: clean template, runner direct"
out=$(cd "$SMOKE_DIR" && go run . -template "$TMPL" 2>/dev/null)
rc=$?
[ "$rc" = "0" ] && pass "exit 0" || warn "exit code (want 0, got $rc)"
[ -z "$out" ] && pass "stdout empty" || warn "stdout non-empty: $out"

# Test 2
echo "Test 2: broken template, runner direct"
inject_break
out=$(cd "$SMOKE_DIR" && go run . -template "$TMPL" 2>/dev/null)
rc=$?
[ "$rc" = "1" ] && pass "exit 1" || warn "exit code (want 1, got $rc)"
case "$out" in
    *"build failed"*) pass "stdout contains 'build failed'" ;;
    *)                warn "stdout missing 'build failed' marker:\n${out}" ;;
esac

cp "$BACKUP" "$TMPL"

# Test 3
echo "Test 3: clean template, smoke.sh wrapper"
out=$(printf '{"tool_input":{"file_path":"%s"}}' "$TMPL" | "$WRAPPER")
rc=$?
[ "$rc" = "0" ] && pass "exit 0" || warn "exit code (want 0, got $rc)"
[ -z "$out" ] && pass "stdout empty" || warn "stdout non-empty: $out"

# Test 4
echo "Test 4: broken template, smoke.sh wrapper"
inject_break
out=$(printf '{"tool_input":{"file_path":"%s"}}' "$TMPL" | "$WRAPPER")
rc=$?
[ "$rc" = "0" ] && pass "wrapper exit 0 (always)" || warn "exit code (want 0, got $rc)"
case "$out" in
    *'"hookSpecificOutput"'*'"additionalContext"'*'build failed'*)
        pass "stdout is hookSpecificOutput JSON with build failure"
        ;;
    *)
        warn "stdout missing expected JSON structure:\n${out}"
        ;;
esac

cp "$BACKUP" "$TMPL"

if [ "$fail" -eq 0 ]; then
    echo
    echo "All self-tests passed."
else
    echo
    echo "Self-tests FAILED."
    exit 1
fi
