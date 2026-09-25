# V28 — SIX-GATE RESULTS (preregistered math, frozen 91073c8)

Data: `results/v28_raw_results.jsonl` (80/80)
SHA256 `2efb4446f35da094a1fb9b3c9f65024bcedd60f648b4d5a4a799180165f21082`.
Paired: `results/v28_paired_results.csv`
(`a0600fc86f0156a896b9ca6d3309491f8b5accd3dedd7784b7c54af5aecc1555`).
Stats: `results/v28_gate_stats.json` (emitted by `scripts/v28_analyze.py`).

## 1. Primary summary

| Metric | Value |
| :--- | ---: |
| Mean paired Δ (A7−V3) | **+1,389.99** |
| Median | +1,286.0 |
| SD (match) / SE (match) | 1,443.4 / 161.4 |
| Seed-mean / seed SD (n=40) | +1,389.99 / 631.0 |
| W/L/T (exact-zero, primary) | **78 / 2 / 0** |
| W/L/T (\|Δ\|≤$500, sensitivity) | 77 / 2 / 1 |
| Positive-match rate | 0.975 (78/80) |
| Seed-positive rate | 1.000 (40/40) |
| Min / max | −3,154 / +12,087 |
| q05 / q95 | +1,286 / +1,369 |
| Trimmed mean (5%) | +1,289.5 |
| Bootstrap 95% CI (secondary) | [+1,286.0, +1,593.8] |
| Wilcoxon p (secondary) | 1.4e−14 |

## 2. Gate verdicts

| Gate | Required | Measured | Verdict |
| :--- | :--- | ---: | :--- |
| 1. Mean > 0 | > 0 | +1,389.99 | **PASS** |
| 2. Median > 0 | > 0 | +1,286.0 | **PASS** |
| 3. Positive rate > 50% | ≥ 41/80 | 78/80 (0.975) | **PASS** |
| 4. Wins > losses | W > L | 78W / 2L / 0T | **PASS** |
| 5. Seed 95% CI fully > 0 | lower > 0 | [+1,188.2, +1,591.8] | **PASS** |
| 6. Tail floor > −$10k | min > −10,000 | −3,154 | **PASS** |

Gate-5 method (frozen in prereg): seed means (n=40),
mean ± t(0.975, df=39)·SD/√40. No substitution was made.

## 3. Seat and seed analysis (§21)

- Seat-0 mean +1,087.7, seat-1 mean +1,692.3; medians +1,286 both.
- Seat-identical seeds: 37/40. The 3 exceptions are fully diagnosed
  (see mechanism/tail audits): 249534 and 249544 carry program-
  independent farm gaps (−6,267 / −10,965 in V3vV3); 249533 is a
  farm-symmetric late-market wobble (G=0, structures identical).
- Seed-mean distribution: 37 seeds at exactly +1,286, 2 at +1,369,
  1 at +5,279.5 (249534). Effect is symmetric in the precise sense:
  every seed-mean is positive and 39/40 equal the mechanical +1,286
  up to reactive noise. The seat-mean gap (+604) is driven entirely
  by the two farm-gap seeds, not by a seat-favoring mechanism.

## 4. Zero / tie / inert analysis (§22)

- Exact ties: 0/80. Action-identical matches: 0/80 (the step-0 wash
  differs by construction in every match).
- No conditioning-on-acting is needed or performed: the primary
  result stands on all 80 matches.

## 5. Decision

**6/6 gates PASS → OUTCOME A (pending §§31–32 verification steps,
all recorded in `V28_CONFIRMATION_REPORT.md`).**
Tail-concentration disclosure: top-1 seed share 9.5% (< 50%),
top-3 14.4%; mean excluding the largest match +1,254.6 — no
OUTCOME-D overlay. The result is not tail-dependent.
