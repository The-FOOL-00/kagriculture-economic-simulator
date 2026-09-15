# AUDIT 2.2: INDEPENDENT STATISTICAL REVIEW & TOST AUDIT
## Full Mathematical Recomputation, Inferential Evaluation, and Equivalence Verification

**Audit Exercise**: Independent Forensic Audit 2.2 of Audit 2.1 Statistical Suite  
**Primary Dataset**: `scratch/v2_dmitrii_margin_scan.json` (150 paired Common Random Number seeds, 300 total matches)  
**Standard**: Stop Rule #4 (Raw-Data Verification) & Classical / TOST Inferential Statistics  
**Date**: 2026-09-11  

---

## 1. Raw Observation Integrity & Experimental Hygiene

Before recomputing summary statistics, the raw data structure of `scratch/v2_dmitrii_margin_scan.json` was audited from scratch:
1. **Total Matches**: Exactly 300 completed match records.
2. **Total Paired Seeds**: Exactly 150 unique, contiguous integer seeds spanning `50000` to `50149` without gaps or duplicates.
3. **Seat Balancing**: Each seed was evaluated in both mirror orientations:
   - Seat 0: (P0 = `ClosedLoopAgentV2`, P1 = `Dmitrii-LB2800`)
   - Seat 1: (P0 = `Dmitrii-LB2800`, P1 = `ClosedLoopAgentV2`)
4. **Paired Margin Identity**: For every seed $s$, the paired difference is:
   $$M(s) = m_{\text{seat0}}(s) + m_{\text{seat1}}(s) = (\text{cash}_{\text{v2, s0}} - \text{cash}_{\text{dmi, s1}}) + (\text{cash}_{\text{v2, s1}} - \text{cash}_{\text{dmi, s0}})$$
   This cancels first-player positional advantages. Recomputation from raw match cash values matched the stored margin vectors (`disc_margins`, `qual_margins`, `hold_margins`) with **0.000 discrepancy**.
5. **Sign Convention**: Positive margin indicates `ClosedLoopAgentV2` outearned `Dmitrii-LB2800`; negative margin indicates `Dmitrii-LB2800` outearned V2.
6. **Failed or Incomplete Matches**: Zero (`g.done == True` across all 300 runs).
7. **Post-Hoc Filtering**: Zero excluded or trimmed seeds in the primary 150-seed set.

---

## 2. Partition-by-Partition Recomputation

All metrics were computed with double-precision floating point arithmetic:

| Partition | Seeds Range | N | Sample Mean ($\bar{x}$) | Sample Median ($\tilde{x}$) | Sample Std ($s$) | Std Error ($\text{SE}$) | Student's t 95% CI | t-stat ($t$) | p-value ($p_t$) | Win Rate (Paired) | Min Margin | Max Margin |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Discovery** | 50000–50049 | 50 | +$39.1200 | +$76.0000 | 157.6082 | 22.2892 | [-$5.6718, +$83.9118] | 1.7551 | 0.0855 | 62.0% (31W-19L) | -$400.0 | +$326.0 |
| **Qualification** | 50050–50099 | 50 | +$11.4000 | -$13.0000 | 190.7404 | 26.9748 | [-$42.8078, +$65.6078] | 0.4226 | 0.6744 | 48.0% (24W-26L) | -$730.0 | +$244.0 |
| **Holdout** | 50100–50149 | 50 | +$23.3200 | +$57.0000 | 151.4359 | 21.4163 | [-$19.7176, +$66.3576] | 1.0889 | 0.2815 | 54.0% (27W-23L) | -$452.0 | +$316.0 |
| **Combined Total** | **50000–50149** | **150** | **+$24.6133** | **+$58.0000** | **166.7481** | **13.6149** | **[-$2.2899, +$51.5166]** | **1.8078** | **0.0727** | **54.67% (82W-68L)** | **-$730.0** | **+$326.0** |

---

## 3. Deep Reconciliation of Confidence Intervals and P-Values

### A. Confidence Interval Formula Comparison
Audit 2 originally reported the 95% CI as `[-$2.07, +$51.30]`. Audit 2.1 corrected this to `[-$2.29, +$51.52]`.

1. **Student's $t$ Distribution ($df = 149$, $t_{\text{crit}} = 1.976013$)**:
   $$\text{CI}_{95\%} = \bar{x} \pm t_{0.975, 149} \times \text{SE} = 24.613333 \pm 1.976013 \times 13.614925$$
   $$\text{CI}_{95\%} = [24.6133 - 26.9033, \; 24.6133 + 26.9033] = [-\$2.2899, \; +\$51.5166]$$
   Rounded to cents: **`[-$2.29, +$51.52]`**.
2. **Standard Normal Approximation ($z_{\text{crit}} = 1.959964 \approx 1.9600$)**:
   $$\text{CI}_{95\%} = 24.613333 \pm 1.959964 \times 13.614925 = [-\$2.0719, \; +\$51.2986]$$
   Rounded to cents: **`[-$2.07, +$51.30]`**.
3. **Non-Parametric Bootstrap ($100,000$ Monte Carlo Resamples)**:
   $$\text{CI}_{95\%} = [-\$2.5600, \; +\$50.5737]$$
4. **Epistemic Conclusion**:
   Audit 2 used the standard normal approximation $z=1.96$ without labeling the approximation. Because $n=150$ is finite, Student's $t$ with $df=149$ is mathematically required. The numerical difference is tiny ($\pm \$0.22$ coins), and **all three methods cross zero on the negative side**.

### B. The P-Value Discrepancy Reconciliation
Audit 2 cited $p = 0.070$ in `AUDIT2_SOURCE_MAP.md:25` and $p = 0.0726$ in `AUDIT2_REPRODUCTIONS.md:21`. Audit 2.1 cited $p = 0.0727$.

1. **Student's $t$ exact p-value ($df = 149$, $t = 1.807820$)**:
   $$p = 2 \times (1 - F_t(1.807820, 149)) = 0.07265166...$$
   Rounding $0.07265166$ to 4 decimal places yields **$p = 0.0727$** (since the fifth digit is 5 followed by 1).
   Truncating or rounding down to 4 decimal places yields **$p = 0.0726$**.
2. **Standard Normal approximation p-value ($z = 1.807820$)**:
   $$p = 2 \times (1 - \Phi(1.807820)) = 0.070635...$$
   Rounding to two significant digits yields **$p = 0.071$** (or $0.070$ if unrounded from $0.0706$).
3. **Epistemic Conclusion**:
   The divergence between $0.070$, $0.0726$, and $0.0727$ is entirely explained by:
   - Normal approximation ($p = 0.0706$) vs Student's $t$ ($p = 0.072652$).
   - Standard rounding ($0.0727$) vs truncation ($0.0726$).
   No deeper data corruption or seed manipulation exists. All values exceed $\alpha = 0.05$.

---

## 4. Audit 2.1 Secondary Calculation Errors Exposed & Corrected

While Audit 2.1's primary statistics (Mean, Std, SE, t-stat, p-value, CI, Win Rate) were 100% verified, our adversarial pass uncovered three secondary calculation errors in `AUDIT2_1_STATISTICAL_AUDIT.md`:

### A. Distributional Percentiles Discrepancy
In `AUDIT2_1_STATISTICAL_AUDIT.md:81-89`, a table of percentiles was presented. Here is the side-by-side comparison against direct recomputation from the raw 150 paired differences:

| Percentile | Reported in Audit 2.1 | True Recomputed Value | Discrepancy | Nature of Discrepancy |
|:---:|:---:|:---:|:---:|:---|
| **p01** | -$623.8 | **-$533.6** | +$90.2 | Overstated lower tail |
| **p05** | -$344.9 | **-$198.5** | +$146.4 | Overstated 5% risk |
| **p10** | -$177.3 | **-$126.2** | +$51.1 | Overstated 10% risk |
| **p25 (Q1)** | -$58.0 | **-$84.0** | -$26.0 | True Q1 is lower |
| **p50 (Median)**| **+$58.0** | **+$58.0** | **$0.0** | **EXACT MATCH** |
| **p75 (Q3)** | +$112.0 | **+$156.0** | +$44.0 | True Q3 is higher |
| **p90** | +$206.4 | **+$204.0** | -$2.4 | Minor discrepancy |
| **p95** | +$244.0 | **+$224.4** | -$19.6 | Minor discrepancy |
| **p99** | +$321.1 | **+$280.7** | -$40.4 | Overstated upper tail |
| **IQR** | $170.0 | **$240.0** | **+$70.0** | **Interquartile range is $240, not $170** |

### B. Trimmed Mean Discrepancy
- Audit 2.1 Line 59 reported: `Trimmed Mean (5% cut each tail): +$33.72`.
- True Recomputed 5% Trimmed Mean (cutting 7 lowest and 7 highest seeds from 150):
  $$\bar{x}_{5\%\text{ trimmed}} = \mathbf{+\$36.53}$$
- Discrepancy: Audit 2.1 underestimated the 5% trimmed mean by $2.81 coins.

### C. Outlier Sensitivity Trimming Discrepancy
In Audit 2.1 lines 107–111, the report claimed that trimming the single worst outlier (Seed 50081, -$730.0) produced:
`New Mean: +$29.68, New Std: 153.22, New SE: 12.55, New 95% CI: [+$4.87, +$54.49], New p-value: 0.0195`.

Recomputing across the exact 149 remaining observations:
- **New Mean**: **+$29.68** (Matches Audit 2.1)
- **New Std ($ddof=1$)**: **155.30** (Reported: 153.22 — Mismatch of 2.08)
- **New SE**: **12.72** (Reported: 12.55 — Mismatch of 0.17)
- **New 95% CI (Student's t, df=148)**: **`[+$4.54, +$54.82]`** (Reported: `[+$4.87, +$54.49]`)
- **New t-stat**: **2.3333**
- **New p-value**: **$p = 0.0210$** (Reported: $p = 0.0195$ — Mismatch of 0.0015)

*Forensic Conclusion on Errors*: Audit 2.1's author apparently computed these secondary exploratory metrics from an uncommitted scratch script or used approximate formulas. While the qualitative takeaways survive (the distribution has positive median and trimming Seed 50081 yields $p < 0.05$), the exact published numbers were inaccurate. Audit 2.2 replaces them with raw-data mathematical ground truth.

---

## 5. Comprehensive TOST (Two One-Sided Tests) Equivalence Audit

Audit 2.1 claimed:
> “TOST demonstrates equivalence within $\pm \$50.00$ coins ($p = 0.0321$), but not within $\pm \$25.00$ ($p = 0.4887$).”

### A. Mathematical Procedure & Formal Verification
To test equivalence within bounds $[-\Delta, +\Delta]$:
1. Lower bound hypothesis:
   $$H_{0,\text{lower}}: \mu \le -\Delta \quad \text{vs} \quad H_{1,\text{lower}}: \mu > -\Delta$$
   $$t_{\text{lower}} = \frac{\bar{x} - (-\Delta)}{\text{SE}} = \frac{24.613333 + \Delta}{13.614925}$$
   $$p_{\text{lower}} = 1 - F_t(t_{\text{lower}}, 149)$$
2. Upper bound hypothesis:
   $$H_{0,\text{upper}}: \mu \ge +\Delta \quad \text{vs} \quad H_{1,\text{upper}}: \mu < +\Delta$$
   $$t_{\text{upper}} = \frac{\bar{x} - \Delta}{\text{SE}} = \frac{24.613333 - \Delta}{13.614925}$$
   $$p_{\text{upper}} = F_t(t_{\text{upper}}, 149)$$
3. Overall decision rule:
   $$p_{\text{TOST}} = \max(p_{\text{lower}}, p_{\text{upper}})$$
   Reject $H_0$ (declare statistical equivalence) at significance level $\alpha = 0.05$ if and only if $p_{\text{TOST}} < 0.05$.

### Full Grid Evaluation Results:
| Equivalence Margin ($\pm \Delta$) | $t_{\text{lower}}$ | $p_{\text{lower}}$ | $t_{\text{upper}}$ | $p_{\text{upper}}$ | $p_{\text{TOST}}$ | Equivalence at $\alpha = 0.05$? |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **$\pm \$25.00$** | 3.6440 | 0.000185 | -0.0284 | 0.488690 | **0.4887** | **REJECTED (NOT EQUIVALENT)** |
| **$\pm \$40.00$** | 4.7458 | 0.000003 | -1.1301 | 0.130105 | **0.1301** | **REJECTED (NOT EQUIVALENT)** |
| **$\pm \$47.15$** | 5.2709 | 0.000000 | -1.6551 | 0.050000 | **0.0500** | **EXACT CRITICAL THRESHOLD** |
| **$\pm \$50.00$** | 5.4803 | 0.000000 | -1.8646 | 0.032101 | **0.0321** | **CONFIRMED EQUIVALENT** |
| **$\pm \$75.00$** | 7.3165 | 0.000000 | -3.7008 | 0.000151 | **0.0002** | **CONFIRMED EQUIVALENT** |
| **$\pm \$100.00$** | 9.1527 | 0.000000 | -5.5371 | 0.000000 | **0.0000** | **CONFIRMED EQUIVALENT** |

**Mathematical Verdict**: The calculation of TOST in Audit 2.1 is **100% MATHEMATICALLY EXACT**.

---

### B. Scientific Validity & Methodological Critique of TOST

A statistical test may be mathematically correct while suffering from severe methodological limitations. Audit 2.2 explicitly answers the critical questions posed in Topic 7:

#### 1. Was the margin of $\pm \$50$ specified BEFORE inspecting the data?
**NO.** In the inherited research and in Audit 2, no formal equivalence test was planned or pre-registered. Audit 2 simply observed $p > 0.05$ and erroneously claimed that "parity is established" (affirming the null). Audit 2.1 recognized this fallacy and introduced TOST post-hoc to determine what margin would be required to prove equivalence.

#### 2. Why did $\pm \$50$ pass while $\pm \$25$ failed?
Under statistical equivalence theory, TOST at level $\alpha = 0.05$ is mathematically equivalent to checking whether the $(1 - 2\alpha) = 90\%$ two-sided confidence interval lies entirely within $[-\Delta, +\Delta]$.
For our 150 paired seeds:
$$t_{0.95, 149} = 1.655145$$
$$\text{CI}_{90\%} = 24.6133 \pm 1.655145 \times 13.614925 = [+\$2.0805, \; +\$47.1462]$$
Because the upper bound of the 90% CI is $+47.15$, **any margin $\Delta \ge 47.15$ will automatically pass, and any margin $\Delta < 47.15$ will automatically fail.**
Choosing $\Delta = \$50$ was simply selecting the nearest round number immediately above the empirical 90% confidence limit!

#### 3. Is $\pm \$50$ an economically meaningful equivalence bound?
Let us examine the economic scale of the Kaggriculture game:
- **Total Episode Cash**: Average final cash across seeds is $\$90,000$ to $\$115,000$.
- **Relative Proximity**: A margin of $\$50$ represents **0.05% of total score**.
- **Microeconomic Scale**: In-game transactions dwarf $\$50$:
  - 1 sheep costs $\$500.00$.
  - 1 cow costs $\$1,200.00$.
  - 10 strawberries sold to town generate $\$140.00$.
  - 1 single day's hiring costs at 9 hands is $\$88.00$.
- **Downside Risk & Variance**: The sample standard deviation is $\$166.75$, and the worst single-seed paired loss was $-\$730.00$.

#### 4. The Distinction Between Mean, Behavioral, and Strategic Equivalence:
- **Mean-Score Proximity (Verified)**: V2 and Dmitrii achieve average rewards within $\$50$ of each other across the 150-seed cohort.
- **Behavioral Equivalence (Refuted)**: The agents are NOT behaviorally equivalent. On Seed 50081, V2 diverged physically for 460 turns due to a sheep purchase shortfall. At steps 712–718, Dmitrii executes a 64-simulation Monte Carlo planner while V2 executes PASS.
- **Strategic Equivalence (Refuted)**: Demonstrating mean equivalence within $\pm \$50$ does not mean the agents are interchangeable in a competitive tournament. V2 possesses different tail risks and different sensitivity to runtime cash perturbations.

**Scientific Verdict on TOST**:
TOST proves **mean-score proximity within a post-hoc margin of $\pm \$50$**, but does **NOT** prove universal parity, behavioral equivalence, or strategic interchangeability.

---

## 6. Definitive Synthesis of Statistical Findings

```
========================================================================================
                        SUMMARY OF 150-SEED PARED BASELINE
========================================================================================
Sample Size (N)            : 150 paired seeds (300 matches, 50k–50149)
Sample Mean Margin         : +$24.61 coins
Sample Median Margin       : +$58.00 coins
Sample Std Deviation       : 166.75 coins
Standard Error             : 13.61 coins
Two-Sided Paired t-test    : t = 1.8078, df = 149, p = 0.0727
Student's t 95% CI         : [-$2.29, +$51.52] (Spans zero)
Standard Normal 95% CI     : [-$2.07, +$51.30] (Spans zero)
Bootstrap 95% CI (100k)    : [-$2.56, +$50.57] (Spans zero)
Paired Win Rate            : 54.67% (82 Wins, 68 Losses, 0 Ties)
Worst Paired Loss          : -$730.0 coins (Seed 50081)
Best Paired Win            : +$326.0 coins (Seed 50020)
Losses > $1,000            : 0 / 150 (0.0%)
Cohen's d                  : 0.1476 (Negligible effect size)
----------------------------------------------------------------------------------------
TOST Equivalence (±$25)    : p = 0.4887 -> NOT PROVEN EQUIVALENT
TOST Equivalence (±$50)    : p = 0.0321 -> EQUIVALENT IN MEAN (Post-hoc bound)
========================================================================================
```

### Inferential Rules for Development:
1. **Never claim V2 is superior**: $p = 0.0727 > 0.05$. The point estimate is positive, but statistically inconclusive.
2. **Never claim V2 and Dmitrii are identical**: Their mean payoffs are close (within $\pm \$50$), but their runtime behaviors and tail distributions differ.
3. **V2 is a robust parity baseline**: With zero losses $> \$1,000$, a 54.7% win rate, and mean score proximity, V2 serves as a dependable benchmark anchor.
