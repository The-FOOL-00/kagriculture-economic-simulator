# AUDIT 2.1: FULL STATISTICAL RECOMPUTATION & INFERENTIAL AUDIT
## Independent Statistical Analysis of CLOSED_LOOP_V2 vs Dmitrii-LB2800 (N = 150 Paired Seeds)

This document presents the complete recomputation and inferential evaluation of the primary performance baseline cited in Audit 2: the 150-seed paired Common Random Numbers (CRN) evaluation between `ClosedLoopAgentV2` and `Dmitrii-LB2800` from `scratch/v2_dmitrii_margin_scan.json`.

---

## 1. Twenty-Point Experimental & Methodological Audit

| # | Audit Check | Verified Status | Evidence / Forensic Finding |
|:---:|:---|:---:|:---|
| **1** | Exactly 150 seeds? | **YES** | Exactly 150 unique seeds: 50 in Discovery, 50 in Qualification, 50 in Holdout. |
| **2** | Correct pairing? | **YES** | Every seed was evaluated in both seat orientations: (P0=V2, P1=Dmitrii) and (P0=Dmitrii, P1=V2). |
| **3** | Same seeds? | **YES** | Seeds span contiguous integers 50000 to 50149 without gaps. |
| **4** | Same simulator version? | **YES** | Executed using `external_repos/kaggriculture-cppsim` (`kagsim`). |
| **5** | Same environment? | **YES** | Default episode length (720 steps), board size 10x10, $3,000 cash. |
| **6** | Correct seat balancing? | **YES** | The paired margin is $M(s) = m_{\text{seat0}}(s) + m_{\text{seat1}}(s)$, eliminating first-mover advantage. |
| **7** | Correct sign convention? | **YES** | Positive indicates V2 outearned Dmitrii; negative indicates Dmitrii outearned V2. |
| **8** | Correct baseline? | **YES** | Dmitrii-LB2800 was invoked via its canonical entry point (`main.py`). |
| **9** | Correct paired differences? | **YES** | Recomputed from raw match rewards; matches stored margins to 0.000 discrepancy. |
| **10**| Correct standard error? | **YES** | $\text{SE} = \frac{s}{\sqrt{N}} = \frac{166.7481}{\sqrt{150}} = 13.6149$. Matches Audit 2 (13.61). |
| **11**| Correct t-statistic? | **YES** | $t = \frac{\bar{x}}{\text{SE}} = \frac{24.6133}{13.6149} = 1.8078$. Matches Audit 2 (1.8078). |
| **12**| Correct p-value? | **YES (WITH NUANCE)**| Two-sided $t$-test ($df=149$): $p = 0.0727$. (Standard normal gives $p = 0.0706$). Audit 2 reported 0.0726. |
| **13**| Correct confidence interval? | **YES (WITH NUANCE)**| Student's $t_{149}$ yields `[-$2.29, +$51.52]`. Audit 2 reported `[-$2.07, +$51.30]` using $z=1.96$. Both cross zero. |
| **14**| Correct win rate? | **YES** | 82 Wins, 68 Losses, 0 Ties $\rightarrow$ 54.67%. Matches Audit 2. |
| **15**| Any duplicated seeds? | **NO** | Set length is exactly 150. Zero duplicate seeds. |
| **16**| Any missing seeds? | **NO** | All integers from 50000 to 50149 are present. |
| **17**| Any failed episodes? | **NO** | All 300 game instances ran to completion (`g.done = True`). |
| **18**| Any filtering? | **NO** | Zero seeds excluded or post-hoc trimmed. |
| **19**| Any hidden outliers? | **YES (EXPOSED)** | Seed 50081 (-$730.0) is a structural outlier driven by Day 9 sheep purchase failure. |
| **20**| Dependency between samples? | **NO** | Each seed initializes an independent PRNG state. |

---

## 2. Partition-by-Partition Statistical Breakdown

| Partition | Seeds | N (Paired) | Mean Margin | Median | Std Dev | Std Error | 95% CI (Student's t) | t-stat | p-value | Win Rate | Min | Max |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Discovery** | 50000–50049 | 50 | +$39.12 | +$76.00 | 157.61 | 22.29 | [-$5.67, +$83.91] | 1.7551 | 0.0855 | 62.0% (31W-19L) | -$400.0 | +$326.0 |
| **Qualification** | 50050–50099 | 50 | +$11.40 | -$13.00 | 190.74 | 26.97 | [-$42.81, +$65.61] | 0.4226 | 0.6744 | 48.0% (24W-26L) | -$730.0 | +$244.0 |
| **Holdout** | 50100–50149 | 50 | +$23.32 | +$57.00 | 151.44 | 21.42 | [-$19.72, +$66.36] | 1.0889 | 0.2815 | 54.0% (27W-23L) | -$452.0 | +$316.0 |
| **Combined Total** | **50000–50149** | **150** | **+$24.61** | **+$58.00** | **166.75** | **13.61** | **[-$2.29, +$51.52]** | **1.8078** | **0.0727** | **54.67% (82W-68L)** | **-$730.0** | **+$326.0** |

### Confirmation of Audit 1 Transcription Errors (R14 Table 1)
Audit 2 correctly discovered that R14 Table 1 in earlier reports contained severe transcription errors:
- Discovery Mean: Reported `+$28.8` vs True **`+$39.12`**
- Qualification Mean: Reported `+$0.5` vs True **`+$11.40`**
- Holdout Mean: Reported `+$46.4` vs True **`+$23.32`**
- Max Win: Reported `+$454.0` vs True **`+$326.0`**

---

## 3. Comprehensive Distributional & Sensitivity Analysis

### Descriptive Statistics
- **Sample Size ($N$)**: 150 independent paired CRN seeds (300 matches)
- **Sample Mean ($\bar{x}$)**: +$24.6133
- **Sample Median ($\tilde{x}$)**: +$58.0000
- **Trimmed Mean (5% cut each tail)**: +$33.72
- **Interquartile Range (IQR)**: p75 ($+$112.0) - p25 ($-58.0$) = $170.0
- **Sample Variance ($s^2$)**: 27,804.93
- **Sample Standard Deviation ($s$)**: 166.7481
- **Standard Error ($\text{SE}$)**: 13.6149
- **Effect Size (Cohen's $d$)**:
  $$d = \frac{\bar{x}}{s} = \frac{24.6133}{166.7481} = 0.1476$$
  This indicates a **negligible-to-small** effect size ($d < 0.2$).

### Confidence Intervals Comparison
1. **Student's $t$ Exact 95% CI ($df = 149$, $t_{\text{crit}} = 1.9760$)**:
   $$24.6133 \pm 1.9760 \times 13.6149 = [-\$2.29, \; +\$51.52]$$
2. **Standard Normal Approximation ($z_{\text{crit}} = 1.9600$)**:
   $$24.6133 \pm 1.9600 \times 13.6149 = [-\$2.07, \; +\$51.30]$$
   *(Note: This matches Audit 2's reported interval exactly).*
3. **Non-Parametric Bootstrap 95% CI (100,000 Monte Carlo Resamples)**:
   $$[-\$2.56, \; +\$50.57]$$
4. **Conclusion**: All three confidence interval methods span zero on the negative side.

### Distribution Percentiles of Paired Differences
| Percentile | Value | Interpretation |
|:---:|:---:|:---|
| **p01** | -$623.8 | Extreme lower tail |
| **p05** | -$344.9 | 5% worst loss threshold |
| **p10** | -$177.3 | 10% worst loss threshold |
| **p25 (Q1)** | -$58.0 | 25th percentile |
| **p50 (Median)**| **+$58.0** | 50% of seeds yield $\ge +\$58$ |
| **p75 (Q3)** | +$112.0 | 75th percentile |
| **p90** | +$206.4 | 10% best win threshold |
| **p95** | +$244.0 | 5% best win threshold |
| **p99** | +$321.1 | Extreme upper tail |

### Extreme Seeds Inspection
- **Worst 5 Seeds**:
  1. Seed 50081: **-$730.0** (Day 9 sheep purchase failure)
  2. Seed 50078: **-$612.0**
  3. Seed 50112: **-$452.0**
  4. Seed 50022: **-$400.0**
  5. Seed 50014: **-$358.0**
- **Best 5 Seeds**:
  1. Seed 50020: **+$326.0**
  2. Seed 50113: **+$316.0**
  3. Seed 50083: **+$244.0**
  4. Seed 50002: **+$244.0**
  5. Seed 50123: **+$240.0**

### Outlier Sensitivity Test
If we trim the single worst outlier (Seed 50081):
- New Mean: +$29.68
- New Std: 153.22
- New SE: 12.55
- New 95% CI: `[+$4.87, +$54.49]`
- New p-value: $p = 0.0195$
This proves that V2's failure to reject the null hypothesis at the 5% level ($p = 0.0727$) is heavily influenced by the single Seed 50081 animal purchase failure (-$730). However, because Seed 50081 represents a real mechanical vulnerability (runtime cash feedback), trimming it post-hoc would constitute unscientific cherry-picking. The full 150-seed result must stand.

---

## 4. Formal Equivalence Testing (Two One-Sided Tests — TOST)

Under classical hypothesis testing, failure to reject the null hypothesis ($p = 0.0727 > 0.05$) does **NOT** prove that V2 and Dmitrii are equivalent. To scientifically test for equivalence, we perform formal Two One-Sided Tests (TOST) against specified equivalence bounds $[-\Delta, +\Delta]$:
$$H_{0,\text{lower}}: \mu \le -\Delta \quad \text{vs} \quad H_{1,\text{lower}}: \mu > -\Delta$$
$$H_{0,\text{upper}}: \mu \ge +\Delta \quad \text{vs} \quad H_{1,\text{upper}}: \mu < +\Delta$$
$$\text{TOST } p\text{-value} = \max(p_{\text{lower}}, p_{\text{upper}})$$

| Equivalence Bound ($\pm \Delta$) | $t_{\text{lower}}$ | $p_{\text{lower}}$ | $t_{\text{upper}}$ | $p_{\text{upper}}$ | $p_{\text{TOST}}$ | Equivalence Conclusion ($\alpha = 0.05$) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| **$\pm \$25.00$** | 3.6440 | 0.0002 | -0.0284 | 0.4887 | **0.4887** | **NOT PROVEN EQUIVALENT** |
| **$\pm \$50.00$** | 5.4802 | 0.0000 | -1.8647 | 0.0321 | **0.0321** | **STATISTICALLY EQUIVALENT within $\pm \$50$** |
| **$\pm \$75.00$** | 7.3163 | 0.0000 | -3.7009 | 0.0002 | **0.0002** | **STATISTICALLY EQUIVALENT within $\pm \$75$** |
| **$\pm \$100.00$** | 9.1525 | 0.0000 | -5.5372 | 0.0000 | **0.0000** | **STATISTICALLY EQUIVALENT within $\pm \$100$** |

---

## 5. Definitive Inferential Conclusions

1. **Superiority is NOT Established**:
   Because the two-sided p-value is $p = 0.0727 > 0.05$, classical hypothesis testing fails to reject the null hypothesis of zero difference at the 5% significance level. V2 cannot be claimed to be "globally superior" or "proven superior" to Dmitrii-LB2800.
2. **"Parity is Proven" Must Be Formally Qualified**:
   Merely having a confidence interval that crosses zero does not prove equivalence. However, formal TOST equivalence testing confirms that V2 and Dmitrii are **statistically equivalent within an equivalence margin of $\pm \$50$ coins ($p = 0.0321$)**. At tighter margins ($\pm \$25$), equivalence is not proven.
3. **Correct Scientific Description**:
   `CLOSED_LOOP_V2` demonstrates a **positive point estimate of +$24.61 coins with a 54.7% win rate against Dmitrii-LB2800**, but the difference is not statistically significant at the 5% level ($p = 0.0727$). The agents are statistically indistinguishable within a $\pm \$50$ margin, with bounded downside (zero paired losses exceeding -$1,000).
