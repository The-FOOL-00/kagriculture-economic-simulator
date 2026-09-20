# AEC PHASE 010: OPPONENT PREEMPTION QUALIFICATION REPORT
**Mechanism**: `OPPONENT_PREEMPT_SELL`  
**Priority Group**: Group E (Priority 12)  
**Evaluation Stage**: Stage A (Pilot Exposure Replay on Fresh Development Seeds `249080–249082`)  
**Matches Evaluated**: 6 Common Random Numbers (CRN) Mirror-Seat Matches (3 Seeds x 2 Seats)  
**Date**: 2026-09-18  
**Architecture Freeze Hash**: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`  
**Governance Scope**: Zero Touches of Protected Cohorts (`340050–340199`, `214200–214249`, `340300–340349`)  

---

## 1. Executive Summary & Qualification Decision

| Metric | Empirical Result | Governance Gate Criterion | Gate Status |
| :--- | :--- | :--- | :--- |
| **Implementation Integrity** | Complete Python implementation (`aec/opportunities/preemption.py`) | Opponent supply forecasting & frontload | **PASSED** |
| **Synthetic Activation** | 100% passing (`test_matrix_10`) | Mock compiler pipeline certified | **PASSED** |
| **Opportunity Detection** | 7,812 target candidates proposed | $\ge 1$ candidates | **PASSED (HIGH PROPOSALS)** |
| **Exact Simulations Run** | 3,906 counterfactual simulations | $\ge 1$ exact simulations | **PASSED** |
| **Committed Patches** | **2 Commits** (0.02% commit rate given exposure) | $\ge 1$ commits (Active Exposure) | **PASSED** |
| **Safety Failures** | 0 Safety Violations | 0 Safety Violations | **PASSED** |
| **Mean Net Delta** | **-$96.67 ± $96.67** ($t=-1.00$, $p=0.3173$) | $\text{Mean}(\Delta) > 0.0$ | **CRITICAL FAILURE** |
| **Per-Commit Realized Loss** | **-$145.00 per commit** | $\text{RealizedDelta} > 0$ | **HARMFUL COMMITS** |
| **Mirror Record** | **0 Wins / 1 Loss / 2 Ties (0.0% Win Rate)** | $\text{WinRate} \ge 50\%$ | **CRITICAL FAILURE** |
| **Downside Risk (P95)** | **-$261.00** | No catastrophic drawdown | **CRITICAL FAILURE** |
| **Final Classification** | **FAILED QUALIFICATION (STRICTLY QUARANTINED)** | — | **STRICTLY QUARANTINED** |

**Official Gate Decision**: **FAILED QUALIFICATION (STRICTLY QUARANTINED)**.  
As anticipated in Part XIX, opponent preemption produces harmful commits in tournament play. On seeds where the mechanism abstained (249080, 249081), net delta was exactly $0.00. On the seed where it committed (seed 249082, 2 commits), net margin plummeted to **-$290.00** (-$145.00 per commit). False opponent dumping forecasts caused premature market liquidation at suboptimal prices, sacrificing market clearing depth. The mechanism is permanently quarantined.

---

## 2. Empirical Performance & Seed-by-Seed Breakdown

From `results/PHASE010_OPPONENT_PREEMPT_SELL_PILOT_RESULTS.csv` and `results/PHASE010_OPPONENT_PREEMPT_SELL_PILOT_TELEMETRY.json`:
- **Seeds Evaluated**: `249080`, `249081`, `249082` (N=3 fresh seeds, 6 matches)
- **Elapsed Replay Runtime**: 814.9s (135.8s / match)
- **Target Candidates Screened**: 7,812 candidates
- **Target Exact Simulations**: 3,906 simulations
- **Target Commits**: 2 commits (100% `OPPONENT_PREEMPT_SELL`)
- **Foundation Commits**: 0 commits
- **Seed Deltas**:
  - Seed `249080`: +$0.0 (S0: +$0, S1: +$0) | 0 commits
  - Seed `249081`: +$0.0 (S0: +$78, S1: -$78) | 0 commits
  - Seed `249082`: **-$290.0** (S0: -$290, S1: -$290) | **2 commits of `OPPONENT_PREEMPT_SELL`**

---

## 3. Forensic Root-Cause Analysis (Per Part XIX)

Under Part XIX of the protocol:
> *"Pay particular attention to: false opponent signal, market timing error, unnecessary preemption, opportunity cost of selling early. If it remains harmful: retain quarantine."*

1. **False Opponent Dumping Signals**:
   - The opponent forecasting heuristic detected opponent inventory accumulation and projected an imminent supply dump.
   - However, the opponent agent did not dump at the anticipated step; rather, it held or cycled crops through normal production.
2. **Opportunity Cost of Early Liquidation**:
   - Preemptively dumping shed inventory sold goods prior to peak town demand ticks, locking in low clearing prices and exhausting market capacity.
   - When the agent later harvested fresh crops, market prices had been depressed by its own preemptive dumping, compounding the loss.
3. **Harmful Commit Rate**:
   - 100% of commits (2/2) were economically destructive (-$145/commit).

---

## 4. Scientific Conclusion & Governance Action

1. `OPPONENT_PREEMPT_SELL` is **FAILED**.
2. It remains **strictly quarantined** from `AEC_ROBUST_QUALIFIED` and barred from all prospective tournament submissions.
3. Stop conditions reached per Part XXVI.
