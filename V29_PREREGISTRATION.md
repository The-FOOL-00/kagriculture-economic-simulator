# V29 — PREREGISTRATION: A7 PROTECTED-HOLDOUT PROMOTION GATE + ABSOLUTE-LEVEL DECOMPOSITION

Frozen and COMMITTED before the first holdout match. V28's result
(+$1,389.99, 78/80, OUTCOME A on virgin seeds 249530..249569) is
CONFIRMATORY evidence and a replication reference only; it confers no
promotion status and may not tune any V29 choice. This document defines
the first and only promotion-holdout test. After the first holdout
match: seeds, code, config, statistics, and thresholds frozen; this
file MUST NOT be modified after holdout results appear.

Companion specs frozen alongside (same commit, same no-edit rule):
`V29_ABSOLUTE_LEVEL_SPEC.md` (decomposition math),
`V29_COHORT_MANIFEST.json` (seeds, arms, counts),
`V29_BASELINE_FREEZE.md` (hashes), `V29_A7_FREEZE.md` (candidate).

## 1. Primary endpoint

Paired terminal-cash difference per match on Arms 1+2: `Δ = A7 − V3`
(same game, mirrored seat). N = 80 matches / 40 seeds. Terminal cash =
`env.steps[-1][seat]["reward"]` (V28 construction).

## 2. Promotion gates (copied EXACTLY from `V28_PREREGISTRATION.md` §5; no threshold eased)

Computed on all 80 Arm-1+2 matches exactly as defined; no substitution:

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

## 3. Holdout seeds

`340050..340089` (40 seeds; see `V29_COHORT_MANIFEST.json`). Remainder
`340090..340199` MUST remain untouched — no V29 process may execute,
reference-as-seed, or write output for any seed ≥ 340090 (enforced by
runner assert + `test_v29_freeze.py`). Previously consumed ranges
(§2 of the manifest) are never substituted in.

## 4. Seat / arm structure (160 matches total)

- Arm 1: A7@0 vs V3@1, 40 seeds × 1 = 40 matches.
- Arm 2: V3@0 vs A7@1, 40 seeds × 1 = 40 matches (mirror control).
- Arm 3: A7 vs A7, 40 seeds × 1 = 40 matches (ONE match per seed
  yields both seats' terminal cash `A0`, `A1`).
- Arm 4: V3 vs V3, 40 seeds × 1 = 40 matches (ONE match per seed
  yields `V0`, `V1`).
- Engine `kaggle_environments==1.32.7`, pool mode,
  `max_tasks_per_child=1` (fresh worker process per match), workers=9,
  checkpointed JSONL, same configuration fingerprint all arms.

## 5. Statistical method (primary + secondary)

- Statistical unit: the SEED (n=40) for all confirmatory inference;
  match-level (n=80) descriptives reported alongside, never
  substituted into Gate 5.
- Ties: exact-zero PRIMARY; |Δ|≤$500 sensitivity analysis.
- Seed-positive rate, seat-specific means/medians, within-seed
  seat-diff distribution, min/max, q05/q25/q75/q95: reported (V28 §4
  constructions).
- Secondary inference (non-gating): seed-level bootstrap 95% CI of
  the mean (seeded RNG 29, 10,000 resamples), Wilcoxon signed-rank p
  on the 80 Δs, 5%-trimmed mean, means excluding largest
  positive/negative match.
- Absolute-level inference: seed-paired, same t-CI construction as
  Gate 5, labeled SECONDARY (see §6).

## 6. Absolute-level decomposition (secondary question, preregistered math)

Entirely per `V29_ABSOLUTE_LEVEL_SPEC.md` (frozen here by reference):
per-seed `L_A`, `L_V`, `CREATE = L_A − L_V`, `EXTRACT = m − CREATE`
with the exact identity `m = CREATE + EXTRACT`; sub-split
`E = O_A + O_V`; seat-level `C_0`/`C_1`; farm-gap controls `G_V`/`G_A`;
pie diagnostics; per-seed `results/v29_decomposition.csv`. No equation
may be added or reinterpreted after results appear. Interpretation
follows spec §6 (rules 1–5), including the refusal to force a label
under an unclean separation.

## 7. Tail analysis (diagnostic; never replaces the primary mean)

Largest positive/negative, top-1/3/5 seed contribution shares,
trimmed mean, mean excluding largest positive, mean excluding largest
negative (brief §25 list), computed on Arms 1+2 exactly as V28 did.
Tail-dependence overlay (copied from V28 §6 OUTCOME D): if the largest
|single-seed total| exceeds 50% of |grand total|, the result is
TAIL-DEPENDENT and MUST be headlined as such; no promotion without a
second cohort even under formal gate passage.

## 8. Failure rules / decision mapping (brief §29)

- **OUTCOME A — PROMOTED** iff: all six §2 gates pass AND (a)
  isolation regression 7/7 PASS, (b) serial/pool parity 8/8 PASS (+
  subprocess parity in committed tests), (c) independent rerun 14/14
  exact (see §11), (d) every record's digests match the freeze (§10),
  (e) no unexplained execution artifact, (f) mechanism audit completes
  with 100% telemetry coverage (see §12) and `step0_rewritten` on all
  80 A7vV3 legs with 0 unexpected shapes, (g) the decomposition shows
  NO catastrophic weakness, i.e. NOT(`Cbar < 0` with the seed 95%
  t-CI fully below zero), (h) no TAIL-DEPENDENT overlay (§7).
  Promotion = research-candidate tier ONLY: no Kaggle submission, no
  V22R1 replacement, no AEC, no packaging (brief §§9/27/28).
- **OUTCOME B — HOLDOUT POSITIVE BUT DECOMPOSITION WEAK** iff: all six
  §2 gates pass (with (a)–(f) and (h) holding) BUT (`Cbar ≤ 0`, or
  `Ebar/M ≥ 50%` with `M > 0`, or the catastrophic-weakness veto (g)
  triggers): A7 is a CONFIRMED COMPETITIVE RESPONSE, not a general
  economic-dominance candidate. Never labeled universal superiority.
- **OUTCOME C — PRIMARY PASS, INTEGRITY FAILURE** iff: any of (a)–(f)
  fails while the economics pass: **V29 INVALID**. No promotion.
- **OUTCOME D — HOLDOUT FAILS** iff: any §2 gate fails: **A7 NOT
  PROMOTED**. Record exactly which gates failed. No retuning (§9).

## 9. No-retuning / holdout-sanctity rule

From the first holdout match until the final report: no change to A7,
V3, harness, config, simulator, engine, thresholds, statistics, or
seed list. No inspection of partial holdout results to adjust the
candidate; no rerunning only losing seeds; no replacing difficult
seeds; no altering thresholds; no conditioning-on-acting for any gate;
no favorable-subset selection. Crash-recovery reruns use identical
bytes only. V28 (+$1,390) and V27 (≈+$1,451) are replication
references, never tuning inputs.

## 10. Digest / freeze rule

Every V29 record carries `a7_digest`, `v3_digest`, `sim_digest`
(P3-adapter/V3-adapter/interface/utils/config bundle), `harness_digest`
(runner SHA256, recorded), `engine_version`, variant + flags. The
runner asserts all frozen digests at every process startup and refuses
mismatches. The analyzer rejects any raw file containing a
non-matching record. V22R1 (`33763a8…` / `6b879b3e…`) is re-verified
but never touched.

## 11. Qualification & verification (prespecified)

- Isolation regression (7 contexts, V28 matrix: V3-after-V3,
  A7-after-V3, V3-after-A7, A7-after-A7, fresh-subprocess A7/V3,
  reversed scheduling, reused-vs-fresh parity) on CONSUMED seeds only
  (249431, 249470 — the V28 audit seeds; never 340050+). Required PASS
  before the tournament. Any mismatch → STOP.
- Serial/pool parity: consumed subset 249436..249439 × Arms 1+2 (8
  matches) executed serial AND pool; require bit-exact (cand reward,
  base reward, action digest, money digest) 8/8. Any mismatch → STOP.
- Independent re-run AFTER the main run: preregistered subset =
  seeds 340050..340054 × Arms 1+2 (10 matches) PLUS seeds 340050..340051
  × Arms 3+4 (4 matches) = 14 instances, re-executed from fresh
  processes via independently reconstructed invocation commands, no
  result cache. Require 14/14 exact (rewards + digests). Any
  mismatch → OUTCOME C.
- Counterfactual/mechanism/tail/decomposition audits are diagnostic
  instruments on frozen records; they cannot change §§2/8 except via
  the preregistered vetoes (g) and (§7 overlay).

## 12. Mechanism replication telemetry (preregistered fields)

`scripts/v29_mechanism.py` replays ALL 80 A7vV3 holdout legs (fresh
processes, frozen bytes) and records per leg: (1) step-17 cash gap,
(2) melon-seed purchase qty gap at step 17, (3) melon plant-count gap
(A7−V3, full-game), (4) first unit-divergence step (or none), (5) first
market-divergence step (or none), (6) harvest-jump step + size (largest
single-step money-gap increase in obs[100..400], or none), (7) terminal
delta. Every leg is then classified CANONICAL_MELON / SHEEP_GATE /
OTHER_POSITIVE / TIE-INERT / FARM-ROUTE_LOSS / OTHER_NEGATIVE with its
telemetry row as evidence; per-category delta contribution is reported.
Measurability = 100% legs with complete telemetry + a published
evidence row each; no leg may be left "unmeasurable".

## 13. Freeze declaration

From the first holdout match: A7 source, V3 source, harness, config,
simulator, engine, environment, thresholds, statistics (§§2/5/6/7),
decomposition equations (§6), telemetry fields (§12), and seed list
(§3) frozen. Any rerun uses identical bytes.
