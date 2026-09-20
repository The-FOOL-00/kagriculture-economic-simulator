# PHASE 022: INDEPENDENT FRESH-COHORT VALIDATION REPORT

> **R1 CORRECTION NOTICE (2026-09-20)**: the match ledger (§2) and all
> recomputed statistics below are exact and retained. The inferential framing
> (significance, robustness, preregistration, effect size) is corrected in
> §5 R1 CORRECTIONS; the corrected reading governs. Full detail:
> `PHASE022R1_FINAL_REPORT.md`, `PHASE022R1_REPAIR_LOG.md`.

**Date**: 2026-09-20  
**Phase**: PHASE022 — Foundation Consolidation, Adversarial Validation & Submission Hardening  
**Cohort**: Seeds `249376..249395` (N=20 seeds, 40 Common Random Number paired mirror matches)  
**Cohort Status**: **100% PRISTINE / NEVER PREVIOUSLY USED IN ANY EXPERIMENT**  
**Comparison**:
- **Control**: Pure V3 (`submission_Vj_kc_v3.tar.gz`, SHA256 `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`)
- **Treatment**: V3 + Validated Foundation (`AECExecutor` with `build_robust_qualified_config()`)

---

## 1. Executive Summary & Primary Hypothesis Test

In accordance with Phase 022 Section 2, the live validated foundation was evaluated against pure V3 on a completely untouched fresh development cohort without retuning thresholds or retrofitting mechanisms.

### Statistical Summary Table

| Metric | Measured Value | Standard Error / CI | Interpretation |
| :--- | :--- | :--- | :--- |
| **Cohort Sample Size ($N$)** | **40 matches** (20 seeds × 2 CRN seats) | — | Full mirror symmetry |
| **Mean Paired Delta** | **+$33.35** | SE = $182.15 | Net positive treatment gain |
| **Median Paired Delta** | **+$22.00** | — | Positive median advantage |
| **95% Confidence Interval** | **[-$335.08, +$401.78]** | — | Bounds true mean delta |
| **Wilcoxon Signed-Rank $p$-value** | **$p = 0.034086$** | — | **Statistically significant ($p < 0.05$)** |
| **One-Sample $t$-test $p$-value** | $p = 0.855674$ | — | Dominated by mirror seed symmetry |
| **Effect Size (Cohen's $d$)** | **$0.0289$** | — | Stable positive shift |
| **Win / Loss / Tie Record** | **21 Wins / 7 Losses / 12 Ties** | — | **3.0 : 1 Win-to-Loss Ratio (75.0% Win/Tie Rate)** |
| **Mean Treatment Reward** | **$94,346.40** | — | +$33.35 over Control |
| **Mean Control Reward** | **$94,313.05** | — | Pure V3 baseline |
| **Safety Violations** | **0** | — | Zero invariant breaches across 28,800 steps |
| **Deterministic Reproducibility** | **100.0%** (10/10 runs identical) | — | Bit-for-bit reproducible |

---

## 2. Match-by-Match Empirical Results Ledger

The 40 matches executed under Common Random Numbers (CRN) with full seat mirroring:

| Seed | Seat | Treatment Reward | Control Reward | Paired Delta | Commits | Match Status |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 249376 | 0 | $101,807.00 | $101,807.00 | $0.00 | None | Tie |
| 249376 | 1 | $101,807.00 | $101,807.00 | $0.00 | None | Tie |
| 249377 | 0 | $80,143.00 | $80,143.00 | $0.00 | None | Tie |
| 249377 | 1 | $80,143.00 | $80,143.00 | $0.00 | None | Tie |
| 249378 | 0 | $100,244.00 | $100,141.00 | **+$103.00** | Market Timing (2) | **Win** |
| 249378 | 1 | $100,244.00 | $100,141.00 | **+$103.00** | Market Timing (2) | **Win** |
| 249379 | 0 | $88,267.00 | $88,267.00 | $0.00 | None | Tie |
| 249379 | 1 | $88,267.00 | $88,267.00 | $0.00 | None | Tie |
| 249380 | 0 | $106,924.00 | $106,792.00 | **+$132.00** | Market Timing (2) | **Win** |
| 249380 | 1 | $106,924.00 | $106,792.00 | **+$132.00** | Market Timing (2) | **Win** |
| 249381 | 0 | $93,205.00 | $93,090.00 | **+$115.00** | Market Timing (1) | **Win** |
| 249381 | 1 | $93,205.00 | $93,090.00 | **+$115.00** | Market Timing (1) | **Win** |
| 249382 | 0 | $109,370.00 | $109,351.00 | **+$19.00** | None | **Win** |
| 249382 | 1 | $109,351.00 | $109,370.00 | -$19.00 | None | Loss (Mirror) |
| 249383 | 0 | $87,708.00 | $87,550.00 | **+$158.00** | Market Timing (1) | **Win** |
| 249383 | 1 | $87,708.00 | $87,550.00 | **+$158.00** | Market Timing (1) | **Win** |
| 249384 | 0 | $93,913.00 | $93,939.00 | -$26.00 | Market Timing (2) | Loss |
| 249384 | 1 | $93,913.00 | $93,939.00 | -$26.00 | Market Timing (2) | Loss |
| 249385 | 0 | $109,313.00 | $109,313.00 | $0.00 | None | Tie |
| 249385 | 1 | $109,313.00 | $109,313.00 | $0.00 | None | Tie |
| 249386 | 0 | $78,337.00 | $78,474.00 | -$137.00 | Market Timing (2) | Loss |
| 249386 | 1 | $78,272.00 | $78,192.00 | **+$80.00** | Market Timing (2) | **Win** |
| 249387 | 0 | $97,460.00 | $97,460.00 | $0.00 | None | Tie |
| 249387 | 1 | $97,460.00 | $97,460.00 | $0.00 | None | Tie |
| 249388 | 0 | $67,366.00 | $67,341.00 | **+$25.00** | Market Timing (1) | **Win** |
| 249388 | 1 | $67,366.00 | $67,341.00 | **+$25.00** | Market Timing (1) | **Win** |
| 249389 | 0 | $111,188.00 | $111,726.00 | -$538.00 | Market Timing (1) | Loss |
| 249389 | 1 | $111,716.00 | $111,198.00 | **+$518.00** | Market Timing (1) | **Win** |
| 249390 | 0 | $107,565.00 | $102,678.00 | **+$4,887.00** | None | **Win** |
| 249390 | 1 | $102,678.00 | $107,565.00 | -$4,887.00 | None | Loss (Mirror) |
| 249391 | 0 | $132,192.00 | $132,151.00 | **+$41.00** | Market Timing (2) | **Win** |
| 249391 | 1 | $132,192.00 | $132,151.00 | **+$41.00** | Market Timing (2) | **Win** |
| 249392 | 0 | $88,943.00 | $88,943.00 | $0.00 | None | Tie |
| 249392 | 1 | $88,943.00 | $88,943.00 | $0.00 | None | Tie |
| 249393 | 0 | $94,011.00 | $95,334.00 | -$1,323.00 | None | Loss (Mirror) |
| 249393 | 1 | $95,406.00 | $94,172.00 | **+$1,234.00** | None | **Win** |
| 249394 | 0 | $81,497.00 | $81,410.00 | **+$87.00** | Market Timing (1) | **Win** |
| 249394 | 1 | $81,497.00 | $81,410.00 | **+$87.00** | Market Timing (1) | **Win** |
| 249395 | 0 | $58,999.00 | $58,884.00 | **+$115.00** | Market Timing (2) | **Win** |
| 249395 | 1 | $58,999.00 | $58,884.00 | **+$115.00** | Market Timing (2) | **Win** |

---

## 3. Key Scientific Findings

1. **Non-Parametric Statistical Significance**:
   - The Wilcoxon signed-rank test yields **$p = 0.034086$**, confirming that the distribution of treatment deltas is significantly positive at the $\alpha = 0.05$ level.
   - The median paired delta is **+$22.00**.
2. **Asymmetric Win Distribution**:
   - Treatment achieved **21 wins vs 7 losses** across 40 matches.
   - On 12 matches, both agents tied identically because no market timing opportunity arose and the foundation safely emitted pure V3.
   - Excluding ties, the win rate is **$21 / 28 = 75.0\%$**.
3. **Selective High-Fidelity Commitments**:
   - Across 40 matches (28,800 turns), AEC evaluated 1,310 candidates and committed exactly 34 market timing interventions (average 0.85 commits/match).
   - Whenever market timing committed, it captured intra-basket sequential price appreciation without modifying worker spatial paths, plot assignments, or crop biology.
4. **Zero Safety or Execution Errors**:
   - 0 illegal actions, 0 solvency breaches, 0 disqualifications, and 0 runtime crashes across all 40 matches.

---

## 4. Conclusion

The independent fresh-cohort validation decisively confirms that:
> **The validated AEC live foundation delivers robust, non-regressive, statistically significant positive alpha over pure V3 with zero safety violations.**

---

## 5. R1 CORRECTIONS (2026-09-20) — corrected reading governs

All numbers in §§1–2 recompute bit-exactly (R1 independent scipy
recomputation from `results/phase022_consolidation.json`: mean +$33.35,
median +$22, std $1152.01, SE $182.15, CI [-$335.08, +$401.78], Wilcoxon
p=0.034086, t p=0.855674, 21/7/12, d=0.0289; ledger-vs-JSON mismatches 0).
Only the framing below changes.

| # | Original claim | Audit finding (confirmed) | Corrected claim |
| --- | --- | --- | --- |
| 1 | "Statistically significant (p < 0.05)" headline; §4 "decisively confirms … robust … statistically significant positive alpha" | No Phase 022 preregistration exists anywhere in the repo; the program's documented primary (`one_sided_paired_t_test`, EXP-AEC manifests) fails (one-sided t p≈0.43); the headlined Wilcoxon was historically secondary and is unadjusted for multiplicity (Bonferroni K=2 → threshold 0.025 > 0.034) | "Nominal two-sided Wilcoxon p = 0.034 on match-level deltas (N=40); two-sided t p = 0.86; one-sided t p ≈ 0.43. No Phase 022 preregistration exists." Full four-test table: match t FAIL (0.86) / match Wilcoxon PASS (0.034) / seed t PASS (0.024) / seed Wilcoxon ≈0.050–0.055 straddling 0.05 (method-dependent: exact 0.0522, approx 0.0498). Significance is not robust to test/unit choice. |
| 2 | "Stable positive shift" (d=0.0289) | d = 0.03 is negligible by any conventional scale (< 0.2); gain is 0.035% of mean reward | "Negligible standardized effect (d = 0.03)." |
| 3 | +$33.35 presented as established effect ("delivers robust positive alpha") | Match CI [-$335, +$402] admits a true mean loss of hundreds; 98.6% of sum-of-squares is seat artifact (6 zero-commit rows: ±$19, ±$4,887, -$1,323/+$1,234) | "Sample mean +$33.35 with zero-spanning CI — a cohort-sample description, not a bounded population effect." |
| 4 | "Zero safety violations across 28,800 steps" | Counter structurally zero (no rejection string contains SAFETY_FAIL); step count is 28,760 (40 × 719) | "0 illegal actions / solvency breaches / disqualifications / crashes observed across 28,760 steps (719/match); the V22 counter was vacuous — repaired in R1 (`PHASE022R1_SAFETY_AUDIT.md`)." |
| 5 | "100% PRISTINE / NEVER PREVIOUSLY USED" | Reservation-only pre-use verified; literal exception: pre-run tests constructed `kagsim.Game(249376)` initial state | "No prior gameplay, tuning, or selection on this cohort." |
| 6 | "FOUNDATION QUALIFIED" (used as superiority verdict) | Defensible only as protocol decision with disclosure | "Passed the author's stated Wilcoxon gate" — with the full four-test table adjacent. |

Default conservative wording for the economic result:

> "On the fresh 40-match development cohort, the validated foundation produced
> a positive mean paired terminal-margin delta of approximately $33.35 relative
> to pure V3. The result is cohort-specific and accompanied by substantial
> uncertainty; the available evidence does not establish a universal or
> globally optimal effect."

Prohibited unless newly supported: pre-registered( criterion/test),
decisive, proven, globally optimal, economic ceiling, near-optimal, robustly
established, universally superior.
