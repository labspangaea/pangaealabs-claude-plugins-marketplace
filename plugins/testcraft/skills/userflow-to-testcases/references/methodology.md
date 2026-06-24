# Authoring methodology — flow → test cases

Self-contained reference for turning a user-flow document into a complete, importer-ready
test-case suite. Organize around **state machines**, not screens — the defects that matter
live where state from one flow gates the next.

## 1. Model state before writing cases

From the source, extract the entities and their states as one or more state machines. Two
axes recur:
- an **actor/account** machine, e.g. `none(404) → unverified → active → suspended`
- a **resource** machine, e.g. `not-found(404) → inactive → active-empty → active-funded → deactivated`

Give each state a short code (`A0…An`, `C0…Cn`). Map each original "flow" or "step" in the
document to a **transition** between states. If the document only describes one entity, one
machine is fine; most real apps have at least an actor and a resource.

## 2. Author cases per transition

For every transition write, at minimum:
- the **happy path** (valid input → success),
- the **validation rejections** (each invalid input → graceful reject),
- the **edge inputs** (boundaries, idempotent retries, empty states),
- the **ownership/identity** checks (acting on someone else's resource).

Every case must state its **downstream impact** in the Expected column — what state it sets
and how that gates a *later* flow. This is the whole point. Examples: "PIN set here is the
PIN required at payment"; "wrong primary card → tops up the wrong card"; "a typo'd email
blocks both verification and every later OTP". A case with no downstream impact is incomplete.

## 3. Actor × resource matrix

Cross-product the machines. Each reachable cell (e.g. a suspended actor acting on a funded
resource) is a gate: assert the right gate fires *before* the resource state is even
evaluated. ID these `MX-<actor>-<resource>` (e.g. `MX-A1-C3`).

## 4. Teardown / deactivation

Model how an active resource becomes blocked — expiry, credential lockout, fraud, admin
action, migration. Each trigger is a separate case (`DEACT-*`). Assert what survives
(balance, etc.) and that every operation is blocked afterward.

## 5. End-to-end journeys

Chain transitions across both machines to prove state propagation over a full path
(`E2E-*`). Name the seam each one stresses; the failure usually shows up one transition
*after* the root cause.

## 6. Security / abuse pass (VAPT)

Independent of the functional cases, sweep each surface the flow exposes and write abuse
cases (`PT-*`). For authorized testing only — write test cases (attack input → risk →
expected secure behavior → recommended fix in the Expected column), never working exploits.
Surfaces to consider when the flow involves them:
- **auth** — brute force, user enumeration, weak secrets, verify-token weakness, session not
  revoked on reset/suspend, fixation, token tampering
- **OTP / secrets** — brute (small code space, no cap), leaked in response/logs, not bound to
  action/resource, replay, resend flooding, no expiry
- **ownership / enumeration** — sequential/guessable IDs → enumerate then claim; identity not
  matched to the issued record; claim/link another user's resource
- **credential / PIN** — brute at money actions, client-side-only checks, weak values
- **money** — amount tampering (negative/zero/decimal/overflow/over-max), payment-callback
  forgery, credit/idempotency replay, price tampering, double-spend race
- **authorization / IDOR** — object IDOR, order/transaction IDOR, cross-account reads, mass
  assignment of privileged fields
- **injection** — SQLi, stored XSS rendered into emails/receipts, header/template injection
- **rate-limit / transport** — registration/OTP flooding, CSRF on state-changing actions,
  missing TLS/HSTS, missing security headers (clickjacking)

## 7. Tag and severity-reason every case

- **Type** — `POS` valid input expecting success · `NEG` invalid input expecting rejection ·
  `VAPT` security/abuse input.
- **Outcome** — what a passing test proves:
  - `TN` good input correctly allowed (happy path)
  - `TP` invalid input correctly blocked (ordinary validation)
  - `FP` legit/edge input must NOT be wrongly rejected
  - `FN!` malicious/invalid input must NOT be wrongly accepted — security-critical
  - Rule of thumb: good+accept→`TN` · bad+reject→`TP` (ordinary) or `FN!` (security/money/
    ownership/auth stakes) · legit-edge+accept→`FP` · attack+reject→`FN!`.
- **Priority** — by blast radius, on the scale matching Type:
  - functional `P0`/`P1`/`P2`; VAPT `CRIT`/`HIGH`/`MED`/`LOW`
  - `P0`/`CRIT` = money loss, takeover, or blocks an entire flow with no workaround;
    `P1`/`HIGH` = major but narrower/recoverable; `P2`/`MED`/`LOW` = cosmetic/edge.
- **Severity_Reasoning** — one sentence naming the blast radius that justifies the priority
  (e.g. "Forged callback credits balance for free."), not a restatement of the title.
- **Transition** — the `From→To` code (`A1→A2`), a matrix cell (`A1×C3`), or `-` if not
  state-bound (most VAPT cases).

## 8. Confirmed conventions (defaults)

- Duplicate value on a uniqueness/identity field (email in use, reuse of a one-time token) →
  `NEG` / `FN!` (wrongly accepting breaches ownership/single-use).
- Benign empty-state / boundary edges (no-match search, removing the last item, amount at a
  limit) → `POS` / `FP`, usually low priority.
- Explicit attack payloads → `VAPT` / `FN!` on the VAPT priority scale.

## 9. IDs

Use a per-Group prefix + sequence: prefix = initials of the Group (`Top-Up`→`TU`,
`Account`→`AC`, single-word→first two letters), then `-01`, `-02`… within that group.
Matrix `MX-…`, teardown `DEACT-…`, journeys `E2E-…`, security `PT-…`. Keep IDs unique.

## 10. Ambiguity

You cannot ask the user mid-run. When the state model is ambiguous (what does "inactive"
mean? what deactivates a resource? is zero-balance distinct? what is "not active"?), pick the
**most defensible interpretation, state it as an assumption**, and collect every ambiguity in
the flow-notes sidecar so a human can confirm. Never invent behavior as fact — mark
unspecified behavior `⚠` in the notes. Never invent fake data; use real values from the source.

## Output schema (importer-ready)

Write a CSV with **exactly these columns, in this order** — they match what the
`testcase-importer` skill consumes, so the handoff is clean:

```
ID, Group, Type, Outcome, Priority, Severity_Reasoning, Transition, Title, Steps / Test Data, Expected Result + Downstream Impact / Fix
```

Every `Type`/`Outcome`/`Priority` value must be in the vocab above. Quote fields containing
commas. Then run `scripts/validate_cases.py` to confirm it's importer-ready before handing off.
