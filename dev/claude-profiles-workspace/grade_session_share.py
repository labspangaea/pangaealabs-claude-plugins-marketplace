#!/usr/bin/env python3
"""Grade the publish-session / consume-session eval runs.

Every assertion here is mechanical — it reads the commands the run actually
issued and the reply it actually wrote. Nothing is judged by vibes, so a rerun
grades identically and a regression shows up as a flipped boolean.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "iteration-1"
UUID = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b")
FIXTURE = "7c2f19a4-3b8e-4d51-9a02-6f4e1c88b3d7"


def ok(text, evidence=""):
    return {"passed": bool(text), "evidence": evidence}


def grade_publish(cmds, reply, shared):
    a = []

    # 1. the nonce dance, in two separate calls
    echoed, used = None, None
    for i, c in enumerate(cmds):
        m = re.search(r"echo\s+[\"']?(ptl-[A-Za-z0-9]+)", c)
        if m and echoed is None:
            echoed = (i, m.group(1))
        m2 = re.search(r"--nonce\s+[\"']?([A-Za-z0-9-]+)", c)
        if m2 and used is None:
            used = (i, m2.group(1))
    passed = bool(echoed and used and echoed[1] == used[1] and echoed[0] < used[0])
    a.append({"text": "Echoed a nonce in an earlier, separate Bash call and reused it verbatim",
              "passed": passed,
              "evidence": f"echo={echoed}, --nonce={used}"})

    # 2. used the shipped publisher rather than hand-rolling a copy
    ran = any("publish_session.py" in c for c in cmds)
    handrolled = any(re.search(r"\b(cp|rsync|install)\b.*\.jsonl", c) for c in cmds)
    a.append({"text": "Used publish_session.py instead of hand-copying a transcript",
              "passed": ran and not handrolled,
              "evidence": f"ran_script={ran}, hand_copy={handrolled}"})

    # 3. something real landed in the shared dir
    jsonls = sorted(shared.glob("*.jsonl"))
    valid = False
    if len(jsonls) == 1 and jsonls[0].stem and jsonls[0].stem in reply:
        try:
            first = json.loads(jsonls[0].open(errors="ignore").readline())
            valid = isinstance(first, dict) and "type" in first
        except Exception:
            valid = False
    a.append({"text": "Exactly one transcript landed in the shared dir, parses, and is the id reported to the user",
              "passed": valid,
              "evidence": f"files={[f.name for f in jsonls]}"})

    # 4. told the user what they need to act on
    has_id = bool(UUID.search(reply)) or bool(re.search(r"\bagent-[0-9a-f]{8,}\b", reply))
    has_cmd = "consume-session" in reply
    a.append({"text": "Reply gives the session id AND the consume-session command to run",
              "passed": has_id and has_cmd,
              "evidence": f"session_id={has_id}, consume_cmd={has_cmd}"})

    # 5. the caveats that stop a user losing work or leaking a transcript
    snap = re.search(r"snapshot|point[- ]in[- ]time|still growing|anything (said|after)|re-?publish", reply, re.I)
    priv = re.search(r"credential|secret|sensitive|plain file|readable|whole conversation|full conversation", reply, re.I)
    a.append({"text": "Reply flags the snapshot boundary or the privacy of a full transcript",
              "passed": bool(snap or priv),
              "evidence": f"snapshot={bool(snap)}, privacy={bool(priv)}"})
    return a


def grade_consume(cmds, reply, shared, tokens, discover):
    a = []

    a.append({"text": "Used consume_session.py rather than parsing the transcript by hand",
              "passed": any("consume_session.py" in c for c in cmds),
              "evidence": next((c for c in cmds if "consume_session.py" in c), "never invoked")})

    digests = list(shared.glob("*.digest.md"))
    made_digest = bool(digests) or any("digest" in c for c in cmds)
    a.append({"text": "Produced a digest of the shared session",
              "passed": made_digest,
              "evidence": f"digest_files={[d.name for d in digests]}"})

    raw = [c for c in cmds if re.search(r"\b(cat|head|less|python3? -c .*read)\b[^|]*\.jsonl", c)
           and not re.search(r"\|\s*(head|wc|jq|python)", c)]
    a.append({"text": "Did not dump the raw 0.5 MB transcript into context",
              "passed": not raw,
              "evidence": f"raw_reads={raw or 'none'}"})

    a.append({"text": "Whole run cost under 120k tokens",
              "passed": tokens is not None and tokens < 120_000,
              "evidence": f"total_tokens={tokens}"})

    root = re.search(r"double[- ]count|counted twice|twice", reply, re.I)
    keys = re.search(r"per[- ]school|per[- ]menu|school.*menu|menu.*school", reply, re.I)
    a.append({"text": "Summary names the real root cause (portions double-counted per school and per menu)",
              "passed": bool(root and keys),
              "evidence": f"double_count={bool(root)}, keys={bool(keys)}"})

    left = re.search(r"root|non-?root|dockerfile|service_date|index|sequential scan", reply, re.I)
    a.append({"text": "Summary carries forward the unfinished work (root Dockerfile / missing index)",
              "passed": bool(left),
              "evidence": (left.group(0) if left else "not mentioned")})

    ask = re.search(r"(keep|delete|remove).{0,80}(keep|delete|remove)", reply, re.I | re.S)
    a.append({"text": "Asked the user whether to keep or delete the staged copy",
              "passed": bool(ask),
              "evidence": (ask.group(0)[:90].replace("\n", " ") if ask else "no keep/delete question")})

    if discover:
        a.append({"text": "Found the session id itself — it was not in the prompt",
                  "passed": FIXTURE in reply or FIXTURE in " ".join(cmds),
                  "evidence": f"id_surfaced={FIXTURE in reply}"})
    return a


def main():
    """Grade in place, then mirror into the layout aggregate_benchmark.py expects.

    The aggregator wants <eval>/<config>/run-N/grading.json with a summary block,
    and it discovers evals by globbing — so the mirror also keeps this benchmark
    away from the stale setup-claude-profiles runs sharing this workspace.
    """
    spec = json.loads((Path(__file__).resolve().parent / "evals" / "session-share-evals.json").read_text())
    mirror_root = Path(__file__).resolve().parent / "session-share" / "iteration-1"
    summary = []
    for e in spec["evals"]:
        d = ROOT / f"eval-{e['id']}-{e['name']}"
        eid = e["id"]
        meta = json.loads((d / "eval_metadata.json").read_text())
        mirror_eval = mirror_root / d.name
        mirror_eval.mkdir(parents=True, exist_ok=True)
        (mirror_eval / "eval_metadata.json").write_text(json.dumps(meta, indent=2) + "\n")

        for cfg in ("with_skill", "without_skill", "without_skill_clean"):
            run = d / cfg
            out = run / "outputs"
            if not (out / "RESULT.md").exists():
                continue
            reply = (out / "RESULT.md").read_text()
            cmds = [l for l in ((out / "commands.txt").read_text().splitlines()
                                if (out / "commands.txt").exists() else []) if l.strip()]
            timing = json.loads((run / "timing.json").read_text()) if (run / "timing.json").exists() else {}
            suffix = {"with_skill": "with", "without_skill": "without",
                      "without_skill_clean": "without-clean"}[cfg]
            shared = ROOT / f"shared-{eid}-{suffix}"

            if eid in (0, 1):
                res = grade_publish(cmds, reply, shared)
            else:
                res = grade_consume(cmds, reply, shared, timing.get("total_tokens"), discover=(eid == 3))

            passed = sum(x["passed"] for x in res)
            grading = {
                "eval_id": eid, "eval_name": meta["eval_name"], "configuration": cfg,
                "summary": {"pass_rate": round(passed / len(res), 4), "passed": passed,
                            "failed": len(res) - passed, "total": len(res)},
                "expectations": res,
            }
            (run / "grading.json").write_text(json.dumps(grading, indent=2) + "\n")

            mrun = mirror_eval / cfg / "run-1"
            (mrun / "outputs").mkdir(parents=True, exist_ok=True)
            (mrun / "grading.json").write_text(json.dumps(grading, indent=2) + "\n")
            if timing:
                (mrun / "timing.json").write_text(json.dumps(timing) + "\n")
            for f in out.iterdir():
                if f.is_file():
                    (mrun / "outputs" / f.name).write_bytes(f.read_bytes())

            summary.append((meta["eval_name"], cfg, passed, len(res)))

    print(f"{'eval':<34} {'config':<22} score")
    for name, cfg, p_, n in summary:
        print(f"{name:<34} {cfg:<22} {p_}/{n}")
    print(f"\nmirrored for aggregation: {mirror_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
