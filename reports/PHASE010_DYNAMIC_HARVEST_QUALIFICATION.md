# AEC PHASE 010: DYNAMIC SHADOW HARVEST QUALIFICATION REPORT
**Mechanism**: `DYNAMIC_SHADOW_HARVEST`  
**Priority Group**: Group A (Priority 1)  
**Evaluation Stage**: Stage A (Pilot Exposure Replay on Fresh Development Seeds `249050–249052`)  
**Matches Evaluated**: 6 Common Random Numbers (CRN) Mirror-Seat Matches (3 Seeds x 2 Seats)  
**Date**: 2026-09-18  
**Architecture Freeze Hash**: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`  
**Governance Scope**: Zero Touches of Protected Cohorts (`340050–340199`, `214200–214249`, `340300–340349`)  

---

## 1. Executive Summary & Qualification Decision

| Metric | Empirical Result | Governance Gate Criterion | Gate Status |
| :--- | :--- | :--- | :--- |
| **Implementation Integrity** | 100% complete; multi-worker coupled patch | Complete Python architecture | **PASSED** |
| **Synthetic Activation** | 100% passing (`test_matrix_1_dynamic_shadow_harvest`) | Passes full mock compiler pipeline | **PASSED** |
| **Opportunity Detection** | 1,876 target opportunities detected | $\ge 1$ opportunities | **PASSED** |
| **Exact Simulations Run** | 900+ counterfactual rollouts | $\ge 1$ exact simulations | **PASSED** |
| **Committed Patches** | **0 Commits** (0.0% commit rate given exposure) | $\ge 1$ commits required for efficacy test | **UNMET (DORMANT)** |
| **Safety Failures** | 0 Safety Violations (100% safe) | 0 Safety Violations | **PASSED** |
| **Mean Net Delta** | **-$4.67 ± $4.67** ($t=-1.00$, $p=0.3173$) | $\text{Mean}(\Delta) > 0.0$ | **INSUFFICIENT** |
| **Final Classification** | **DORMANT / ECONOMICALLY DOMINATED BY BASELINE** | — | **QUARANTINED** |

**Official Gate Decision**: **DORMANT / FUNCTIONALLY COMPLETE (QUARANTINED FROM LIVE)**.  
The mechanism is structurally sound and synthetically verified, but in full-game empirical play against the pristine V3 chassis, it experiences zero commits because the baseline already captures mature crop harvest value or the proposed reallocation is economically dominated. Per Part X and XI, no post-hoc tuning will be performed to artificially manufacture commits.

---

## 2. Telemetry & Empirical Exposure Breakdown

From `results/PHASE010_DYNAMIC_SHADOW_HARVEST_PILOT_TELEMETRY.json`:
- **Seeds Evaluated**: `249050`, `249051`, `249052` (N=3 fresh seeds, 6 matches)
- **Elapsed Replay Runtime**: 1229.6s (204.9s / match)
- **Target Candidates Screened**: 1,876 candidates
- **Target Exact Simulations**: 932 simulations
- **Target Commits**: 0
- **Foundation Commits**: 2 (100% `DEPENDENCY_AWARE_MARKET_TIMING`)
- **Total Abstentions**: 930
- **Primary Abstain Classification**: `NO_CANDIDATE_CERTIFIED_SUPERIOR` (Economic dominance by V3 baseline)
- **Safety Rejections**: 0
- **Runtime Exceptions / Aborts**: 0 (100% fail-closed stability)
- **Mirror Record**: 0 Wins / 1 Loss / 2 Ties
- **Seed Deltas**:
  - Seed `249050`: -$14.0 (S0: -$14, S1: -$14)
  - Seed `249051`: +$0.0 (S0: +$0, S1: +$0)
  - Seed `249052`: +$0.0 (S0: +$0, S1: +$0)

---

## 3. Root-Cause Diagnostic Analysis (Per Part X)

Under Part X of the scientific governance protocol:
> *Distinguish: NATURALLY DORMANT, OPPORTUNITY RARE, DETECTOR TOO CONSERVATIVE, FUNNEL TOO CONSERVATIVE, ECONOMICALLY DOMINATED, INTEGRATION BUG.*

1. **Not an Integration Bug**: `LaborOpportunityAnalyzer` successfully detects mature crops, resolves coordinates, passes candidates to `HarvestCoupledPatchGenerator`, simulates trajectories, and performs safety checking without error.
2. **Not Opportunity Rare**: 1,876 candidates were generated across 6 matches (~312 opportunities per match).
3. **Primary Cause: ECONOMICALLY DOMINATED BY V3 BASELINE**:
   - The V3 baseline incorporates an internal greedy agricultural scheduler that routes workers to mature crops within 1–2 turns of biological readiness.
   - When `DYNAMIC_SHADOW_HARVEST` proposes diverting an auxiliary worker to harvest a mature plant, the 18-step exact counterfactual rollout reveals that either:
     a) The baseline worker arrives at the same tile within 2 steps anyway, resulting in $\Delta_{\text{margin}} = \$0.00$; or
     b) Diverting the worker delays other baseline operations (e.g. crop watering or market transport), creating net negative or zero incremental margin ($\Delta_{\text{margin}} \le 15.0$).
   - As a result, the candidate is safely and correctly rejected by `WinModel` as economically inferior to the baseline plan.

---

## 4. Scientific Conclusion & Governance Action

1. `DYNAMIC_SHADOW_HARVEST` remains **quarantined** from the `AEC_ROBUST_QUALIFIED` build.
2. The implementation is preserved in `AEC_RESEARCH_FULL` as functionally complete.
3. No further qualification seeds will be spent on this mechanism, adhering to Part XXVI (Stop Conditions: insufficient exposure / economic dominance).
