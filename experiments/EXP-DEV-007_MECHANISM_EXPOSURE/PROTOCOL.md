# EXP-DEV-007_MECHANISM_EXPOSURE — FROZEN PROTOCOL

## Prospective Mechanism-Exposure Study of the Frozen DEV-006 H=500 Guard

**Document Identifier**: `PROTOCOL.md`
**Experiment Identifier**: `EXP-DEV-007_MECHANISM_EXPOSURE`
**Date**: 2026-09-15
**Status**: PRE-REGISTRATION FREEZE (committed before any runner exists and
before any experimental seed executes)
**Governance Authority**: Zero-Leakage Governance
**Prior experiment**: EXP-DEV-006 (Discovery INCONCLUSIVE→Category A;
Qualification INCONCLUSIVE; guard inert 0/50 on 50050–50099)

### Frozen identity

| Artifact | Path | SHA-256 (frozen) |
|---|---|---|
| Baseline V54++ (Sub 56146971) | `candidates/compiled_v54_plus_residual.py` | `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb` |
| Treatment DEV-006 | `candidates/closed_loop_architecture/dev_006_horizon_guard_scheduler.py` | `06db94e59e2c271b5490aad78fdb760bd8a250f28ec4407de2d2f6be0644f5eb` |
| Diagnostic DEV-005 | `candidates/closed_loop_architecture/dev_005_confirmed_shop_scheduler.py` | `f52b168619e47bea6a052faff890fc84804cb39b47392d247139967f910e2a78` |
| Control (Sub 56146947) | `candidates/compiled_v54_plus_shop.py` | `f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8` |

**Cohort**: seeds 310000–310499 inclusive, N=500 (fixed by
`SEED_SELECTION_RULE.md`, certified by `SEED_PROVENANCE.md`).
**Design**: 4 games per seed (primary arm DEV-006 vs baseline × 2 seats;
diagnostic arm DEV-005 vs baseline × 2 seats; identical CRN) = 2,000 games.

---

## 1. Purpose and research questions

This experiment characterizes the H=500 late-entry mechanism WITHOUT
post-hoc seed selection. It does not optimize H, test H2, or modify any
treatment. It answers:

1. How frequently does the pre-defined late-entry condition naturally occur?
2. When it occurs, does frozen DEV-006 prevent the downstream damage seen in
   prior Discovery?
3. How large is the conditional DEV-005 → DEV-006 effect among exposed
   episodes?
4. How much does that mechanism matter to unconditional expected reward?

Q1–Q3 are mechanism questions (Estimands 2–3). Q4 is an economic question
(Estimand 1). They are reported separately and never collapsed into one score.

## 2. Treatment (frozen, no modification)

- Treatment: DEV-006 exactly as frozen (`06db94e5…`). One-factor difference
  vs DEV-005: `HORIZON_GUARD_THRESHOLD = 500`; a NEW specialization
  (BASELINE_BACKBONE → specialized) is rejected when `720 − step < 500`.
- Diagnostic comparator: DEV-005 exactly as frozen (`f52b1686…`).
- Performance baseline: V54++ residual exactly as frozen (`18402ec6…`).
- Explicitly forbidden: any H change, H sweep, H2, runway model, threshold
  retuning, route change, YARN exception, or any edit to the three frozen
  source files. Any such idea requires a NEW experiment identity.

## 3. Background incidence (context, not selection)

Observed trigger incidence to date: retrospective 247xxx 2/50; Discovery
248xxx 2/50; Qualification 50050–50099 0/50. Fresh-cohort combined: 2/100.
Every observed trigger was a first-time step-288 YARN entry on 4th-shop
reveal. These facts motivated the exposure design and the N=500 choice
(see `POWER_PLANNING.md`); they were NOT used to select seeds.

## 4. Trigger definition (frozen before execution)

### 4.1 Exact predicate (validated against source, 2026-09-15)

A **qualifying late-entry exposure** occurs in a seed×match of the DEV-005
diagnostic arm when ALL of the following hold at a planning checkpoint s:

1. s ∈ {72, 144, 216, 288} (the `act()` checkpoint dispatch; step from
   `obs["step"]`, else `24*day + hour`).
2. `best_delta >= TAU` (1500.0), where best is taken over non-backbone plans
   of (plan value − backbone value) with strict `>` selection from 0.0.
3. `money >= L_MIN` (100.0) at checkpoint s.
4. `is_confirmed`: `ROUTE_REQUIRED_SHOPS[best_plan]` ∈ currently observed
   `unlocked_shops` at s.
5. `720 − s < 500` (on the frozen grid this holds iff s = 288).
6. `active_plan == "BASELINE_BACKBONE"` at checkpoint entry (a
   BASELINE→specialized **transition event**, not maintenance of a
   pre-existing specialization).
7. `best_plan != "BASELINE_BACKBONE"` (implied by (ii) since TAU > 0;
   stated for completeness).

Conditions (i)–(iv)+(vii) are exactly DEV-005's `SPECIALIZE_CONFIRMED`
predicate (`dev_005…py` gating block); (v)–(vi) are the guard-relevant
restrictions from DEV-006's `REJECT_HORIZON` branch. No additional hidden
conditions exist: the best-plan loop, confirmation gate, and checkpoint
dispatch were read in full. In particular, "first-time" in (vi) means
active-plan-at-entry is BASELINE — a re-entry after an earlier
specialize-then-revert would also satisfy (vi) and would also fire the
guard; early-specialization history is recorded as a covariate (§6.3) so
first-entry vs re-entry can be distinguished forensically.

### 4.2 Operational detection (from pre-treatment decision state)

From the DEV-005 arm's `decision_events` for a seed×match:

- a row with `step == 288`, `decision == "SPECIALIZE_CONFIRMED"`,
  `best_candidate_plan != "BASELINE_BACKBONE"`, and prior active plan
  BASELINE, where prior active plan = that seed×match's step-216 row
  `active_plan_after` (every checkpoint appends exactly one row, so the
  step-216 row always exists).
- `trigger_step`, `specialization` (= best_candidate_plan), `shop_state`
  (= current_shops), `cash_before_entry` (= liquidity),
  `expected_incremental_value`, and the early-specialization flag (any
  SPECIALIZE_CONFIRMED at 72/144/216 in the same seed×match) are recorded
  from the same pre-treatment telemetry.

### 4.3 Seed-level aggregation

- `trigger_occurs(seed)` = qualifying event in ≥1 of the 2 DEV-005 matches.
- The seed is the primary incidence unit (consistent with the paired design).
  Per-match exposure is recorded as secondary detail.

### 4.4 What the trigger is NOT

The trigger is a **decision-state event**, not a reward outcome. It is NOT
"seeds where DEV-005 lost", NOT "seeds where DEV-006 won", NOT any function
of terminal reward, and it must not be redefined after outcomes are observed.

### 4.5 Pre-registered integrity cross-checks

- C1: every trigger seed×match shows `REJECT_HORIZON` at step 288 in the
  DEV-006 arm at the same seed×match×step.
- C2: pre-288 decision histories (72/144/216) are identical across arms on
  trigger seeds.
- C3: every DEV-006 `REJECT_HORIZON` corresponds to a DEV-005 trigger event.
- C4 (purity): DEV-006−DEV-005 paired contrast ≠ 0 only on trigger-exposed
  seeds.
- Any violation → STOP all interpretation and investigate as a possible
  one-factor breach before proceeding.
- A trigger event at any step other than 288 contradicts the frozen-grid
  analysis; it is recorded and investigated as an integrity anomaly.

## 5. Estimands and analysis plan

Primary unit: seed, paired over 2 seats. Tie rule: delta == 0.0 exactly.
Percentiles: linear interpolation (DEV-006 `pct()`); p-values: two-sided
Student-t via `scipy.stats.t.sf` (df = N−1); CIs: Student-t with df = N−1.

### ESTIMAND 1 — UNCONDITIONAL PERFORMANCE (DEV-006 − baseline, all N seeds)

Per-seed paired delta Δ⁶ᵢ = 0.5(Δ⁶ᵢ,₀ + Δ⁶ᵢ,₁). Report: N, mean, median, SD
(n−1), SE, t, two-sided p, 95% CI, 10% trimmed mean, p01/p05/p10/p25/p50/
p75/p90/p95/p99, min, max, W/L/T + rates, nonzero count, mean-ex-best,
mean-ex-top2. Answers Q4.

### ESTIMAND 2 — TRIGGER INCIDENCE

k = #{seeds with trigger_occurs}; estimate P(trigger) = k/N with an exact
Clopper-Pearson 95% CI. Secondary: per-match rate with CI; trigger-step and
specialization distributions. Answers Q1.

### ESTIMAND 3 — CONDITIONAL MECHANISM EFFECT (trigger-exposed seeds only)

Among the k exposed seeds, for the mechanism contrast (DEV-006−DEV-005
paired), DEV-005 damage (DEV-005−baseline), and DEV-006 residual
(DEV-006−baseline): mean, median, SD, 95% CI (Student-t, labeled descriptive
when k is small), min, max, W/L/T of the contrast; guard-firing concordance
(pre-registered expectation: 100%); counts of full prevention (DEV-006 ==
baseline exactly), partial prevention, no prevention, and exposed-seed harm
(contrast < 0). Answers Q2–Q3.

**Causal language rule**: trigger exposure is endogenous to game state (shop
reveals, model values, liquidity). Estimand 3 is reported ONLY as the
"conditional paired effect among prospectively defined trigger-exposed
episodes" (and, separately, the unconditional Estimand 1). The words "causal
treatment effect" must not be used for Estimand 3.

## 6. Per-seed capture

### 6.1 Every seed

seed, trigger_occurs, trigger_step, specialization, shop_state,
cash_before_entry, expected_incremental_value, early_specialization_flag,
remaining_horizon (= 720 − trigger_step), DEV005_plan, DEV006_plan,
guard_fired, DEV005_reward, DEV006_reward, baseline_reward (per match and
paired), DEV005_minus_baseline, DEV006_minus_baseline, DEV006_minus_DEV005,
terminal_cash, terminal_liquidity, terminal inventory detail as instrumented.

### 6.2 Every trigger-exposed seed (extended)

Route before/after entry, animal-purchase tape deltas, maintenance/feed
burden, harvest/service events, market sales, dead-inventory proxies, worker
utilization as instrumented, time-to-recovery (first step the DEV-005 money
trajectory durably diverges from baseline, if ever), and whether downstream
divergence occurs under each arm.

## 7. Outcome-pattern definitions (descriptive, no single score)

Mechanism patterns (from Estimands 2+3; C1–C4 must hold in all cases):

- **A. mechanism supported**: k ≥ 3 AND conditional contrast mean > 0 AND
  zero exposed-seed harm (contrast ≥ 0 on every exposed seed) AND zero
  guard-attributable damage anywhere (contrast min ≥ 0 across all N).
- **B. mechanism weakened**: k ≥ 3 AND (conditional contrast mean ≤ 0 OR any
  exposed-seed harm OR any guard-attributable damage).
- **C. mechanism untestable**: k ≤ 2 — too few episodes to assess consistency.
  k = 0 is reported verbatim as "mechanism not exposed in this cohort".

Overall patterns (from Estimand 1, using the frozen V1.1 §2.7 bar
descriptively — this is NOT a Qualification claim):

- **D. overall improved**: two-sided p < 0.05 with mean > 0 AND min ≥ −$800.
- **F. overall harmed**: two-sided p < 0.05 with mean < 0, OR min < −$800,
  OR forensically confirmed guard-attributable severe failure.
- **E. overall neutral**: all other Estimand 1 outcomes.

The result is reported as a pair (e.g., "A + E"). A strong mechanism with a
neutral unconditional result is a coherent, publishable outcome — not a
contradiction.

## 8. Stop rules

1. Execute exactly N=500 seeds (310000–310499), then STOP.
2. No early stopping for positive results; no early stopping for negative
   results; no peeking-driven decisions of any kind.
3. No seed replacement, no cohort resizing, no extension — including after a
   zero-trigger outcome. A follow-up requires a NEW protocol.
4. No parameter, H, H2, route, threshold, or treatment change at any point.
5. Integrity-gate failure (hash mismatch, C1–C4 violation, parity failure) →
   STOP and investigate before any interpretation.
6. No second experiment is authorized by this protocol.

## 9. Forensic plan (post-execution only)

After all 500 seeds complete, forensically trace (money-trajectory replay,
both arms + baseline, both matches): every trigger-exposed seed; every
nonzero Estimand-1 seed; every seed with DEV-005/DEV-006 divergence; every
seed with |DEV-006 − baseline| ≥ $2,000. The tracer consumes fixed seed
lists from main-run telemetry and cannot alter cohort membership. Every
exposed seed and every unusually large delta receives a full replay with
the §6 field set; unusually large is defined prospectively as |paired
delta| ≥ $2,000 or any new minimum.

## 10. Simulator and pre-execution validation

- Engine: kagsim 1.32.7. Preferred: authoritative Windows binary IF loadable
  AND passing the identical validation below; else the validated
  pure-Python port at `experiments/EXP-DEV-006_HORIZON_KILLTEST/port/kagsim_py`
  (`0.4.0.port1`), unchanged (manifest hashes in §12 task 5 of PRECHECK.md).
- Before the first experimental seed, re-run ALL of: port-manifest
  validation (4/4 files + 2/2 validators); golden traces 47,520/47,520;
  frozen DEV-005 replay 100/100 (consumed 247xxx cohort vs frozen
  RAW_RESULTS reference — no experimental seeds); decision-event parity
  400/400; one-factor DEV-006 identity probe (exit 0).
- If any check fails: STOP. Do not silently modify the port.

## 11. Governance and quarantine

- Quarantined (runner hard-abort on request): 214200–214249 (final holdout),
  50050–50099, 50000–50049, 50100–50149, 50000–50499, 245000–245049,
  246000–246049, 247000–247049, 248000–248049, plus any seed outside
  310000–310499.
- Frozen files (§identity table) are read-only; hashes re-verified at
  runner-freeze and at launch.
- No Kaggle interaction, no submission generation, no holdout access beyond
  non-consumption certification.

## 12. Claim discipline

Allowed: "the trigger occurred on k/N seeds (95% CI …)"; "among
trigger-exposed episodes the conditional paired contrast was …";
"unconditional mean … (95% CI …)"; "pattern A + E".
Forbidden: "H=500 causes +$X"; "H=500 is optimal"; any Qualification,
Top-10, or Kaggle-superiority claim; any trigger redefinition; any
single-score summary of the experiment.

## 13. Runner and execution deliverables (future work, constrained now)

The execution runner does NOT exist yet. It must be written to this
protocol's constraints (exact cohort constants; quarantine guards; 4
games/seed CRN; §6 telemetry incl. prior-active-plan derivation; C1–C4 and
purity computation; zero outcome-dependent logic) and frozen in its own
commit BEFORE the first experimental seed, with this protocol's hash
re-verified at that freeze. Execution then produces: RUNNER,
RESULTS.csv, PAIRED_DELTAS.csv, TRIGGER_EVENTS.csv, FORENSIC_TRACES.json,
STATISTICS.json, FORENSIC_AUDIT.md, FINAL report, EXECUTION_MANIFEST.json.

## 14. Protocol commitment rule

This protocol, `PROTOCOL_HASH.txt`, `SEED_SELECTION_RULE.md`,
`SEED_PROVENANCE.md`, `POWER_PLANNING.md`, and `PRECHECK.md` are committed
to Git before any runner work begins. The freeze-commit hash and timestamp
are the authorization boundary: no experimental seed may execute before it.
