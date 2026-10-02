# PHASE022 REQUIRED CORRECTIONS (Independent Adversarial Audit)

**Date**: 2026-09-20. The auditor describes corrections but implements none,
per the audit's absolute rules. Items are ordered by severity.

## A. ENGINEERING (release-blocking; archive must be rebuilt)

### A1. Fix the competition entrypoint (P0 -- the submission does not run)

- **Defect**: packaged `main.py` uses `__file__` at module top; Kaggle's loader
  `exec`s agent sources in a bare namespace without `__file__`, so every step
  raises `NameError`, every action is an exception object coerced to PASS, and
  the submission scores $3,000.00 (starting money) deterministically.
- **Correction**: resolve the submission root without `__file__` at import
  time (KE injects `configuration["__raw_path__"]` on every call; add
  `os.getcwd()`/`sys.path` fallbacks for non-KE harnesses). Retire archive
  hash `2b23bc22...`; rebuild; re-verify.
- **Also fix the QA** (`scripts/build_phase022_submission.py`): assert reward
  far above starting money (e.g. > $10,000 vs starter); run head-to-head vs
  the V3 reference in KE and require V3-scale rewards; surface agent stderr
  (fail on any agent-side exception); flag >2x latency deviation from
  validation; record both players' rewards.

### A2. Re-verify packaged determinism and behavior after A1

- The current "$3,000 == $3,000" check is void (dead-agent equality). Re-run
  packaged determinism plus a packaged-vs-kagsim behavioral correspondence
  check on at least one reference seed before any release claim.

### A3. Commit the release (provenance)

- HEAD is `15c0f29` (Phase 021); all V22 code, scripts, reports, and the
  archive are uncommitted (528 working-tree entries). Tag a release commit so
  "audited == packaged" is pinned by hash, not by timing.

## B. SCIENTIFIC WORDING (documentation corrections; no re-tuning)

### B1. Statistics (fresh validation + final report + manifest rationale)

- Replace "statistically significant (p < 0.05)" headlines with: "nominal
  two-sided Wilcoxon p = 0.034 on match-level deltas (N=40); two-sided t-test
  p = 0.86; no Phase 022 preregistration exists and the program's documented
  primary (one-sided t) is non-significant."
- Disclose the seed-level reading alongside: "seed-mean aggregation (N=20):
  Wilcoxon p = 0.051, t p = 0.024, median $0."
- Delete "robust", "decisively confirms", "Stable positive shift" (d = 0.03
  is negligible; gain is 0.035% of mean reward).
- Present +$33.35 strictly as the sample mean with its zero-spanning CI, not
  as an established population effect.
- Restrict "FOUNDATION QUALIFIED" to "passed the author's stated Wilcoxon
  gate" with the full four-test table adjacent.

### B2. Attribution

- Cut "100% of the active empirical alpha" and "necessary and sufficient
  driver" to: "the only mechanism with measurable incremental effect in this
  cohort and design (+$35.50 marginal vs timing-off arms)."
- Cut "proven defense-in-depth" / "zero regression" for Liq/Shutdown to: "no
  evidence of regression in this cohort (neither mechanism triggered a
  committable candidate); live protective value unproven."
- Persist per-arm match ledgers on any future run (currently summaries only).

### B3. Counterfactual fidelity

- Withdraw the empirical MAE = $0.00 validation claim (tautological by
  construction: `win_model.py:373-374`). Rewrite the section as architecture
  description; delete "audited against realized match outcomes",
  "bit-exact mathematical fidelity", "r = 1.0000" as evidence.
- Delete per-commit "Impact on Match" attributions lacking decomposition.

### B4. Determinism

- Cut "720/720 steps bit-identical" and "zero sources of nondeterminism
  remain" to what was checked: "10/10 aggregate comparisons (rewards, delta,
  commit counts) identical across 5 seeds x 3 runs; per-step trajectory
  identity not compared."

### B5. Performance

- Delete "sub-100ms turn latencies" and "zero risk of timeout". Accurate text:
  "median 50.89 ms, mean 75.76 ms; P95 229.40 ms, P99 404.87 ms, max
  2,346.68 ms -- all within the 1,000 ms Kaggle budget except the max, whose
  step is unidentified in the exported aggregates; the config's own 100 ms
  limit (`within_limit=false`) is breached."
- Delete the 9-stage pipeline table (unsourced; telemetry has 6 fields) or
  re-source it from new instrumentation.
- Fix step counts: 719 decision steps/match (kagsim `sim.hpp:359`), 28,760
  total -- not "720-step matches" / "28,800 steps".
- Qualify step-0-max and 1.8/2.5 ms fast-path figures as unverified (no
  per-step export).

### B6. Safety

- Replace "0 safety violations" with: "no unsafe commits observed; the
  `safety_violations` counter is structurally zero (no rejection string
  contains SAFETY_FAIL) and cannot detect fail-open."
- Correct the macro-test description (no livestock/feed-deficit was
  constructed; the test asserts almost nothing) and strengthen or drop the
  tautological assertions (cash/market/worker tests).
- Disclose that `purchase_ok` and `market_collision_ok` certificate fields are
  never evaluated (fail-open defaults), and that LIQ/SHUT live paths never
  executed in validation.
- Note the in-flight continuation path skips re-verification (unreachable
  under the qualified config; latent otherwise).

### B7. Autonomy/optimality language

- Keep the honest "not end-to-end trained" demarcation. Cut "mathematically
  proven superior and safe", "proven Pareto-optimal", "confirmed optimal",
  "This proves", "optimal TSP routes", "mathematically optimal / empirical
  ceiling", "highly accretive", "Scientifically Proven" to evidence-graded
  phrasing ("simulator-superior under the evaluated horizon", "heuristic
  scheduler", "best validated configuration to date").
- Cut "thousands of abstention records are fully serialized" (only 34 COMMIT
  records exported; rejected candidates and abstentions unexported).

### B8. Holdouts and cohorts

- Retract "100% Untouched" for 340300..340349: EXP-AEC-004 executed 100
  matches there (Sept 18). Re-designate the tournament cohort; never reuse.
  (340050..340199 and 214200..214249 remain clean to the best of the audit's
  repo-wide 6-digit search.)
- Soften "100% pristine / never previously executed" for 249376..249395 to
  "no prior gameplay, tuning, or selection on this cohort" (pre-run tests
  constructed `kagsim.Game(249376)` initial state -- immaterial, but literal).
- Fix historical table rows (P019 4/6/0, P020 0/10/0 over claimed N=20):
  disclose the per-seed vs per-match unit.
- Add a reconciliation note for P20 "market timing ELIMINATED (-$60.03)"
  vs V22 "timing drives +$35.50" (different cohorts; diagnostic probes vs
  live commits).

### B9. Governance registry

- Align `MECHANISM_REGISTRY` statuses with prose or vice versa: tranche and
  asset-holding are `EXPERIMENTAL`, not `QUARANTINED`; they are absent from
  `QUARANTINED_MECHANISMS`; several `ACTIVE`/`DEVELOPMENT` entries sit inside
  the quarantine tuple. Replace "unreachable through configuration" with
  "disabled by default in the qualified config and blocked at three
  enforcement layers; reachable only via explicit research configs."
- Implement or remove vacuous safety predicates; fix the `safety_violations`
  metric to count rejected/committed-unsafe events it can actually observe.

## C. RED-TEAM ATTACK SUMMARY (all attacks executed; see main report)

1. +$33.35 effect: numbers exact; inference fragile (seed-level Wilcoxon
   p=0.051; no prereg; primary-test convention fails). Downgrade, don't discard.
2. Market-timing causality: enforcement valid; identical arms explained;
   generality overclaimed. Scope to cohort.
3. Safety: fail-closed structure verified; suite weaker than reported; metrics
   vacuous in parts. Qualify.
4. Determinism: aggregate equality verified (plus FULL-arm re-execution);
   trajectory identity unverified. Scope the claim.
5. Fidelity: KILLED as empirical validation (tautology). Withdraw.
6. Autonomy: honest core, overclaimed adjectives. Trim.
7. Standalone submission: KILLED as packaged (dead under KE). Rebuild.

Unresolved risks after corrections: live LIQ/SHUT behavior; per-arm ledgers;
per-step latency attribution; full-suite re-execution (Windows-only kagsim).
