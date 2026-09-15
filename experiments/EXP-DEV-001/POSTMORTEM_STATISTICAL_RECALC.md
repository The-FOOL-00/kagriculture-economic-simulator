# EXP-DEV-001 POSTMORTEM STATISTICAL RECALCULATION & DISTRIBUTION AUDIT

**Experiment Identifier**: `EXP-DEV-001`  
**Raw Source Files**:
- [`experiments/EXP-DEV-001/EXP-DEV-001_RAW_RESULTS.json`](file:///c:/Users/Sundareswaran/Kagriculture/experiments/EXP-DEV-001/EXP-DEV-001_RAW_RESULTS.json)
- [`experiments/EXP-DEV-001/EXP-DEV-001_PAIRED_DELTAS.csv`](file:///c:/Users/Sundareswaran/Kagriculture/experiments/EXP-DEV-001/EXP-DEV-001_PAIRED_DELTAS.csv)  
**Recomputation Script**: [`scratch/detailed_stats.py`](file:///c:/Users/Sundareswaran/Kagriculture/scratch/detailed_stats.py)  
**Auditor**: Antigravity Autonomous Pair Programmer  
**Date**: 2026-09-11  

---

## 1. Data Integrity and Sample Verification

The raw experimental outputs were parsed and independently verified:
- **Seed Count**: Exactly 50 seeds (`50000` to `50049`).
- **Completeness**: 0 missing seeds, 0 duplicates, 0 truncated or malformed episodes.
- **Match Count**: 100 paired matches vs `ClosedLoopAgentV2`, 100 paired matches vs `Dmitrii-LB2800` (total 200 matches).
- **Discrepancies vs Runner Output**: **0 (Zero)** numerical discrepancies across all metrics.

---

## 2. Independent Statistical Recalculation: Primary Comparison (vs. `ClosedLoopAgentV2`)

$$\text{Margin}(s) = (\text{Cand}_0 - \text{V2}_1) + (\text{Cand}_1 - \text{V2}_0)$$

| Metric | Runner Reported | Independent Recalculation | Discrepancy | Standard Error / Notes |
| :--- | :---: | :---: | :---: | :--- |
| **Sample Size ($N$)** | 50 | 50 | None | Discovery seeds 50000–50049 |
| **Mean Paired Margin ($\Delta \mu$)** | **+$265.18** | **+$265.18** | None | Arithmetic mean |
| **Median Paired Margin** | **+$0.00** | **+$0.00** | None | Exactly 42/50 seeds tied |
| **10% Trimmed Mean** | — | **+$0.40** | — | Trims top/bottom 5 seeds |
| **Sample Standard Deviation ($s$)** | 2,191.06 | 2,191.06 | None | $s = \sqrt{\frac{1}{N-1} \sum (x_i - \bar{x})^2}$ |
| **Standard Error ($SE$)** | 309.86 | 309.86 | None | $SE = s / \sqrt{N}$ |
| **Student's $t$-statistic ($df=49$)** | 0.8558 | 0.8558 | None | $t = \bar{x} / SE$ |
| **Two-Sided $p$-value** | 0.3963 | 0.396274 | None | $p > 0.05$ ($H_0$ NOT rejected) |
| **95% Student-$t$ Confidence Interval** | `[-$357.51, +$887.87]` | `[-$357.51, +$887.87]` | None | Spans zero |
| **95% Bootstrap Confidence Interval** | — | `[-$132.36, +$926.86]` | — | 10,000 resamples (spans zero) |
| **Wins** | 6 | 6 | None | 12.0% win rate |
| **Losses** | 2 | 2 | None | 4.0% loss rate |
| **Ties** | 42 | 42 | None | 84.0% tie rate |
| **Worst Single-Seed Loss** | **-$2,388.00** | **-$2,388.00** | None | Seed 50018 ($< -\$800.00$ stop) |
| **Best Single-Seed Win** | **+$15,264.00** | **+$15,264.00** | None | Seed 50004 |

---

## 3. Independent Statistical Recalculation: Reference Comparison (vs. `Dmitrii-LB2800`)

| Metric | Runner Reported | Independent Recalculation | Discrepancy |
| :--- | :---: | :---: | :---: |
| **Sample Size ($N$)** | 50 | 50 | None |
| **Mean Paired Margin** | **+$291.10** | **+$291.10** | None |
| **Median Paired Margin** | **+$121.00** | **+$121.00** | None |
| **10% Trimmed Mean** | — | **+$75.67** | — |
| **Standard Deviation ($s$)** | 2,201.71 | 2,201.71 | None |
| **Standard Error ($SE$)** | 311.37 | 311.37 | None |
| **Student's $t$-statistic ($df=49$)** | 0.9349 | 0.9349 | None |
| **Two-Sided $p$-value** | 0.3544 | 0.354423 | None |
| **95% Student-$t$ Confidence Interval** | `[-$334.62, +$916.82]` | `[-$334.62, +$916.82]` | None |
| **95% Bootstrap Confidence Interval** | — | `[-$136.26, +$978.22]` | — |
| **Wins / Losses / Ties** | 33W - 17L - 0T | 33W - 17L - 0T | None |
| **Win Rate vs Dmitrii** | 66.0% | 66.0% | None |
| **Worst Single-Seed Loss** | -$3,424.00 | -$3,424.00 | None |
| **Best Single-Seed Win** | +$15,120.00 | +$15,120.00 | None |

> **Critical Note on Separation of Baselines**: The comparison against `Dmitrii-LB2800` must not be conflated with the comparison against `ClosedLoopAgentV2`. Because the treatment tied V2 on 42 of 50 seeds, the treatment's performance vs Dmitrii on those 42 seeds is **strictly identical to V2's performance vs Dmitrii**.

---

## 4. Complete Empirical Quantile Spectrum

| Quantile | Treatment vs V2 ($) | Treatment vs Dmitrii ($) |
| :---: | :---: | :---: |
| **$p_{01}$** | -$1,223.27 | -$1,935.38 |
| **$p_{05}$** | $0.00 | -$341.70 |
| **$p_{10}$** | $0.00 | -$124.20 |
| **$p_{25}$** | $0.00 | -$42.00 |
| **$p_{50}$ (Median)** | $0.00 | +$121.00 |
| **$p_{75}$** | $0.00 | +$170.00 |
| **$p_{90}$** | +$16.20 | +$230.00 |
| **$p_{95}$** | +$90.20 | +$267.20 |
| **$p_{99}$** | +$7,878.72 | +$7,875.84 |

---

## 5. Outlier Sensitivity and Distributional Fragility Analysis

The distribution of paired deltas vs `ClosedLoopAgentV2` is severely bimodal and skewed by two extreme seeds: Seed 50004 (+$15,264.00) and Seed 50018 (-$2,388.00). Diagnostic sensitivity analyses demonstrate the extreme fragility of the reported mean:

| Sample Partition | $N$ | Mean Paired Margin ($\Delta \mu$) | Median | SD ($s$) | $t$-statistic | $p$-value | 95% Student-$t$ CI |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Full Ensemble** | 50 | **+$265.18** | $0.00 | 2,191.06 | 0.8558 | 0.3963 | `[-$357.51, +$887.87]` |
| **Excluding Seed 50004 (+15k outlier)** | 49 | **-$40.92** | $0.00 | 343.99 | -0.8327 | 0.4092 | `[-$139.72, +$57.89]` |
| **Excluding Seed 50018 (-2.3k outlier)** | 49 | **+$319.33** | $0.00 | 2,179.70 | 1.0255 | 0.3103 | `[-$306.76, +$945.41]` |
| **Excluding BOTH Outliers (50004 & 50018)** | 48 | **+$7.98** | $0.00 | 34.61 | 1.5971 | 0.1169 | `[-$2.07, +$18.03]` |

### Analytical Conclusions from Sensitivity Audit:
1. **The positive mean (+$265.18) is entirely artificial**: It is 100% dependent on a single positive outlier (Seed 50004). Removing Seed 50004 turns the strategy net negative (-$40.92).
2. **The 10% Trimmed Mean is +$0.40**: In the central 80% of the distribution, the strategy offers virtually zero economic advantage over V2.
3. **Inert Mass**: 42 out of 50 seeds produced a delta of exactly **$0.00**. The treatment was completely inert across 84% of evaluated world states.
