# V28 — PREREGISTRATION: A7 vs V3 VIRGIN CONFIRMATION

Frozen BEFORE the first confirmation match. V27's A7 result (+$1,451,
119/120, consumed seeds) is EXPLORATORY and post-hoc selected; this
document defines the first and only confirmatory test. No V28 outcome
may retroactively promote V27 to confirmatory status.

## 1. Primary comparison

`A7` = `V27AblationAdapter("V27-ABL-A7")`, file SHA256
`18d2c8ea…` (see `V28_A7_FREEZE.md`), flags
(call_v3_at_step0=True, open_units=30, dispatch=False,
rewrite_step0_wash=True)
vs `V3` = `V3BackboneAdapter` over `submission_Vj_kc_v3.tar.gz`
(`845e0d10…`). No AEC, no market timing, no tuning, no seed-specific
behavior, no V25 code in either arm (A7 inherits only the hermetic V3
loader; P3 behavior flags are all off).

Engine `kaggle_environments==1.32.7`, pool mode,
`max_tasks_per_child=1` (fresh worker process per match), workers=9,
checkpointed JSONL, mirrored seats.

## 2. Cohort (see `V28_COHORT_MANIFEST.json`)

Seeds `249530..249569` × seats {0,1} = 80 matches, pending a clean
registry scan (no reference to any seed ≥ 249530 anywhere; holdouts
`214200..214249`, `340050..340199` untouched; retired `340300..340349`
excluded). If the scan finds contamination, the manifest resolves the
next legal block and this document is amended BEFORE any match runs
(with the reason recorded). After the first match: seeds frozen.

## 3. Primary endpoint

Paired terminal-cash difference per match: `Δ = A7 − V3` (same game,
mirrored seat). N=80 matches / 40 seeds.

## 4. Secondary endpoints (non-gating unless stated)

- Median paired Δ.
- Positive-match rate (Δ>0): match-level AND seed-level (seed = mean
  of its 2 seats).
- W/L/T: exact-zero ties PRIMARY; |Δ|≤$500 as sensitivity.
- Tail: min Δ, q05/q95, max Δ.
- Seat symmetry: seat-0 vs seat-1 means, within-seed seat-diff
  distribution.
- Tie/inert decomposition: exact ties, action-identical matches,
  conditional effect when A7 acts (SECONDARY; never replaces gate 4).
- Tail concentration: top-1/2/3 seed contribution share; means
  excluding largest positive / largest negative match (diagnostic).
- Rewrite integrity: `step0_rewritten` must be True on 80/80;
  `step0_unexpected_shape` must be False on 80/80 (else the A7
  treatment did not deploy as specified — integrity failure, §E).

## 5. The six preregistered gates (ALL must hold)

Computed on all 80 matches exactly as defined; no substitution:

1. **Mean**: arithmetic mean of the 80 paired Δs > 0.
2. **Median**: median of the 80 paired Δs > 0.
3. **Positive-match rate**: fraction of 80 matches with Δ > 0 exceeds
   0.50 (≥ 41/80).
4. **Wins > losses**: exact-zero W/L/T, wins > losses.
5. **Seed-clustered 95% CI fully positive**: let m_s = mean of the 2
   seat Δs for seed s (n=40). CI = mean(m) ± t(0.975, df=39) ·
   SD(m)/√40. PASS iff the lower bound > 0. (Method frozen here; no
   post-hoc switch to match-level, bootstrap, or Wilcoxon for the
   gate. Bootstrap CI and Wilcoxon p reported as secondary.)
6. **Tail floor**: min Δ over 80 matches > −$10,000 (2× the worst
   history-free V27 loss, −$5,054).

## 6. Decision mapping

- All 6 gates pass → **OUTCOME A: A7 CONFIRMED** (standalone
  mechanism; enters a LATER promotion/holdout cycle — no auto-submit).
- Mean > 0 but ≥1 gate fails → **OUTCOME B: A7 NOT CONFIRMED**.
- Mean < 0 → **OUTCOME C: A7 FAILED TO GENERALIZE** (mean == 0
  exactly → B, gates 1–4 fail by construction).
- **OUTCOME D disclosure** (overlays A/B, never overrides the gates):
  if the largest |single-seed total| exceeds 50% of |grand total|,
  the result is TAIL-DEPENDENT and must be headlined as such; do not
  promote even under formal gate passage without a second cohort.
- Execution contamination detected at any point → **OUTCOME E: V28
  INVALID**; stop, fix, restart only with this preregistration
  unchanged.

## 7. Anti-p-hacking rules

No favorable-subset selection, no seat subsetting, no outlier removal
from the primary result, no CI-method change, no seed-block
replacement after results, no reruns-until-green, no
conditioning-on-acting for any gate. Every non-§5 statistic is labeled
exploratory/secondary.

## 8. Qualification & verification (prespecified, non-gating)

- Execution-order + serial/parallel parity matrices run on CONSUMED
  seeds only (never 249530+); required PASS before the tournament.
- Independent verification: the first 5 cohort seeds × 2 seats
  (10 matches) are re-run post-tournament in fully fresh subprocess
  interpreters; require exact reward+digest equality with tournament
  records.
- Counterfactual/mechanism/tail audits are diagnostic instruments on
  frozen records; they cannot change §§5–6.

## 9. Freeze

From the first confirmation match: A7 source, V3 source, harness,
config, simulator, engine, environment, thresholds, statistics, and
seed list frozen. Any crash-recovery rerun uses identical bytes.
