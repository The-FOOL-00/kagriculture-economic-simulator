# EXP-AEC-002 Preregistration: Causally Validated Prospective Evaluation Protocol

**Preregistration Protocol:** PREREG-EXP-AEC-002-20260917  
**Date:** 2026-09-17  
**Status:** PREREGISTERED & FROZEN (EXECUTION STRICTLY HALTED)  
**Parent Studies:**
- `EXP-AEC-001` (Finding: Valid Non-Inferiority, Treatment Remained Dormant)
- `AEC V1.1 Final Readiness Audit` (Verdict: Ready Only After Final Development Fix)
- `AEC V1.1 Final Development Fix Verification` (Report: Complete, Parity Verified)  

**Authoritative Directive:** DO NOT LAUNCH EXP-AEC-002 YET. Prospective execution requires formal user review and authorization.

---

## 1. Scientific Governance & Non-Tuning Declaration

This protocol establishes a prospective evaluation of AEC V1.1 against the frozen V3 control under pre-committed experimental constraints:
1. **Fixed Cohort Invariance:** The experimental cohort is fixed to the standard pre-registered prospective block: seeds `340000`–`340049` (50 seeds, 100 paired CRN seat matches). The cohort has NOT been selected or modified based on performance.
2. **Holdout Partition Isolation:** Seeds `340050`–`340199` (150 seeds) remain strictly quarantined, locked, and unexecuted.
3. **Frozen Baseline Immutability:** The control agent is extracted from the immutable archive `submission_Vj_kc_v3.tar.gz` (SHA256: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`).
4. **Historical Isolation:** EXP-AEC-001 artifacts and execution records are read-only and immutable.
5. **No Outcome-Driven Parameter Tuning:** Latencies, search budgets, horizon allocations, and opportunity thresholds are fixed in advance and cannot be adjusted post-hoc.

---

## 2. Mechanism Governance and Status Specification

Under the findings of the Final Readiness Audit and the completed development fixes, the prospective treatment mechanism configuration is pre-committed as follows:

```python
ENABLED_FOUNDATION_MECHANISMS = (
    "FRONTLOAD_ORDERS",
    "TERMINAL_LIQUIDATION",
    "PHASE_SHUTDOWN",
)

QUARANTINED_MECHANISMS = (
    "LOCAL_WEED_DIG",
    "DYNAMIC_SHADOW_HARVEST",
    "CARGO_FERRY_PRIORITY",
    "OPPONENT_PREEMPT_SELL",
    "EMERGENCY_FEED_PURCHASE",
    "TERMINAL_HARVEST_SWEEP",
    "TOWN_CYCLE",
)
```

### Mechanism Roles

| Mechanism Family | Scientific Status | Experimental Role | Prospective Policy | Expected Frequency |
|---|---|---|---|---|
| **`FRONTLOAD_ORDERS`** | `VERIFIED_SOURCE` | **ACTIVE TREATMENT** | Certified by exact two-phase lockstep counterfactual simulation (`sim.hpp:578–617`). Reorders `SELL` before capital orders only when positive marginal advantage is certified. | Rare / Opportunistic |
| **`TERMINAL_LIQUIDATION`** | `VERIFIED_SOURCE` | **DEFENSE-IN-DEPTH** | Fail-closed endgame liquidation. Redundant with V3's primary line; commits only if unliquidated inventory unexpectedly exists at step 718. | Near-Zero |
| **`PHASE_SHUTDOWN`** | `VERIFIED_SOURCE` | **DEFENSE-IN-DEPTH** | Fail-closed late-game dead capital prevention. Redundant with V3; commits only if obsolete seed purchase unexpectedly passes macro planner. | Near-Zero |
| **`LOCAL_WEED_DIG`** | `QUARANTINED` | **QUARANTINED** | **Rejected at commitment gate.** Telemetry emits `decision="ABSTAIN"`, `abstain_reason="SCIENTIFIC_QUARANTINE"`. Exact baseline action returned. | **0.0% (Forbidden)** |

---

## 3. Opponent Pressure Model — Non-Overclaiming Declaration

In accordance with scientific integrity guidelines:
- **No Claim of Proven Behavioral Model:** The opponent pressure model (`sale_pressure >= threshold`) is **not** claimed as an empirically validated behavioral forecast of opponent intent.
- **Scientific Characterization:** Observed and forecast mature rival crops are treated solely as an **opportunity trigger** signaling potential market collision.
- **Causal Decider:** The counterfactual two-phase lockstep simulator alone determines whether an actual price priority advantage exists under the candidate reordering. If no rival sale occurs or prices are identical, the evaluator certifies zero advantage and AEC strictly abstains.

---

## 4. Experimental Design

### 4.1 Comparison Structure (Common Random Numbers)
- **Design:** Paired-seat Common Random Numbers (CRN).
- **Cohort Size:** $N = 50$ game seeds (`340000` through `340049`).
- **Matches per Seed:** Exactly 2 matches per seed (Seat 0 and Seat 1 switched).
- **Total Matches:** $M = 100$ completed games.
- **Pairing:**
  - Game A: Treatment (AEC V1.1) in Seat 0 vs Control (Frozen V3) in Seat 1.
  - Game B: Control (Frozen V3) in Seat 0 vs Treatment (AEC V1.1) in Seat 1.
- **Seat-Averaged Paired Metric:**
  $$\Delta \text{Margin}_s = \frac{1}{2} \left[ (\text{Margin}_{\text{treat, Seat 0}} - \text{Margin}_{\text{ctrl, Seat 1}}) + (\text{Margin}_{\text{treat, Seat 1}} - \text{Margin}_{\text{ctrl, Seat 0}}) \right]$$

### 4.2 Primary Outcome
- **Primary Metric:** Mean Paired Terminal Margin Delta ($\overline{\Delta \text{Margin}}$).
- **Statistical Test:** Two-sided Paired $t$-test ($\alpha = 0.05$) and Wilcoxon Signed-Rank Test.
- **Confidence Interval:** 95% Student's $t$ and 95% BCa Bootstrap Confidence Interval (10,000 resamples).

### 4.3 Secondary Outcomes
1. **Win Rate Delta ($\Delta \text{WinRate}$):** Treatment win rate minus Control win rate in percentage points.
2. **Mean Final Cash ($\Delta \text{Cash}$):** Average net cash delta at step 719.
3. **Commitments by Mechanism:** Cumulative count of committed actions for each mechanism family.
4. **Quarantine Invariant:** Total commits for `LOCAL_WEED_DIG` must be exactly 0.
5. **Peak Shed Utilization:** Maximum shed stock recorded across all matches ($\le 100$ units).
6. **Turn Latency:** Maximum per-step computation time ($\le 100$ ms target, strictly $< 1000$ ms fail-closed bound).

---

## 5. Formal Pre-Registered Hypotheses

### Primary Hypothesis (H1: Non-Inferiority and Opportunistic Value)
$$\begin{aligned}
H_0 &: \mu_{\Delta \text{Margin}} < 0 \\
H_1 &: \mu_{\Delta \text{Margin}} \ge 0 \quad \text{with non-inferior win rate } (\Delta \text{WinRate} \ge -2.0\text{ pp})
\end{aligned}$$

### Secondary Hypothesis (H2: Quarantine Integrity)
$$\text{Commits}(\text{LOCAL\_WEED\_DIG}) = 0 \quad \text{across all 72,000 treatment agent turns.}$$

### Secondary Hypothesis (H3: Ground-Truth Market Lockstep Parity)
Every committed `FRONTLOAD_ORDERS` intervention yields non-negative realized market cash difference ($\Delta M_{\text{our}} \ge 0$) under two-phase lockstep engine resolution.

---

## 6. Pre-Registered Decision Criteria

### 6.1 Acceptance Criteria (All Must Be Satisfied)
1. **`ACC_1` (Non-Inferior Win Rate):** $\Delta \text{WinRate} \ge -2.0\text{ pp}$.
2. **`ACC_2` (Non-Negative Mean Margin):** $\overline{\Delta \text{Margin}} \ge \$0.00$.
3. **`ACC_3` (Non-Negative Median Margin):** $\text{Median}(\Delta \text{Margin}) \ge \$0.00$.
4. **`ACC_4` (Bounded Tail Risk):** 5th percentile $\Delta \text{Margin} \ge -\$250.00$.
5. **`ACC_5` (Zero Safety Regressions):** 0 illegal moves, 0 shed overflow discards, 0 unhandled exceptions.
6. **`ACC_6` (Quarantine Adherence):** Exactly 0 commits of `LOCAL_WEED_DIG` or any quarantined family.

### 6.2 Falsification Boundaries (Any Triggers Rejection)
1. **`FALS_1`:** $\Delta \text{WinRate} < -2.0\text{ pp}$.
2. **`FALS_2`:** Statistically significant negative margin loss ($\overline{\Delta \text{Margin}} < -\$50.00$ with $p < 0.05$).
3. **`FALS_3`:** Any disqualified match or game rule violation.
4. **`FALS_4`:** Any shed stock $> 100$ causing item deletion.
5. **`FALS_5`:** Any step latency $> 1000$ ms.
6. **`FALS_6`:** Any commitment of a quarantined mechanism.

---

## 7. Execution Readiness Gate

| Condition | Status | Verification Reference |
|---|---|---|
| Frozen V3 Control SHA256 Verified | **CONFIRMED** | `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943` |
| `LOCAL_WEED_DIG` Quarantined in Config & Registry | **CONFIRMED** | `ScientificStatus.QUARANTINED` in `config.py` |
| Two-Phase Lockstep Market Parity ($+\$31 / -\$30 / +\$61$) | **CONFIRMED** | Bit-exact parity in `tests/aec/test_v1_1_development_fixes.py` |
| Full AEC Regression Test Suite Passing | **CONFIRMED** | 110/110 tests passing |
| Holdout Range `340050`–`340199` Untouched | **CONFIRMED** | 100% untouched |
| Prospective Seeds Executed | **ZERO** | 0 prospective seeds run |
| EXP-AEC-002 Run Execution | **HALTED** | Pending explicit user authorization |

**Preregistration Seal:** `PREREG-EXP-AEC-002-20260917-FROZEN`
