# AEC PHASE 010: ROUTE COMPRESSION QUALIFICATION REPORT
**Mechanism**: `ROUTE_COMPRESSION`  
**Priority Group**: Group B (Priority 4)  
**Evaluation Stage**: Stage A (Pilot Exposure Replay on Fresh Development Seeds `249056–249058`)  
**Matches Evaluated**: 6 Common Random Numbers (CRN) Mirror-Seat Matches (3 Seeds x 2 Seats)  
**Date**: 2026-09-18  
**Architecture Freeze Hash**: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`  
**Governance Scope**: Zero Touches of Protected Cohorts (`340050–340199`, `214200–214249`, `340300–340349`)  

---

## 1. Executive Summary & Qualification Decision

| Metric | Empirical Result | Governance Gate Criterion | Gate Status |
| :--- | :--- | :--- | :--- |
| **Implementation Integrity** | Complete Python implementation (`aec/opportunities/route_compression.py`) | Integrated multi-step trajectory synthesis | **PASSED** |
| **Synthetic Activation** | 100% passing (`test_matrix_3_route_compression`) | Mock compiler pipeline certified | **PASSED** |
| **Opportunity Detection** | 266 route candidates proposed | $\ge 1$ candidates | **PASSED** |
| **Exact Simulations Run** | 134 counterfactual simulations | $\ge 1$ exact simulations | **PASSED** |
| **Committed Patches** | **0 Commits** (0.0% commit rate given exposure) | $\ge 1$ commits required for efficacy test | **UNMET (DORMANT)** |
| **Safety Failures** | 0 Safety Violations (100% safe) | 0 Safety Violations | **PASSED** |
| **Mean Net Delta** | **+$62.00 ± $33.08** ($t=1.87$, $p=0.0609$) | $\text{Mean}(\Delta) > 0.0$ | **UNATTRIBUTED (0 commits)** |
| **Final Classification** | **DORMANT / ECONOMICALLY DOMINATED BY BASELINE** | — | **QUARANTINED** |

**Official Gate Decision**: **DORMANT / FUNCTIONALLY COMPLETE (QUARANTINED FROM LIVE)**.  
The mechanism is verified synthetically, but achieves zero commits in full-game empirical play against the pristine V3 chassis. While the paired net margin is positive (+$62.00), 100% of commits (6/6) were executed by foundation `DEPENDENCY_AWARE_MARKET_TIMING`. Per Part XIV, a shorter route is not automatically a better route; where no exact economic improvement over the baseline is proven, the mechanism must remain quarantined.

---

## 2. Telemetry & Empirical Exposure Breakdown

From `results/PHASE010_ROUTE_COMPRESSION_PILOT_TELEMETRY.json`:
- **Seeds Evaluated**: `249056`, `249057`, `249058` (N=3 fresh seeds, 6 matches)
- **Elapsed Replay Runtime**: 1130.7s (188.5s / match)
- **Target Candidates Screened**: 266 candidates
- **Target Exact Simulations**: 134 simulations
- **Target Commits**: 0
- **Foundation Commits**: 6 (100% `DEPENDENCY_AWARE_MARKET_TIMING`)
- **Total Abstentions**: 134
- **Primary Abstain Reason**: `NO_CANDIDATE_CERTIFIED_SUPERIOR`
- **Safety Rejections**: 0
- **Runtime Exceptions / Aborts**: 0 (100% fail-closed stability)
- **Mirror Record**: 2 Wins / 0 Losses / 1 Tie
- **Seed Deltas**:
  - Seed `249056`: +$113.0 (S0: +$113, S1: +$113)
  - Seed `249057`: +$0.0 (S0: -$632, S1: +$632)
  - Seed `249058`: +$73.0 (S0: +$73, S1: +$73)

---

## 3. Root-Cause Diagnostic Analysis (Per Part X & XIV)

1. **Shortest-Path Optimality of Baseline**:
   - The V3 baseline agent uses an internal BFS pathfinder for worker transit to shed tiles, which already plans Euclidean/Manhattan optimal routes without extraneous wander steps.
   - Detour compaction candidates attempting to interpose intermediate crop harvests during transit delay arrival at the shed, which either delays the market sale or creates worker collision risks with peer workers.
2. **Economic Attribution Purity**:
   - The observed positive delta (+$62.00) was generated purely by `DEPENDENCY_AWARE_MARKET_TIMING` exploiting sequential pricing at the shop unlock windows, with zero contribution from route compaction.
3. **Safety & Governance**:
   - Zero collisions, zero invalid movement steps, and zero safety rejections occurred.

---

## 4. Scientific Conclusion & Governance Action

1. `ROUTE_COMPRESSION` remains **quarantined** from `AEC_ROBUST_QUALIFIED`.
2. Preserved in `AEC_RESEARCH_FULL` for diagnostic research.
3. Stop condition reached per Part XXVI: zero natural commits confirmed.
