# AEC PHASE 010: CARGO FERRY QUALIFICATION REPORT
**Mechanism**: `CARGO_FERRY`  
**Priority Group**: Group B (Priority 5)  
**Evaluation Stage**: Stage A (Pilot Exposure Replay on Fresh Development Seeds `249059–249061`)  
**Matches Evaluated**: 6 Common Random Numbers (CRN) Mirror-Seat Matches (3 Seeds x 2 Seats)  
**Date**: 2026-09-18  
**Architecture Freeze Hash**: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`  
**Governance Scope**: Zero Touches of Protected Cohorts (`340050–340199`, `214200–214249`, `340300–340349`)  

---

## 1. Executive Summary & Qualification Decision

| Metric | Empirical Result | Governance Gate Criterion | Gate Status |
| :--- | :--- | :--- | :--- |
| **Implementation Integrity** | Complete Python implementation (`aec/opportunities/cargo_ferry.py`) | Two-worker coupled trajectory synthesis | **PASSED** |
| **Synthetic Activation** | 100% passing (`test_matrix_4_cargo_ferry`) | Mock compiler pipeline certified | **PASSED** |
| **Opportunity Detection** | 744 ferry candidates proposed | $\ge 1$ candidates | **PASSED** |
| **Exact Simulations Run** | 372 counterfactual simulations | $\ge 1$ exact simulations | **PASSED** |
| **Committed Patches** | **0 Commits** (0.0% commit rate given exposure) | $\ge 1$ commits required for efficacy test | **UNMET (DORMANT)** |
| **Safety Failures** | 0 Safety Violations (100% safe) | 0 Safety Violations | **PASSED** |
| **Mean Net Delta** | **+$26.00 ± $28.45** ($t=0.91$, $p=0.3608$) | $\text{Mean}(\Delta) > 0.0$ | **UNATTRIBUTED (0 commits)** |
| **Final Classification** | **DORMANT / ECONOMICALLY DOMINATED BY BASELINE** | — | **QUARANTINED** |

**Official Gate Decision**: **DORMANT / FUNCTIONALLY COMPLETE (QUARANTINED FROM LIVE)**.  
The two-worker cargo ferry mechanism is structurally verified and collision-free. In full-game matches against the frozen baseline, it proposed 744 candidates across 6 matches, but all 744 abstained in exact counterfactual simulation. Per Part XV, diverting an auxiliary worker to haul cargo merely shifts labor cost from the farmer to the hand without improving joint two-worker trajectory margin. The observed +$26.00 net delta was 100% attributable to foundation `DEPENDENCY_AWARE_MARKET_TIMING` (10 commits). The mechanism remains quarantined.

---

## 2. Telemetry & Empirical Exposure Breakdown

From `results/PHASE010_CARGO_FERRY_PILOT_TELEMETRY.json`:
- **Seeds Evaluated**: `249059`, `249060`, `249061` (N=3 fresh seeds, 6 matches)
- **Elapsed Replay Runtime**: 1275.8s (212.6s / match)
- **Target Candidates Screened**: 744 candidates
- **Target Exact Simulations**: 372 simulations
- **Target Commits**: 0
- **Foundation Commits**: 10 (100% `DEPENDENCY_AWARE_MARKET_TIMING`)
- **Total Abstentions**: 372
- **Primary Abstain Reason**: `NO_CANDIDATE_CERTIFIED_SUPERIOR`
- **Safety Rejections**: 0
- **Runtime Exceptions / Aborts**: 0 (100% fail-closed stability)
- **Mirror Record**: 2 Wins / 1 Loss / 0 Ties
- **Seed Deltas**:
  - Seed `249059`: +$78.0 (S0: +$78, S1: +$78)
  - Seed `249060`: +$20.0 (S0: +$20, S1: +$20)
  - Seed `249061`: -$20.0 (S0: -$20, S1: -$20)

---

## 3. Root-Cause Diagnostic Analysis (Per Part XV)

Under Part XV of the qualification protocol:
1. **Auxiliary Worker Opportunity Cost**:
   - In baseline V3 operation, when auxiliary hands are hired, their time is strictly allocated to crop maintenance (watering and harvesting).
   - Reassigning an auxiliary hand to ferry cargo saves the Farmer travel steps, but forgoes the Hand's field production. The exact simulator projects that the net economic benefit $\Delta_{\text{net}} = V_{\text{farmer\_saved}} - \text{OppCost}_{\text{hand}}$ is near-zero or negative.
2. **Two-Worker Coupling Invariant**:
   - Part XV explicitly mandates: *"Reject any commit where the ferry merely transfers cost from one worker to another without improving the full trajectory."*
   - The AEC candidate funnel and `WinModel` strictly adhered to this invariant, refusing to commit zero-margin diversions.
3. **Attribution Purity**:
   - 100% of realized commits were foundation market timing adjustments, confirming pure attribution.

---

## 4. Scientific Conclusion & Governance Action

1. `CARGO_FERRY` remains **quarantined** from `AEC_ROBUST_QUALIFIED`.
2. Two-worker coordination logic is preserved in `AEC_RESEARCH_FULL`.
3. Stop condition reached per Part XXVI: zero commits under exact counterfactual certification.
