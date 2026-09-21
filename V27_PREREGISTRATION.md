# V27 — PREREGISTRATION: PROSPECTIVE GENERALIZATION TEST

Frozen BEFORE any prospective seed is touched and before ablation
results are known. Covers Stage A (discovery) and Stage B
(confirmation). Ablations (Phase 7–8) are firewalled to consumed seeds
and cannot alter this plan.

## 1. Primary comparison

`V25_P3` (frozen `candidates/v25_p3_unified.py`, `13292582…`, via
hermetic `V25P3BackboneAdapter`) vs `V3` (frozen
`submission_Vj_kc_v3.tar.gz`, `845e0d10…`, via hermetic
`V3BackboneAdapter`). No AEC, no market timing, no tuning, no
seed-specific behavior. The V25 file-loader pool pattern is BANNED
(history-dependent; ledger §1); a committed test enforces adapter
hermeticity (order-independence).

## 2. Cohorts (see V27_COHORT_MANIFEST.json)

- Stage A discovery: seeds `249490..249509` × seats {0,1} = 40 matches.
- Stage B confirmation: seeds `249510..249529` × seats {0,1} = 40 matches.
- Engine 1.32.7, MAX_WORKERS=9, checkpointed JSONL, opponent always
  frozen V3, mirrored CRN seats.

## 3. Endpoints

### Primary endpoint
Paired terminal-cash difference per match: `V25 − V3` (Objective A).

### Secondary endpoints
- Median paired delta.
- Positive-match rate (fraction Δ>0) — match-level AND seed-level
  (seed = mean of its 2 seats).
- W/L/T: exact-zero ties PRIMARY (V26 convention); |Δ|≤$500 ties as
  sensitivity (V25 convention). Zero exact ties expected (wash differs).
- Tail floor: min Δ; q10.
- Seat symmetry: within-seed seat-diff distribution; seat-effect test.
- Farm-gap spot check: V3v3 hermetic matches ONLY on seeds with
  |seat0−seat1| > $300 (targeted; same $300 rule as retrospective).
- Regime-conditional delta (EXPLORATORY, non-gating): Δ by sign and
  magnitude of the t=288 money gap (the 249463 watchlist pattern,
  n=1 provenance — corroboration only, no promotion power).

### Head-to-head (Objective B), reported separately
Win/loss counts, win rate, seed-level sign test. Never collapsed with
Objective A.

## 4. Primary generalization gates (Stage B confirmation)

ALL must hold (existing research standard, plus one seed-level gate
justified by the seat-identity finding — effective N is 20 seeds):

1. Mean paired Δ > 0 (40 matches).
2. Median paired Δ > 0.
3. Positive-match rate > 50% (≥21/40).
4. Wins > losses (exact-zero W/L/T).
5. Tail floor: min Δ > −$10,000 (2× worst history-free loss −$5,054).
6. Seed-positive rate > 50% (≥11/20 seed-means > 0). [NEW: seed-level]

Reported non-gating: seed-mean 95% cluster CI, Wilcoxon p, seed sign
p, farm-gap spot results, regime-conditional table.

## 5. Stage rules

**Stage A (discovery):** run frozen P3vsV3 on 249490..509. Allowed:
analysis, regime-watchlist observation (is a t≈288 threshold tip
observable prospectively?). NOT allowed: any code change to P3, V3,
adapters, or harness based on Stage A; any threshold/gate change;
using Stage A to select seeds, seats, or analyses for Stage B beyond
this document.

**Freeze:** after Stage A, code is frozen (hash-recorded). No changes
before/during Stage B except crash-recovery reruns (identical code).

**Stage B (confirmation):** run frozen P3vsV3 on 249510..529. No
changes after seeing Stage A. This is the robustness verdict.

## 6. Decision mapping (binds §27 states to gates)

- All 6 gates pass + no farm-artifact dominance (largest |single-seed
  contribution| < 50% of total) + watchlist corroborated or absent →
  OUTCOME A (robust) or B (conditional, only with a replicated early
  predictor — none currently exists).
- Gates pass but result dominated by 1–2 seeds, or seed CI straddles
  zero with |mean| < $500 → OUTCOME E (unresolved / small vs variance).
- 1+ gates fail with negative mean and seed CI excluding large
  positive values → OUTCOME D (failed to generalize; V3 remains).
- Mixed signs with no early predictor and wide CIs → OUTCOME C
  (seed-noise-dominated; reopen backbone research, no AEC).
- Forcing a binary winner when CIs straddle zero is PROHIBITED (E, not
  A/D, is the honest state).

## 7. Counterfactual diagnostics (exploratory, non-gating)

Using validated V26 backbone-aware continuation, exact active-backbone
state, no mechanisms:
- CF-1: on 249463, V3-continuation with cash injected to P3's t≈280
  level → does the t=289 sheep branch fire? Report predicted vs
  realized effect + reconstruction fidelity (never equated).
- CF-2 (if CF-1 fires): same injection −$1 (below threshold) as a
  falsification control.
- Report: V27_COUNTERFACTUAL_ANALYSIS.md with predicted/realized/
  fidelity triples. These diagnose the threshold story; they cannot
  promote P3.

## 8. Ablation firewall

Ablations (V27_ABLATION_PLAN.md) run ONLY on consumed seeds
(249430..249489 trajectories/matches). They may not use, peek at, or
select from 249490+. Ablation outcomes may not change §§1–7. Any
research variant is labeled `V27-ABL-*`, never "V25 P3".

## 9. Test requirements for the prospective runner

Deterministic replay (same seed twice → same digest), parallel/serial
parity, adapter hermeticity (history-independence), checkpoint resume,
frozen-hash assertions (P3/V3/engine). Committed before Stage A runs.
