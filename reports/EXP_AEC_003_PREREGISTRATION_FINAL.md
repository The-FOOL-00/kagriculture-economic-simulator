# EXP-AEC-003 Final Preregistration Protocol: Causal Dependency-Aware Market Timing

**Protocol Identifier:** `PREREG-EXP-AEC-003-20260917-FINAL`  
**Date Established:** 2026-09-17  
**Governance Standard:** Absolute Scientific Governance, Prospective Double-Blind Mirror CRN Protocol  
**Execution Status:** **FROZEN PROTOCOL — EXECUTION STRICTLY HALTED**  
**Authoritative Directive:** **DO NOT EXECUTE.** This protocol is frozen for peer/system review. No prospective seed may be executed, simulated, or scouted without explicit formal user authorization.

---

## 1. Executive Summary & Experimental Context

This prospective evaluation directly succeeds the falsification of **EXP-AEC-002** (where unconditional `FRONTLOAD_ORDERS` yielded $-\$0.92$ paired margin, $-\$2.07$ lower bound, $-4.00\text{ pp}$ win-rate delta due to intra-basket sequential price impact blindness).

Following that empirical result, the AEC architecture was overhauled:
1. `FRONTLOAD_ORDERS` was permanently retired and classified as `FALSIFIED`.
2. `ActionBasketDependencyGraph` (`aec/ir/dependency_graph.py`) was introduced to explicitly model `SAME_ASSET_MARKET_COUPLING`, `CASH_COUPLING`, and `CAPACITY_COUPLING`.
3. `transform_dependency_aware_market_timing` was implemented to preserve same-asset order queues, strictly refusing to invert `BUY` $\to$ `SELL` sequences on the same commodity.
4. The counterfactual forward simulator was synchronized to exact engine lockstep sequential pricing, validated by a 15-case parity suite against ground-truth `kagsim` achieving 100% numeric equality.
5. The safety certificate strictly rejects candidates when `counterfactual_fidelity` is `FAILED` or `UNKNOWN`.

**EXP-AEC-003** tests whether this causal, dependency-aware compiler pass restores statistical non-inferiority or superiority against the Frozen V3 Control across a fresh prospective 50-seed cohort.

---

## 2. Experimental Hypotheses

### 2.1 Null Hypothesis ($H_0$)
$$H_0: \mu_\Delta < \$0.00$$

### 2.2 Alternative / Primary Hypothesis ($H_1$)
$$H_1: \mu_\Delta \ge \$0.00$$

where $\mu_\Delta$ is the population mean paired terminal-margin delta between the Treatment agent (`DEPENDENCY_AWARE_MARKET_TIMING` on Frozen V3) and the Control agent (Frozen V3).

### 2.3 Primary Statistical Test
- **Test:** One-sided paired $t$-test on seed-paired terminal-margin deltas $\Delta_s$.
- **Significance Level ($\alpha$):** $0.05$
- **Degrees of Freedom ($df$):** $N - 1 = 49$ ($N = 50$ paired seeds)

---

## 3. Seed Partition Architecture & Governance Covenant

```
[340000 ----------- 340049] [340050 ----------- 340199] [340200 ----------- 340249] [340250 ----------- 340299]
    EXP-AEC-001 (HISTORICAL)      AEC LOCKED HOLDOUT (150)     EXP-AEC-002 (HISTORICAL)     EXP-AEC-003 (PROSPECTIVE)
      PERMANENTLY CONSUMED           STRICTLY TOUCHLESS          PERMANENTLY CONSUMED         PROPOSED VIRGIN COHORT
```

| Partition | Seed Range | Size ($N$) | Lifecycle Status | Governance Covenant |
|---|---|---|---|---|
| `HISTORICAL-AEC-001` | `340000–340049` | 50 seeds | **CONSUMED** | Historical baseline archive. Never rerun. |
| `LOCKED-HOLDOUT-AEC` | `340050–340199` | 150 seeds | **LOCKED HOLDOUT** | **Touchless.** Strictly quarantined. Zero simulation, zero inspection, zero tuning. |
| `HISTORICAL-AEC-002` | `340200–340249` | 50 seeds | **CONSUMED** | Historical archive. Results frozen as scientific evidence. |
| **`PROSPECTIVE-AEC-003`** | `340250–340299` | 50 seeds | **PROPOSED PROSPECTIVE** | Pre-registered contiguous cohort. Virgin, unexecuted, and uninspected. |

---

## 4. Treatment and Control Specifications

### 4.1 Control Agent
- **Backbone:** Exact frozen V3 submission (`submission_Vj_kc_v3.tar.gz`).
- **Archive SHA-256:** `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`.
- **AEC Layer:** Disabled (pure backbone baseline).

### 4.2 Treatment Agent
- **Backbone:** Identical frozen V3 submission (`submission_Vj_kc_v3.tar.gz`).
- **Active Foundation Mechanisms:**
  - `DEPENDENCY_AWARE_MARKET_TIMING` (Active Experimental Mechanism under test).
  - `TERMINAL_LIQUIDATION` (Defense-in-depth infrastructure; dormant until step 718).
  - `PHASE_SHUTDOWN` (Defense-in-depth infrastructure; dormant until step 672).
- **Quarantined Mechanisms (100% Inactive):**
  - `FRONTLOAD_ORDERS` (RETIRED / FALSIFIED).
  - `LOCAL_WEED_DIG`, `DYNAMIC_SHADOW_HARVEST`, `CARGO_FERRY_PRIORITY`, `OPPONENT_PREEMPT_SELL`, `EMERGENCY_FEED_PURCHASE`, `TERMINAL_HARVEST_SWEEP`, `TOWN_CYCLE`.
- **Safety Checker Invariants:** All 10 invariants active, requiring `fidelity == VERIFIED`.

---

## 5. Match Structure & Estimators

- **Cohort Size:** 50 contiguous seeds (`340250` through `340299` inclusive).
- **Match Design:** Double-blind Common Random Numbers (CRN) with mirror seat swapping:
  - **Match A:** Seat 0 = Treatment, Seat 1 = Control.
  - **Match B:** Seat 0 = Control, Seat 1 = Treatment.
- **Total Matches:** $50 \times 2 = 100$ games ($71,900$ treatment turns).
- **Paired Delta Estimator:**
  $$\Delta_s = \frac{1}{2} \left[ \left(\text{Margin}_{\text{treat, Seat 0}} - \text{Margin}_{\text{ctrl, Seat 1}}\right) + \left(\text{Margin}_{\text{treat, Seat 1}} - \text{Margin}_{\text{ctrl, Seat 0}}\right) \right]$$
- **Primary Metric:** Mean Paired Terminal-Margin Delta ($\overline{\Delta} = \frac{1}{N} \sum_{s=1}^N \Delta_s$).

### 5.1 Secondary Statistical & Robustness Analyses
The following preregistered secondary robustness tests and estimators are pre-specified and retained:
- **Two-Sided Wilcoxon Signed-Rank Test:** Paired non-parametric analysis on seed-averaged margin deltas $\Delta_s$.
- **Student-$t$ Confidence Intervals:** One-sided lower 95% confidence bound ($\overline{\Delta} - t_{0.05, 49} \times \text{SE}$) and two-sided 90% confidence interval for $\mu_\Delta$.
- **Bootstrap Procedure:** 95% BCa (bias-corrected and accelerated) bootstrap confidence interval for $\mu_\Delta$ based on $10,000$ paired resamples.
- **Win-Rate Definitions:**
  - *Primary Standard:* Total tournament matches $M = 100$:
    $$\Delta \text{WinRate} = \frac{W_{\text{treat}} - W_{\text{ctrl}}}{M} \times 100\text{ pp}$$
  - *Secondary Robustness Standard:* Ties excluded from denominator:
    $$\Delta \text{WinRate}_{\text{excl}} = \left( \frac{W_{\text{treat}}}{W_{\text{treat}} + W_{\text{ctrl}}} - \frac{W_{\text{ctrl}}}{W_{\text{treat}} + W_{\text{ctrl}}} \right) \times 100\text{ pp} \quad (\text{if } W_{\text{treat}} + W_{\text{ctrl}} > 0)$$
- **No Post-Hoc Tests:** No post-hoc statistical tests or altered thresholds may be introduced during or after execution.

---

## 6. Pre-Specified Decision Criteria

### 6.1 Primary Acceptance Criteria
Primary acceptance is kept strictly separate from the hypothesis definition. Primary acceptance requires satisfying **both** of the following conditions:
1. **Lower 95% Confidence Bound:**
   $$\text{Lower 95\% Bound for } \mu_\Delta \ge \$0.00$$
   (The one-sided lower 95% Student-$t$ confidence bound for the population mean paired terminal-margin delta must be $\ge \$0.00$).
2. **Win-Rate Non-Inferiority:**
   $$\Delta \text{WinRate} \ge -2.0\text{ percentage points}$$
   (Across all $M = 100$ mirror CRN matches).

*(Note: The confidence-bound condition is an operational decision criterion, not part of $H_0$.)*

### 6.2 Full Operational Acceptance Criteria (Must satisfy all 7)
1. `ACC_1`: One-sided lower 95% confidence bound for $\mu_\Delta \ge \$0.00$.
2. `ACC_2`: Win-rate delta $\Delta \text{WinRate} \ge -2.0\text{ percentage points}$.
3. `ACC_3`: Median paired margin delta $\ge \$0.00$.
4. `ACC_4`: 5th percentile margin delta $\ge -\$250.00$.
5. `ACC_5`: Zero safety violations (0 disqualifications, 0 illegal moves, 0 shed overflows).
6. `ACC_6`: Zero quarantined mechanism commits (100% quarantine adherence).
7. `ACC_7`: 100% adherence to `COUNTERFACTUAL_FIDELITY: VERIFIED`.

### 6.3 Falsification Bounds (Any triggers FALSIFIED classification)
1. `FALS_1`: Win-rate delta $\Delta \text{WinRate} < -2.0\text{ percentage points}$.
2. `FALS_2`: One-sided lower 95% confidence bound for $\mu_\Delta < \$0.00$.
3. `FALS_3`: Any rule violation, disqualification, or unhandled exception.
4. `FALS_4`: Any unquarantined commit of quarantined mechanism families.
5. `FALS_5`: Any execution of seeds within locked holdout `340050–340199`.

---

## 7. Statistical Power & Sensitivity Analysis

- **Sample Size:** $N = 50$ paired seeds ($100$ CRN mirror matches, $71,900$ treatment decision turns, $df = 49$).
- **Historical Variance & Standard Error:** Based on historical paired variance in EXP-AEC-002 ($s_{\Delta} \approx \$4.80$), the standard error of the mean for $N = 50$ is:
  $$\text{SE} = \frac{s_{\Delta}}{\sqrt{50}} = \frac{\$4.80}{7.071} \approx \$0.679$$
- **Critical Rejection Threshold ($\alpha = 0.05$, One-Sided, $df = 49$):**
  For degrees of freedom $df = 49$, the one-sided critical $t$-value is $t_{0.05, 49} \approx 1.6766$. The minimum observed sample mean required to reject $H_0$ and achieve a lower 95% confidence bound $\ge \$0.00$ is:
  $$\overline{\Delta}_{\text{crit}} = t_{0.05, 49} \times \text{SE} \approx 1.6766 \times \$0.6788 \approx +\$1.14$$
  *(Note: An observed effect size at the critical boundary $\mu_\Delta = +\$1.14$ corresponds to exactly 50.1% detection probability / 50% statistical power).*
- **Prospective Power & Minimum Detectable Effects:**
  Under the prospective $N = 50$ design with $\alpha = 0.05$ (one-sided) and historical variance ($s_\Delta \approx \$4.80$):
  - **80% Power ($\beta = 0.20$):** Powered to detect a true population effect size of:
    $$\mu_{\Delta, 80\%} = (t_{0.95, 49} + t_{0.80, 49}) \times \text{SE} \approx (1.6766 + 0.8480) \times \$0.6788 \approx +\$1.71$$
    (Standardized effect size Cohen's $d_z = \frac{\$1.71}{\$4.80} \approx 0.357$, small-to-medium effect).
  - **90% Power ($\beta = 0.10$):** Powered to detect a true population effect size of:
    $$\mu_{\Delta, 90\%} = (t_{0.95, 49} + t_{0.90, 49}) \times \text{SE} \approx (1.6766 + 1.2991) \times \$0.6788 \approx +\$2.02$$
    (Standardized effect size Cohen's $d_z = \frac{\$2.02}{\$4.80} \approx 0.421$).
- **Non-Inferiority Sensitivity:**
  The design provides rigorous 5% Type I error control against false non-inferiority claims when $\mu_\Delta < \$0.00$. If the true population delta is near zero ($\mu_\Delta \approx \$0.00$), the probability of obtaining a sample lower bound $\ge \$0.00$ is capped at $\alpha = 0.05$.

---

## 8. Classification Decision Matrix & Dormancy Interpretation

| Classification | Conditions | Scientific Interpretation |
|---|---|---|
| **ACTIVE_POSITIVE** | All 7 `ACC_*` pass, $\overline{\Delta} > \$0.00$, commits $\ge 5$. | Mechanism demonstrates causal, statistically certified economic superiority. |
| **ACTIVE_NON_INFERIOR** | All 7 `ACC_*` pass, $\overline{\Delta} \ge \$0.00$, commits $\ge 5$. | Mechanism eliminates frontload deficit without degrading baseline. |
| **ACTIVE_NEGATIVE** | Any `FALS_*` triggers, commits $\ge 5$. | Mechanism remains economically defective; candidate falsified. |
| **DORMANT / INCONCLUSIVE** | All safety checks pass, but commits $< 5$. | Inconclusive evaluation due to low activation opportunity. |
| **INVALID** | Safety violations, unquarantined commits, or holdout breach. | Execution invalid; protocol voided. |

### Dormancy Rule Specification
- **Threshold:** $\text{Commits} < 5 \implies \text{DORMANT / INCONCLUSIVE}$.
- **Governance Role:** The dormancy rule is strictly an **interpretation gate**, not an efficacy threshold. A trial with fewer than 5 commits reflects insufficient opportunity encounters during the 100 matches to establish causal efficacy, and must not be classified as active positive or non-inferior. Conversely, the dormancy threshold must never be used to post-hoc filter or manufacture statistical significance.

---

## 9. Immutable Freeze Verification Hashes

| Entity | Path | Expected SHA-256 |
|---|---|---|
| **V3 Backbone Tarball** | `submission_Vj_kc_v3.tar.gz` | `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` |
| **Prelaunch Audit** | `reports/EXP_AEC_003_PRELAUNCH_AUDIT.md` | `f36148c4cb955f9e7d64d4298cf1f32e1518e67a3648de523cd1486a79845fd3` |
| **Cohort Audit** | `reports/EXP_AEC_003_COHORT_AUDIT.md` | `14f9a1f3937a32e85c5207dbb839fab8de8f83148038283d84877b0889b5255a` |
| **Freeze Certification** | `reports/EXP_AEC_003_FINAL_FREEZE_CERTIFICATION.md` | Recorded upon certification |
| **AEC Config** | `aec/config.py` | `a92bb57785535d0c5b51895d5242fbf5a33f4a09c89b8160e8424bf245d63d55` |

---

## 10. Execution Governance Directive

**EXECUTION IS STRICTLY HALTED.**  
This document represents the formal prelaunch preregistration. No matches will be initiated until explicit authorization is granted.
