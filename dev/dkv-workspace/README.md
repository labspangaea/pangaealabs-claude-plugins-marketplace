# dkv eval workspace

- `evals/evals.json` — output-quality eval prompts (3 cases + a 4th coverage case added in iter-3)
- `grade_mechanical.py` — the countable half of grading; the judgment half is graded by reading
- `run_trigger_eval.py` — copy of the corrected docsmith harness with a neutral `STUB_TOKEN`
  (`design-skill-eval`). The docsmith original hardcodes `make-pdf-skill-eval`, whose *name* would
  bias any PDF-related negative in a design eval set.
- `trigger-evals.json` — 20 triggering queries, 10 positive / 10 near-miss negative

## The trigger runs here are INVALID — do not cite them

`trigger-run-v1-INVALID.json`, `trigger-run-v2-INVALID.json` and
`trigger-control-docsmith-INVALID.json` were all run against the *normal* config, without the
plugin-free `CLAUDE_CONFIG_DIR` that `CLAUDE.md` mandates. A dozen competing design skills
(`impeccable`, `frontend-design`, `high-end-visual-design`, …) get selected instead of the test
stub, and the detector counts only the stub, so correct selections record as misses.

The docsmith control proves it: same description and eval set that `CLAUDE.md` records at 7/10
recall scored **0/10** under these conditions. Kept only as evidence of the failure mode.

To run this properly you need a fresh `CLAUDE_CONFIG_DIR` authed via `claude /login` — which was
unavailable in the environment where these were attempted.
