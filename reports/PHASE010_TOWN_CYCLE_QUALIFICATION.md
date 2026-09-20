# AEC PHASE 010: TOWN CYCLE MARKET TIMING QUALIFICATION REPORT
**Mechanism**: `TOWN_CYCLE`  
**Priority Group**: Group C (Priority 6)  
**Evaluation Stage**: Stage A (Pilot Exposure Replay on Fresh Development Seeds `249062–249064`)  
**Matches Evaluated**: 6 Common Random Numbers (CRN) Mirror-Seat Matches (3 Seeds x 2 Seats)  
**Date**: 2026-09-18  
**Architecture Freeze Hash**: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`  
**Governance Scope**: Zero Touches of Protected Cohorts (`340050–340199`, `214200–214249`, `340300–340349`)  

---

## 1. Executive Summary & Qualification Decision

| Metric | Empirical Result | Governance Gate Criterion | Gate Status |
| :--- | :--- | :--- | :--- |
| **Implementation Integrity** | Complete Python implementation (`aec/opportunities/town_cycle.py`) | Integrated causal order mutation | **PASSED** |
| **Synthetic Activation** | 100% passing (`test_matrix_5_town_cycle`) | Passes full mock compiler pipeline | **PASSED** |
| **Opportunity Detection** | 1,337 target candidates proposed | $\ge 1$ candidates | **PASSED** |
| **Exact Simulations Run** | 682 counterfactual simulations | $\ge 1$ exact simulations | **PASSED** |
| **Committed Patches** | **247 Commits** (18.5% commit rate given exposure) | $\ge 1$ commits (Active Exposure) | **PASSED (HIGH EXPOSURE)** |
| **Safety Failures** | 0 Safety Violations | 0 Safety Violations | **PASSED** |
| **Mean Net Delta** | **-$36,655.33 ± $14,386.69** ($t=-2.55$, $p=0.0108$) | $\text{Mean}(\Delta) > 0.0$ | **CRITICAL FAILURE** |
| **95% Confidence Interval** | **[-$64,853.24, -$8,457.43]** | Bounded above zero | **CRITICAL FAILURE** |
| **Mirror Record** | **0 Wins / 3 Losses / 0 Ties (0.0% Win Rate)** | $\text{WinRate} \ge 50\%$ | **CRITICAL FAILURE** |
| **Downside Risk (P95)** | **-$61,183.40** | No catastrophic drawdown | **CRITICAL FAILURE** |
| **Final Classification** | **FAILED QUALIFICATION (PERMANENTLY QUARANTINED)** | — | **STRICTLY QUARANTINED** |

**Official Gate Decision**: **FAILED QUALIFICATION (STRICTLY QUARANTINED)**.  
The mechanism achieves real-game exposure and commits frequently (247 commits across 6 matches), but produces severe, statistically significant economic destruction: a net margin loss of **-$36,655.33 per seed** ($t=-2.55, p=0.0108$), 0 wins out of 3 seeds, and catastrophic liquidity starvation. Per Part XXI, `TOWN_CYCLE` is permanently barred from live deployment and strictly quarantined.

---

## 2. Empirical Performance & Seed-by-Seed Breakdown

From `results/PHASE010_TOWN_CYCLE_PILOT_RESULTS.csv` and `results/PHASE010_TOWN_CYCLE_PILOT_TELEMETRY.json`:
- **Seeds Evaluated**: `249062`, `249063`, `249064` (N=3 fresh seeds, 6 matches)
- **Elapsed Replay Runtime**: 903.2s (150.5s / match)
- **Target Commits**: 247 commits (100% `TOWN_CYCLE`)
- **Foundation Commits**: 8 commits (`DEPENDENCY_AWARE_MARKET_TIMING`)
- **Seed Deltas**:
  - Seed `249062`: -$23,126.0 (S0: -$23,126, S1: -$23,126) | 80 `TOWN_CYCLE` commits
  - Seed `249063`: -$65,412.0 (S0: -$62,091, S1: -$68,733) | 89 `TOWN_CYCLE` commits
  - Seed `249064`: -$21,428.0 (S0: -$21,428, S1: -$21,428) | 78 `TOWN_CYCLE` commits

---

## 3. Forensic Root-Cause Analysis (Per Part XVI)

Under Part XVI of the qualification protocol:
> *"Do NOT assume: town cycle always means hold or town cycle always means advance. The experiment determines whether the signal is economically useful."*

Forensic tracing of the 247 commits revealed the exact economic failure mechanism:
1. **Liquidity Starvation from Delayed Sales (`DELAY_SALE`)**:
   - In baseline play, the agent sells shed crops immediately to fund the continuous purchase of high-yield seeds (e.g. melon, strawberry) and hire field labor.
   - `TownCycleSignalDetector` repeatedly withheld baseline `SELL` orders, waiting 1–3 turns for an expected town shop absorption tick.
   - Holding inventory deprived the agent of immediate liquid cash at critical daily transition turns ($t \equiv 0 \pmod{24}$). As a result, the agent was unable to afford seed planting schedules, leaving agricultural land unplanted for full cycles.
2. **Shed Blockage and Inventory Saturation**:
   - Delaying sales rapidly caused shed inventory to accumulate near capacity.
   - With the shed full, workers were unable to drop harvested crops, halting harvesting and causing standing crops to decay or remain unharvested.
3. **Market Price Slippage on Delayed Dumping**:
   - When the delayed inventory was finally liquidated, the large lump-sum volume exceeded the town shop's single-turn absorption depth, causing intra-turn sequential price collapse.
   - The microscopic price bump anticipated by the signal was completely erased by the market's price elasticity penalty.

---

## 4. Scientific Conclusion & Governance Action

1. `TOWN_CYCLE` is **FAILED**. It produces consistent, statistically significant, catastrophic losses (-$36,655 / seed, $p=0.0108$).
2. `TOWN_CYCLE` is **permanently quarantined** from `AEC_ROBUST_QUALIFIED`.
3. Per Part XXVI, stop conditions are met: the mechanism is proven harmful and must not receive further live qualification trials.
