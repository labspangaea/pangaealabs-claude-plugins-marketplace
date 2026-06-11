#!/usr/bin/env python3
"""Triggering eval for the make-pdf skill description — corrected for CC 2.1.x.

This is a drop-in replacement for skill-creator's `run_eval.py` that fixes the
detector bug which made the stock harness report an all-negative "the stub never
triggers in 2.1.x" artifact. See dev/docsmith-workspace/run_eval.py.patch for the
minimal upstream diff, and CLAUDE.md ("Skill-description optimizer", gotcha 3) for
the full root-cause writeup.

What it measures
----------------
For each query it drops ONE shared `.claude/commands/make-pdf-skill-eval.md` stub
(carrying the description under test) into the project root, runs a real
`claude -p "<query>"` with stream-json, and records whether the model selects that
stub via the Skill (or Read) tool. Result is compared to `should_trigger`.

Two fixes vs the stock harness
------------------------------
1. ONE shared persistent stub for the whole run, not a per-worker `-<uid>` stub.
   With concurrent workers each writing their own uid stub, a worker checking for
   *its own* uid misses when the model picks a sibling worker's stub -> false miss.
2. Scan ALL assistant turns; conclude "not triggered" only at the top-level
   `result` event. The stock harness returns False on the first `message_stop`
   (or first non-Skill/Read tool), but on CC 2.1.x the model inspects the input
   file in turn 1 and selects the skill in turn 2 -> the stock detector bails
   before the selection and under-counts.

Usage (MUST be isolated — see CLAUDE.md gotchas 1 & 2)
------------------------------------------------------
    # one-time: authenticate a plugin-free config dir
    CLAUDE_CONFIG_DIR=/tmp/sc-iso-config claude /login

    # seed the input files the should-trigger queries reference, then run from a
    # throwaway cwd (never from under the marketplace checkout):
    cd /tmp/sc-iso-proj
    CLAUDE_CONFIG_DIR=/tmp/sc-iso-config python3 run_trigger_eval.py \
        --eval-set dev/docsmith-workspace/trigger-evals.json \
        --skill-md plugins/docsmith/skills/make-pdf/SKILL.md \
        --project-root /tmp/sc-iso-proj --model sonnet --runs 2

A description override can be passed with --description to test a candidate
without editing SKILL.md.
"""
import argparse
import json
import os
import re
import select
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

STUB_TOKEN = "make-pdf-skill-eval"  # single shared stub name; detector greps for this


def parse_skill_md(skill_md: Path) -> tuple[str, str]:
    """Return (name, description) from a SKILL.md frontmatter block."""
    text = skill_md.read_text()
    fm_match = re.search(r"^---\s*\n(.*?)\n---", text, re.S)
    if not fm_match:
        raise ValueError(f"No YAML frontmatter found in {skill_md}")
    fm = fm_match.group(1)
    name_match = re.search(r"name:\s*(.*)", fm)
    desc_match = re.search(r"description:\s*(.*)", fm, re.S)
    if not name_match or not desc_match:
        raise ValueError(f"frontmatter missing name/description in {skill_md}")
    name = name_match.group(1).strip()
    # description may be one long line; cut at the next top-level frontmatter key
    desc = re.split(r"\n[a-zA-Z0-9_-]+:\s", desc_match.group(1).strip())[0].strip()
    return name, desc


def run_single(query: str, token: str, timeout: int, project_root: str, model: str | None) -> bool:
    """Run one `claude -p` and return whether the model selected the stub skill."""
    cmd = ["claude", "-p", query, "--output-format", "stream-json",
           "--verbose", "--include-partial-messages"]
    if model:
        cmd += ["--model", model]
    # Drop CLAUDECODE so a nested `claude -p` is allowed; keep CLAUDE_CONFIG_DIR.
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                            cwd=project_root, env=env)
    assert proc.stdout is not None
    cur_tool: str | None = None
    acc = ""
    buf = ""
    start = time.time()
    try:
        while time.time() - start < timeout:
            if proc.poll() is not None:
                buf += proc.stdout.read().decode("utf-8", "replace")
            else:
                ready, _, _ = select.select([proc.stdout], [], [], 1.0)
                if not ready:
                    continue
                chunk = os.read(proc.stdout.fileno(), 8192)
                if not chunk:
                    break
                buf += chunk.decode("utf-8", "replace")
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                etype = event.get("type")
                if etype == "stream_event":
                    se = event.get("event", {})
                    st = se.get("type", "")
                    if st == "content_block_start":
                        cb = se.get("content_block", {})
                        cur_tool = cb.get("name", "") if cb.get("type") == "tool_use" else None
                        acc = ""
                    elif st == "content_block_delta" and cur_tool:
                        delta = se.get("delta", {})
                        if delta.get("type") == "input_json_delta":
                            acc += delta.get("partial_json", "")
                            if cur_tool in ("Skill", "Read") and token in acc:
                                return True
                    elif st in ("content_block_stop", "message_stop"):
                        # message_stop ends ONE turn, not the run — keep scanning.
                        cur_tool, acc = None, ""
                elif etype == "assistant":
                    # full-message fallback: catch a Skill/Read selection in any turn
                    for c in event.get("message", {}).get("content", []):
                        if c.get("type") == "tool_use" and c.get("name") in ("Skill", "Read"):
                            if token in json.dumps(c.get("input", {})):
                                return True
                elif etype == "result":
                    return False  # run finished without selecting the stub
            if proc.poll() is not None and "\n" not in buf:
                break
        return False
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--eval-set", required=True, help="Path to trigger-evals.json")
    ap.add_argument("--skill-md", required=True, help="Path to the skill's SKILL.md")
    ap.add_argument("--description", default=None, help="Override description to test")
    ap.add_argument("--project-root", required=True,
                    help="Throwaway cwd that holds .claude/commands (NOT the repo)")
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--timeout", type=int, default=150)
    ap.add_argument("--runs", type=int, default=2, help="Runs per query")
    args = ap.parse_args()

    eval_set = json.loads(Path(args.eval_set).read_text())
    name, desc = parse_skill_md(Path(args.skill_md))
    if args.description:
        desc = args.description.strip()

    cdir = Path(args.project_root) / ".claude" / "commands"
    cdir.mkdir(parents=True, exist_ok=True)
    stub = cdir / f"{STUB_TOKEN}.md"
    indented = "\n  ".join(desc.split("\n"))
    stub.write_text(
        f"---\ndescription: |\n  {indented}\n---\n\n# {name}\n\nThis skill handles: {desc}\n"
    )
    print(f"skill={name} desc_len={len(desc)} runs={args.runs} "
          f"workers={args.workers} model={args.model}", file=sys.stderr)

    try:
        jobs = [(it["query"], STUB_TOKEN, args.timeout, args.project_root, args.model)
                for it in eval_set for _ in range(args.runs)]
        results: dict[str, list[bool]] = {}
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = {ex.submit(run_single, *job): job for job in jobs}
            for fut in as_completed(futs):
                query = futs[fut][0]
                try:
                    results.setdefault(query, []).append(bool(fut.result()))
                except Exception as exc:  # keep going; count as a miss
                    print(f"  ! {query[:48]}: {exc}", file=sys.stderr)
                    results.setdefault(query, []).append(False)
    finally:
        stub.unlink(missing_ok=True)

    items = {it["query"]: it for it in eval_set}
    rows = []
    tp = tn = fp = fn = 0
    for query, trigs in results.items():
        should = items[query]["should_trigger"]
        rate = sum(trigs) / len(trigs)
        did = rate >= 0.5
        ok = did == should
        if should and did:
            tp += 1
        elif should and not did:
            fn += 1
        elif not should and did:
            fp += 1
        else:
            tn += 1
        rows.append((ok, should, did, rate, sum(trigs), len(trigs), query))

    rows.sort(key=lambda r: (r[1], not r[0]), reverse=True)
    print("\n=== TRIGGER EVAL (corrected detector) ===", file=sys.stderr)
    for ok, should, did, _rate, t, n, query in rows:
        print(f"[{'PASS' if ok else 'FAIL'}] want={'Y' if should else 'N'} "
              f"got={'Y' if did else 'N'} {t}/{n}  {query[:62]}", file=sys.stderr)
    total = len(rows)
    passed = sum(1 for r in rows if r[0])
    print(f"\nPASS {passed}/{total}   TP={tp} TN={tn} FP={fp} FN={fn}", file=sys.stderr)
    print(f"  should-trigger recall  : {tp}/{tp + fn}", file=sys.stderr)
    print(f"  no-trigger specificity : {tn}/{tn + fp}", file=sys.stderr)

    print(json.dumps({
        "model": args.model, "runs": args.runs, "passed": passed, "total": total,
        "confusion": {"TP": tp, "TN": tn, "FP": fp, "FN": fn},
        "rows": [{"pass": r[0], "should_trigger": r[1], "did_trigger": r[2],
                  "rate": r[3], "triggers": r[4], "runs": r[5], "query": r[6]}
                 for r in rows],
    }, indent=2))


if __name__ == "__main__":
    main()
