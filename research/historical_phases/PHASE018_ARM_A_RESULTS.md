# PHASE018 — ARM A RESULTS (Funnel Reservation, isolated)

**Status**: COMPLETE
**Date**: 2026-09-19
**Design**: preregistered in `PHASE018_FUNNEL_RESERVATION_SPEC.md`
**Cohort**: fresh seeds `249296..249305` (10 seeds × 2 CRN mirror seats × 2 comparisons = 40 matches)

---

## 0. Reproducibility gate (passed before treatment claims)

`results/PHASE018_BASELINE_REPRO_*`: exact re-execution of the Phase017 protocol —
6508/2082/736/54, O1–O4 410/394/124/400, precision 98.10%, all 10 paired seed
margins identical. Baseline reproducible; Repair A code present but default-off
during repro (legacy behavior unperturbed at full-match fidelity).

## 1. Arms

- **A0** — foundation control (`build_robust_qualified_config()`), common control.
- **A1** — Phase015 treatment, reservation OFF (`build_phase015_treatment_config()`).
- **A2** — A1 + `enable_funnel_reservation=True` ONLY (unit-verified single-field
  diff). No quantity, trigger, representation, or evaluator change.

## 2. Headline economics (paired terminal margin vs A0)

| Arm | Mean | Std | 95% CI | W/L/T | Min | Max |
|---|---|---|---|---|---|---|
| A1vA0 | -$1,360.2 | 1214.1 | [-$2,112.7, -$607.7] | 1/9/0 | -$3,480 | +$107 |
| A2vA0 | -$1,310.9 | 1195.7 | [-$2,052.0, -$569.8] | 1/9/0 | -$3,480 | +$80 |
| **Effect A2−A1** | **+$49.3** | 81.0 | [-$0.9, +$99.5] | 4/2/4 | -$27 | +$208 |

Per-seed effect: 249296 +116, 249297 −26, 249298 +129, 249299 0, 249300 0,
249301 0, 249302 +93, 249303 −27, 249304 0, 249305 +208.

Note: the fresh-cohort A1 baseline (−$1,360) is harsher than Phase017 (−$884) —
cohort variance, which is why the within-phase common-control A1 leg (same seeds)
is the only valid comparator. No seed got meaningfully worse (worst −$27, parity
band); four seeds tied exactly (no crowding pressure on those trajectories).

## 3. Mechanism effect (candidate funnel, treatment ledger)

| Metric | A1 (off) | A2 (on) |
|---|---|---|
| Candidates / simulated / escalated / committed | 6651 / 2093 / 608 / 36 | 6509 / 2069 / 602 / 50 |
| Foundation candidates → simulated → **committed** | 56 → 56 → **0** | 102 → 102 → **14** |
| Tranche commits | 36 | 36 (unchanged) |
| Reservation saves (within-turn, all sites) | 0 | 7,670 across 20/20 matches |
| Experimental sim cost of reservation | — | −24 sims (−1.1%), 0 commits lost |

Reservation **nearly doubled foundation candidates** reaching the patch stage
(56 → 102) and restored **14 foundation commits** (all
`DEPENDENCY_AWARE_MARKET_TIMING`) while leaving experimental search intact
(identical 36 tranche commits). A1 committed ZERO foundation candidates across
the entire fresh cohort — systematic crowding-out reproduced on untouched seeds.

All 14 restored commits land on steps **433** (6×72+1) and **649** (9×72+1): the
post-block-boundary windows where V3 emits reorderable multi-order queues (same
structural window as the 249288 step-649 failure). Simulated values +$1..+$129 —
treatment's own-farm value, correctly small (see §6).

Escalation regimes A1→A2: CASH 116→110, BUDGET 116→116, QUEUE 174→174, FEED
202→202 — evaluator behavior preserved.

## 4. Foundation preservation vs control

| Seed | A0 commits (×2 seats) | A1 foundation commits | A2 foundation commits |
|---|---|---|---|
| 249296 | 2 | 0 | 2 |
| 249297 | 2 | 0 | 2 |
| 249298 | 2 | 0 | 2 |
| 249299 | 0 | 0 | 0 |
| 249300 | 0 | 0 | 0 |
| 249301 | 0 | 0 | 0 |
| 249302 | 4 | 0 | 4 |
| 249303 | 2 | 0 | 2 |
| 249304 | 0 | 0 | 0 |
| 249305 | 2 | 0 | 2 |

A2's foundation-commit pattern mirrors A0's opportunity structure seed-for-seed.
Opportunity cost of reserved slots: nil (experimental commits/sims unchanged).

## 5. Safety, evaluator, runtime

- Unsafe commits: **0** in A1, **0** in A2 (all 86 commits passed safety).
- Safety-rejection counts (correct rejections): 1,218 (A1) vs 1,160 (A2).
- Macro evaluator: untouched code; regime mix stable (§3); escalation rate
  29.0% → 29.1%.
- Runtime: mean match elapsed 210 s (A1) vs 211 s (A2) — no explosion.
  Limitation: this harness persisted only per-match elapsed, not per-turn
  latency percentiles; Arm B/C harnesses persist full per-turn latency.

## 6. Seed-249288 diagnostic (consumed seed, mechanistic — not evidence)

`scripts/diagnose_phase018_seed249288.py`: A1 reproduces the Phase017 failure
(step 649: 16 opps, 0 sims, BACKBONE/NO_FEASIBLE_CANDIDATE_PATCHES, paired
−$1,561). A2: opportunity reservation saves `MARKET_TIMING_STEP_649` (from 40
raw opps), foundation simulates AND commits at step 649 both seats — **selection
repaired**. Terminal paired −$1,578 (Δ −$17, parity band): treatment's own-farm
commit value differs from control's +$1,485 (different farm/state), so restoring
selection is necessary but not sufficient for large terminal gains on this seed.
Verdict: **mechanism ✓, terminal ≈ neutral** — consistent with the cohort's small
positive mean.

## 7. Success-criteria verdict (§33)

| Criterion | Result |
|---|---|
| A. Mechanism-level causal effect | **PASS** — within-turn saves + 0→14 commits, tranche intact |
| B. Funnel integrity | **PASS** — foundation no longer systematically crowded out |
| C. No safety regression | **PASS** — zero violations both arms |
| D. No macro-evaluator regression | **PASS** — code untouched, regimes stable |
| E. No runtime explosion | **PASS** — elapsed identical |
| F. Economic improvement | **WEAK PASS** — +$49.3, CI [−$0.9, +$99.5]; positive but small |

## 8. Decision

**Outcome A (partial repair, infrastructure adoption).** Funnel reservation is
adopted as **gated architectural infrastructure**: enabled in mixed
foundation+experimental research arms, default-off (provable no-op) in the frozen
live foundation. It is NOT a Phase015 qualification event: A2 remains −$1,310.9
(1W/9L), and Phase015 mechanisms stay quarantined. The dominant residual loss is
tranche-candidate quality itself → proceed to isolated Repair B.
