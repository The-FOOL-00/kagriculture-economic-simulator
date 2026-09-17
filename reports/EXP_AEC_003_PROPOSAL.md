# EXP-AEC-003 Preregistration Proposal: Causal Dependency-Aware Market Timing

**Protocol Identifier:** `PREREG-EXP-AEC-003-20260917-PROPOSAL`  
**Date Established:** 2026-09-17  
**Governance Standard:** Strict Scientific Governance & Prospective Double-Blind CRN Protocol  
**Execution Status:** **FROZEN PROPOSAL — STRICT EXECUTION HALT**  
**Authoritative Directive:** **DO NOT EXECUTE.** This document is a formal scientific proposal. No prospective seed may be executed, simulated, or scouted without explicit formal user authorization.

---

## 1. Scientific Context & Parent Study Lineage

This prospective evaluation proposal directly succeeds:
1. **`EXP-AEC-001` (Historical / Consumed):** Verified baseline non-inferiority under conservative isolation gates (0 commits).
2. **`EXP-AEC-002` (Historical / Falsified):** Evaluated unconditional `FRONTLOAD_ORDERS`. Falsified with mean paired margin $-\$0.92$, lower 95% bound $-\$2.07$, win-rate delta $-4.00\text{ pp}$. Forensic audit revealed intra-basket price impact blindness and opponent dump hallucinations.
3. **`AEC Architecture Checkpoint V1.2` (`reports/AEC_ARCHITECTURE_CHECKPOINT.md`):**
   - Built `ActionBasketDependencyGraph` (`aec/ir/dependency_graph.py`) with explicit same-asset, cash, and capacity coupling edges.
   - Repaired counterfactual simulator to follow exact engine lockstep market clearing.
   - Validated 15/15 market coupling parity cases against ground-truth `kagsim` engine with 100% exact numeric equality.
   - Enforced `COUNTERFACTUAL_FIDELITY: VERIFIED` safety certificate gating.

---

## 2. Core Scientific Hypothesis

### 2.1 Primary Hypothesis ($H_1$)
A causal, dependency-aware market timing compiler (`DEPENDENCY_AWARE_MARKET_TIMING`) that:
1. Detects intra-basket coupling via `SAME_ASSET_MARKET_COUPLING` edges,
2. Accounts for endogenous price feedback across multi-order queues,
3. Evaluates clearing under conservative neutral rival modeling (eliminating phantom dump arbitrage), and
4. Strictly requires `COUNTERFACTUAL_FIDELITY: VERIFIED`,

will achieve **statistical non-inferiority** ($\overline{\Delta} \ge \$0.00$, Lower 95% Bound $\ge \$0.00$, $\Delta \text{WinRate} \ge -2.0\text{ pp}$) against the Frozen V3 Control baseline across a prospective 50-seed cohort, completely eliminating the $-4.00\text{ pp}$ deficit caused by unconditional frontloading.

### 2.2 Null Hypothesis ($H_0$)
Tactical market order reordering, even when dependency-aware and verified under exact lockstep semantics, produces inferior or non-equivalent terminal margins ($\overline{\Delta} < \$0.00$ or Lower 95% Bound $< \$0.00$).

---

## 3. Cohort Partition & Protection Protocol

```
[340000 ----------- 340049] [340050 ----------- 340199] [340200 ----------- 340249] [340250 ----------- 340299]
    EXP-AEC-001 (HISTORICAL)      AEC LOCKED HOLDOUT (150)     EXP-AEC-002 (HISTORICAL)     EXP-AEC-003 (PROSPECTIVE)
      PERMANENTLY CONSUMED           STRICTLY TOUCHLESS          PERMANENTLY CONSUMED         PROPOSED VIRGIN COHORT
```

| Partition | Seed Range | Size ($N$) | Status | Governance Covenant |
|---|---|---|---|---|
| `HISTORICAL-AEC-001` | `340000–340049` | 50 seeds | **CONSUMED** | Historical archive. Never rerun. |
| `LOCKED-HOLDOUT-AEC` | `340050–340199` | 150 seeds | **LOCKED HOLDOUT** | **Touchless.** Strictly quarantined. Zero simulation, zero inspection. |
| `HISTORICAL-AEC-002` | `340200–340249` | 50 seeds | **CONSUMED** | Historical archive. Results frozen. |
| **`PROSPECTIVE-AEC-003`** | `340250–340299` | 50 seeds | **PROPOSED PROSPECTIVE** | Pre-registered contiguous cohort. Virgin and unexecuted. |

---

## 4. Experimental Match Design

- **Cohort:** 50 contiguous seeds (`340250` through `340299` inclusive).
- **Match Structure:** 2 mirror Common Random Numbers (CRN) matches per seed:
  - **Match A:** Player 0 = AEC V1.2 (`DEPENDENCY_AWARE_MARKET_TIMING`), Player 1 = Frozen V3 Control.
  - **Match B:** Player 0 = Frozen V3 Control, Player 1 = AEC V1.2 (`DEPENDENCY_AWARE_MARKET_TIMING`).
- **Total Matches:** $50 \times 2 = 100$ games ($71,900$ treatment turns).
- **Paired Delta Estimator:**
  $$\Delta_s = \frac{1}{2} \left[ \left(\text{Margin}_{\text{treat, Seat 0}} - \text{Margin}_{\text{ctrl, Seat 1}}\right) + \left(\text{Margin}_{\text{treat, Seat 1}} - \text{Margin}_{\text{ctrl, Seat 0}}\right) \right]$$

---

## 5. Pre-Specified Decision Criteria

### 5.1 Acceptance Criteria (Must meet all 7)
1. `ACC_1`: One-sided lower 95% confidence bound of $\overline{\Delta} \ge \$0.00$.
2. `ACC_2`: Win-rate delta $\Delta \text{WinRate} \ge -2.0\text{ percentage points}$.
3. `ACC_3`: Median paired margin delta $\ge \$0.00$.
4. `ACC_4`: 5th percentile margin delta $\ge -\$250.00$.
5. `ACC_5`: Zero safety violations (0 disqualifications, 0 illegal moves, 0 shed overflows).
6. `ACC_6`: Zero quarantined mechanism commits (100% quarantine adherence).
7. `ACC_7`: 100% adherence to `COUNTERFACTUAL_FIDELITY: VERIFIED`.

### 5.2 Falsification Bounds (Any triggers FALSIFIED verdict)
1. `FALS_1`: Win-rate delta $\Delta \text{WinRate} < -2.0\text{ percentage points}$.
2. `FALS_2`: Lower 95% confidence bound $< \$0.00$.
3. `FALS_3`: Any rule violation, disqualification, or unhandled exception.
4. `FALS_4`: Any unquarantined commit of quarantined mechanism families.
5. `FALS_5`: Any execution of seeds within the locked holdout `340050–340199`.

---

## 6. Scientific Justification: Why This Is the Highest-Value Next Test

1. **Direct Hypothesis Closure:** EXP-AEC-002 falsified unconditional sell-before-buy frontloading. The highest-value scientific action is to test whether the causal, dependency-aware reformulation eliminates the failure mode on a clean prospective cohort.
2. **Methodological Rigor:** Testing `DEPENDENCY_AWARE_MARKET_TIMING` isolates the effect of the repaired counterfactual engine and dependency DAG from unrelated multi-worker route heuristics.
3. **No Risk to Holdout:** Conducted on contiguous prospective seeds `340250–340299`, preserving the pristine locked holdout `340050–340199`.
4. **Governed Freeze:** Completely pre-registered before execution.
