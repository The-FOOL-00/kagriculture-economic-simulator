# PHASE022 STATISTICAL RECALCULATION (Independent Adversarial Audit)

**Date**: 2026-09-20
**Auditor method**: recomputed from `results/phase022_consolidation.json` match rows (N=40) with
independent code (`scipy`), cross-checked against the markdown ledger in
`PHASE022_FRESH_VALIDATION.md`. No experiments were run; no holdouts touched.

## 1. Row-level verification

- Stored match rows: 40 (seats 0/1 x seeds 249376..249395, contiguous, no gaps).
- Markdown ledger rows parsed: 40. **Ledger-vs-JSON mismatches: 0.**
- Seat balance: 20 seat-0 + 20 seat-1. CRN mirror structure confirmed by design
  (head-to-head treatment-vs-control within one game per seat; see
  `scripts/run_phase022_consolidation.py:101-162`).
- Treatment/control mapping: `trt_reward` = reward of the seat the AEC agent
  occupied; `paired_delta = trt - ctrl` within the same game. Verified in code.

## 2. Number-by-number recalculation (match level, N=40)

| Metric | Reported | Recalculated | Match? |
| --- | --- | --- | --- |
| N (matches / nonzero) | 40 / 28 | 40 / 28 | YES |
| Mean paired delta | +$33.35 | +$33.3500 | YES (exact) |
| Median paired delta | +$22.00 | +$22.00 | YES (exact) |
| Std (ddof=1) | $1152.01 | $1152.0082 | YES |
| SE | $182.15 | $182.1485 | YES |
| 95% CI (t) | [-$335.08, +$401.78] | [-$335.08, +$401.78] | YES |
| t-test p (two-sided) | 0.855674 | 0.855674 | YES (exact) |
| Wilcoxon p (two-sided) | 0.034086 | 0.034086 | YES (exact) |
| Win / Loss / Tie | 21 / 7 / 12 | 21 / 7 / 12 | YES |
| Cohen's d | 0.0289 | 0.028949 | YES |
| Mean treatment reward | $94,346.40 | $94,346.40 | YES |
| Mean control reward | $94,313.05 | $94,313.05 | YES |

Additional auditor computations (same data):

- Wilcoxon exact-method p = 0.0337 (normal approximation 0.0341 is fine).
- Wilcoxon one-sided (greater) p = 0.0170.
- Wilcoxon statistic W = 110 of total rank sum 406 (positive ranks dominate
  296:110). The +/-$4,887 mirror pair occupies the top two ranks and contributes
  net +1 rank point: the test is nearly blind to the seat-noise scale, but also
  nearly blind to economic magnitude.
- One-sided t-test p ~= 0.43 (fails; see section 5).

**Arithmetic verdict: every reported number is correct. No fabrication, no
rounding fraud, no ledger mismatch.**

## 3. Variance structure: 98.6% of the sum-of-squares is seat artifact

Six match rows have nonzero deltas with ZERO AEC commits (pure V3-vs-V3 seat
asymmetry under head-to-head mirroring):

| Seed | Seat | Delta | Commits |
| --- | --- | --- | --- |
| 249382 | 0 / 1 | +$19 / -$19 | none |
| 249390 | 0 / 1 | +$4,887 / -$4,887 | none |
| 249393 | 0 / 1 | -$1,323 / +$1,234 | none |

These 6 rows contribute 98.6% of the total sum-of-squares. The treatment signal
lives in the remaining 1.4%. Consequences:

1. The match-level t-test and t-CI are dominated by seat noise, not by
   treatment heterogeneity. The CI spanning zero is the honest reflection of
   this design, not a coding error.
2. The Wilcoxon test sidesteps the scale problem by rank transformation, which
   is exactly why the two tests disagree (p = 0.034 vs p = 0.856).
3. Any mean-based economic claim (+$33.35) inherits the seat-noise variance and
   cannot be separated from zero at the match level.

## 4. Seed-level aggregation: the significance flips

Aggregating each mirror pair to one seed mean (N=20, the dependence-robust unit;
mirror pairs are negatively correlated by construction):

- Seed means: 8 positive / 4 negative / 8 zero. Median = **$0.00**.
- Mean = +$33.35 (unchanged), CI = **[+$4.81, +$61.89]** (excludes zero).
- Seed-level t-test p = **0.0244** (significant).
- Seed-level Wilcoxon p = **0.0508** (NOT significant at 0.05).

So each level of analysis has one passing and one failing test, in opposite
directions:

| Level | t-test | Wilcoxon |
| --- | --- | --- |
| Match (N=40) | FAIL (0.856) | PASS (0.034) |
| Seed (N=20) | PASS (0.024) | FAIL (0.051) |

**The "statistically significant" conclusion is not robust to the choice of
test or unit of analysis.** Neither "significant" nor "not significant" can be
asserted insensitive to specification. The only robust descriptive facts are:
more wins than losses (21 vs 7), positive sample mean (+$33.35), negligible
standardized effect (d = 0.03).

## 5. Preregistration and test-convention failure (material)

- No Phase 022 preregistration document exists anywhere in the repository
  (repo-wide search for Phase 022 prereg/protocol: zero hits; the string
  "preregister" appears in zero Phase 022 files).
- The program's documented convention (`EXP-AEC-002/003/004` execution
  manifests, `primary_test` field) is **`one_sided_paired_t_test`**, with the
  two-sided Wilcoxon as the *secondary* robustness test.
- Under that convention the Phase 022 primary test FAILS (one-sided t p ~= 0.43).
- The report headlines the historically-secondary Wilcoxon (p = 0.034) without
  disclosing the convention switch.
- Test multiplicity is unadjusted: t + Wilcoxon were both computed and the
  smaller reported. Under Bonferroni with K=2 (per
  `DEVELOPMENT_EXPERIMENT_PROTOCOL_V1.md` section on multiple-testing control),
  the threshold would be 0.025 and p=0.034 would fail. The t-test result was at
  least disclosed, so this is a caveat, not concealment.

## 6. Effect-size interpretation failure

Cohen's d = 0.029 is described as "Stable positive shift". By any conventional
scale (negligible < 0.2), d = 0.03 is a negligible standardized effect. The
phrase is spin and must be removed. The mean gain is 0.035% of mean game
reward ($33.35 / $94,313).

## 7. Answers to the mandated caveat questions

1. Is "statistically significant" defensible under the reported preregistered
   test? **NO as phrased.** There is no Phase 022 preregistration in the
   artifacts; under the program's documented primary (one-sided t), the result
   is non-significant. The defensible phrasing is: "nominal two-sided Wilcoxon
   p = 0.034 on match-level deltas (N=40); the t-test and all preregistration-
   convention readings are non-significant."
2. Does the confidence interval materially limit the economic claim? **YES.**
   [-$335, +$402] admits a true mean loss of hundreds of dollars. The +$33.35
   figure is a sample mean, not a bounded population effect.
3. Is "+$33.35 advantage" sample mean or stable population effect? It is
   reported with a CI, but headline wording ("delivers robust positive alpha",
   "decisively confirms") presents it as an established effect. Must be
   reworded to sample-mean language.
4. Is "FOUNDATION QUALIFIED" protocol decision or universal superiority? It is
   used as both. It is defensible ONLY as "passed the author's stated
   Wilcoxon gate" with all four test outcomes disclosed alongside.

## 8. Classification

**Statistical validity: REQUIRES CORRECTION.** The computations are honest and
exact; the inferential framing (significance, robustness, preregistration,
effect size) overstates what the numbers support.
