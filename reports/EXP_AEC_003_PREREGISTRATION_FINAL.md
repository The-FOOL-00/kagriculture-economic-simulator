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

### 2.1 Primary Hypothesis ($H_1$)
A causal, dependency-aware market timing compiler pass (`DEPENDENCY_AWARE_MARKET_TIMING`) that:
1. Detects intra-basket coupling via `SAME_ASSET_MARKET_COUPLING` edges,
2. Accounts for endogenous sequential price feedback across multi-order queues,
3. Refuses to frontload `SELL` before `BUY` on identical assets,
4. Evaluates clearing under conservative neutral rival modeling, and
5. Strictly requires `COUNTERFACTUAL_FIDELITY: VERIFIED`,

will achieve **statistical non-inferiority** ($\overline{\Delta} \ge \$0.00$, Lower 95% Bound $\ge \$0.00$, $\Delta \text{WinRate} \ge -2.0\text{ pp}$) against the Frozen V3 Control baseline across a prospective 50-seed cohort, completely eliminating the $-4.00\text{ pp}$ win-rate deficit caused by unconditional frontloading.

### 2.2 Null Hypothesis ($H_0$)
Tactical market order reordering, even when dependency-aware and verified under exact lockstep semantics, produces inferior or non-equivalent terminal margins ($\overline{\Delta} < \$0.00$ or Lower 95% Bound $< \$0.00$).

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

---

## 6. Pre-Specified Decision Criteria

### 6.1 Acceptance Criteria (Must satisfy all 7)
1. `ACC_1`: One-sided lower 95% confidence bound of $\overline{\Delta} \ge \$0.00$.
2. `ACC_2`: Win-rate delta $\Delta \text{WinRate} \ge -2.0\text{ percentage points}$.
3. `ACC_3`: Median paired margin delta $\ge \$0.00$.
4. `ACC_4`: 5th percentile margin delta $\ge -\$250.00$.
5. `ACC_5`: Zero safety violations (0 disqualifications, 0 illegal moves, 0 shed overflows).
6. `ACC_6`: Zero quarantined mechanism commits (100% quarantine adherence).
7. `ACC_7`: 100% adherence to `COUNTERFACTUAL_FIDELITY: VERIFIED`.

### 6.2 Falsification Bounds (Any triggers FALSIFIED classification)
1. `FALS_1`: Win-rate delta $\Delta \text{WinRate} < -2.0\text{ percentage points}$.
2. `FALS_2`: Lower 95% confidence bound $< \$0.00$.
3. `FALS_3`: Any rule violation, disqualification, or unhandled exception.
4. `FALS_4`: Any unquarantined commit of quarantined mechanism families.
5. `FALS_5`: Any execution of seeds within locked holdout `340050–340199`.

---

## 7. Statistical Power & Sensitivity Analysis

- **Sample Size:** $N = 50$ paired seeds ($100$ CRN matches).
- **Historical Standard Error:** In EXP-AEC-002, $s_{\Delta} \approx \$4.80$, yielding standard error $\text{SE} \approx \$0.68$.
- **Critical Threshold:** For a one-sided 95% lower bound $\ge \$0.00$, the sample mean must satisfy:
  $$\overline{\Delta} \ge 1.677 \times \text{SE} \approx \$1.14$$
- **Sensitivity:** The design is powered to detect an economic effect of $\ge +\$1.15$ per episode, or confirm non-inferiority if the true margin delta is non-negative and variance is comparable.

---

## 8. Classification Decision Matrix

| Classification | Conditions | Scientific Interpretation |
|---|---|---|
| **ACTIVE_POSITIVE** | All 7 `ACC_*` pass, $\overline{\Delta} > \$0.00$, commits $\ge 5$. | Mechanism demonstrates causal, statistically certified economic superiority. |
| **ACTIVE_NON_INFERIOR** | All 7 `ACC_*` pass, $\overline{\Delta} \ge \$0.00$, commits $\ge 5$. | Mechanism eliminates frontload deficit without degrading baseline. |
| **ACTIVE_NEGATIVE** | Any `FALS_*` triggers, commits $\ge 5$. | Mechanism remains economically defective; candidate falsified. |
| **DORMANT / INCONCLUSIVE** | All safety checks pass, but commits $< 5$. | Inconclusive evaluation due to low activation opportunity. |
| **INVALID** | Safety violations, unquarantined commits, or holdout breach. | Execution invalid; protocol voided. |

---

## 9. Immutable Freeze Verification Hashes

| Entity | Path | Expected SHA-256 |
|---|---|---|
| **V3 Backbone Tarball** | `submission_Vj_kc_v3.tar.gz` | `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` |
| **Prelaunch Audit** | `reports/EXP_AEC_003_PRELAUNCH_AUDIT.md` | Recorded upon creation |
| **Cohort Audit** | `reports/EXP_AEC_003_COHORT_AUDIT.md` | Recorded upon creation |
| **AEC Config** | `aec/config.py` | Recorded in commit `d9e03e8` + updates |

---

## 10. Execution Governance Directive

**EXECUTION IS STRICTLY HALTED.**  
This document represents the formal prelaunch preregistration. No matches will be initiated until explicit authorization is granted.
