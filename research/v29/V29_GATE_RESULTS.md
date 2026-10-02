# V29 — SIX-GATE RESULTS (preregistered math, frozen d818fb1)

Data: `results/v29_raw_results.jsonl` (160/160; Arms 1+2 = 80)
SHA256 `565f11989e7ad630559ac4fab4195fda4269b5d50f48e9bdbc6996d3bfaa23bc`.
Paired: `results/v29_paired_results.csv`
(`7a7d758165a018e8c94ba5d409c0505acbdeb4c450fe6ef4f6aff4143a21b47c`).
Stats: `results/v29_gate_stats.json` (emitted by `scripts/v29_analyze.py`).

Historical replication references (NOT tuning inputs): V28 +$1,389.99,
V27 ≈ +$1,451.

## 1. Primary summary (Arms 1+2, A7−V3)

| Metric | Value |
| :--- | ---: |
| Mean paired Δ | **+1,289.18** |
| Median | +1,286.0 |
| SD (match) / SE (match) | 156.2 / 17.5 |
| Seed-mean / seed SD (n=40) | +1,289.18 / 15.0 |
| W/L/T (exact-zero, primary) | **80 / 0 / 0** |
| W/L/T (|Δ|≤$500, sensitivity) | 80 / 0 / 0 |
| Positive-match rate | 1.000 (80/80) |
| Seed-positive rate | 1.000 (40/40) |
| Min / max | +583 / +1,989 |
| q05 / q25 / q75 / q95 | +1,165.5 / +1,286 / +1,286 / +1,406.5 |
| Trimmed mean (5%) | +1,289.53 |
| Bootstrap 95% CI (secondary) | [+1,286.0, +1,294.5] |
| Wilcoxon p (secondary) | 7.6e−17 |

## 2. Gate verdicts

| Gate | Required | Measured | Verdict |
| :--- | :--- | ---: | :--- |
| 1. Mean > 0 | > 0 | +1,289.18 | **PASS** |
| 2. Median > 0 | > 0 | +1,286.0 | **PASS** |
| 3. Positive rate > 50% | ≥ 41/80 | 80/80 (1.000) | **PASS** |
| 4. Wins > losses | W > L | 80W / 0L / 0T | **PASS** |
| 5. Seed 95% CI fully > 0 | lower > 0 | [+1,284.38, +1,293.97] | **PASS** |
| 6. Tail floor > −$10k | min > −10,000 | +583 | **PASS** |

Gate-5 method (frozen in prereg): seed means (n=40),
mean ± t(0.975, df=39)·SD/√40, tcrit = 2.0227. No substitution made.

## 3. Seat and seed analysis

- Seat-0 (Arm 1) mean +1,250.9, seat-1 (Arm 2) mean +1,327.45;
  medians +1,286 both seats.
- Seat-identical seeds: 33/40. The 7 exceptions are diagnosed in the
  mechanism audit: 6 carry tiny farm gaps (|G| ≤ $219, vs V28's
  −$6k/−$11k) and all 7 show late reactive-market micro-divergence;
  340060 is asymmetric with ZERO farm gap (pure wobble, cf. V28's
  249533). Seed means remain +$1,286 ± $15 on all 40.
- Zero / tie / inert: exact ties 0/80; action-identical matches 0/80
  (the step-0 wash differs by construction in every match). No
  conditioning-on-acting performed.

## 4. Replication comparison

| Campaign | Cohort | Mean | Median | W/L/T |
| :--- | :--- | ---: | ---: | :--- |
| V27 exploratory | consumed | ≈ +$1,451 | +$1,286 | 119/120 |
| V28 confirmation | 249530..249569 | +$1,389.99 | +$1,286 | 78/2/0 |
| **V29 holdout** | **340050..340089** | **+$1,289.18** | **+$1,286** | **80/0/0** |

The median is +$1,286 in all three campaigns; the V29 mean sits $101
below V28's (no +$12k tip on this slice) with 10× tighter seed-SD
($15 vs $631). The effect replicated quantitatively for the third time.

## 5. Decision

**6/6 gates PASS.** Tail-concentration disclosure: top-1 seed share
2.7% (< 50%), top-3 7.7%, top-5 12.7%; mean excluding the largest match
+$1,280.3 — no tail-dependence overlay. The primary result is not
tail-dependent. Promotion mapping continues in
`V29_CREATE_EXTRACT_DECOMPOSITION.md` (OUTCOME A vs B turns on the
decomposition, per preregistration §8).
