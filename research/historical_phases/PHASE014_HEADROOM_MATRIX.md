# PHASE 014: AEC HEADROOM & CANDIDATE-GAP MATRIX

**Phase**: 014 — AEC Economic Headroom Audit  
**Date**: September 19, 2026  
**Chassis Freeze Hash**: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`  
**Empirical Control**: Live Foundation (`V3` + `DEPENDENCY_AWARE_MARKET_TIMING` + `TERMINAL_LIQUIDATION` + `PHASE_SHUTDOWN`)  

---

## 1. Candidate-Gap Matrix (§14)

The Candidate-Gap Matrix details representative oracle opportunities, whether existing AEC mechanisms detect or represent them, exact simulation outcomes, safety gate verdicts, and the missing architecture layer:

| Oracle Opportunity | Current Mechanism | Detected? | Represented? | Patchable? | Exact Sim? | Safety? | Final Decision | Missing Layer |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| **Tranche Shed Liquidation** (Sell 10 uncommitted Strawberries during +25% price window) | None (`MARKET_TIMING` only reorders existing orders) | NO | NO | YES | YES | PASS | ABSTAIN (No Opps) | **DETECTOR** (Shed asset holding cost trigger missing) |
| **Terminal Runway Clearance** (Sell 100% held stock at step 712) | `TERMINAL_LIQUIDATION` | YES | PARTIAL | YES | YES | PASS | COMMIT / ABSTAIN | **REPRESENTATION** (Only dumps top asset; fails multi-asset dump) |
| **Preemptive Sell Ahead of Rival** (Clear market depth 1 tick before rival arrives at shop) | `OPPONENT_PREEMPT_SELL` (Quarantined) | NO | NO | YES | YES | PASS | ABSTAIN (Quarantined) | **DETECTOR / META** (Continuous pressure detector does not emit order) |
| **Helper Produce Sweep** (Helper collects dropped crop while Lead harvests) | `CARGO_FERRY` (Quarantined) | NO | NO | YES | YES | PASS | ABSTAIN (Quarantined) | **DETECTOR** (Multi-worker cargo handoff unrepresented) |
| **Adjacent Crop Harvest Swap** (Execute immediate harvest at (r,c) instead of transit detour) | `DYNAMIC_SHADOW_HARVEST` (Quarantined) | NO | NO | YES | YES | PASS | ABSTAIN (Quarantined) | **DETECTOR** (Event detector blind to worker spatial detour cost) |
| **Delayed Sell Before Town Refresh** (Hold inventory 2 steps for step % 72 town demand spike) | `TOWN_CYCLE` (Quarantined) | NO | NO | YES | YES | PASS | ABSTAIN (Quarantined) | **DETECTOR** (Town consumption tick unrepresented in market IR) |
| **Solvency Seed Frontload** (Buy 5 seeds before step 23 to avoid day-boundary cash squeeze) | None | NO | NO | YES | YES | PASS | ABSTAIN (No Opps) | **DETECTOR** (Liquidity frontload opportunity detector missing) |
| **Endgame Transit Truncation** (Abort step 705 return transit to harvest adjacent ripe field) | None | NO | NO | YES | YES | PASS | ABSTAIN (No Opps) | **REPRESENTATION** (No endgame route truncation candidate generator) |
| **Commodity Arbitrage Purchase** (Procure raw inputs from shop for conversion) | `SHOP_ARBITRAGE` (Quarantined) | YES | DEFECTIVE | YES | YES | FAIL | SAFETY_REJECT | **ECONOMIC_EVAL** (Working capital starvation) |
| **Livestock Feed Rescue** (Emergency WHEAT buy when consecutive unfed == 1) | `EMERGENCY_FEED_PURCHASE` (Dormant) | YES | YES | YES | YES | PASS | ABSTAIN (Unneeded) | **OPPORTUNITY_GATING** (Baseline maintains safe feed) |

---

## 2. Objective Headroom Scorecard (§30)

The Priority Score is calculated objectively as:
$$\text{Priority Score} = \text{States Count} \times \text{Mean Headroom (USD)} \times \text{Representability Factor}$$

| Gap Class | States | Positive Headroom (USD) | Mean Headroom (USD) | Current AEC Coverage | Representability | Priority Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Detector** | 8,066 | $1,595,000 | $197.74 | 0.00% | 0.90 | **1,435,500** |
| **Representation** | 2,185 | $421,705 | $193.00 | 0.00% | 0.80 | **337,360** |
| **Opponent** | 373 | $58,452 | $156.71 | 0.00% | 0.50 | **29,226** |
| **Composition** | 368 | $29,366 | $79.80 | 0.00% | 0.60 | **17,619** |
| **Economic Evaluation** | 14 | $322 | $23.00 | 0.00% | 0.85 | **274** |
| **Horizon** | 20 | $212 | $10.60 | 0.00% | 0.65 | **138** |
| **Patch** | 2 | $70 | $35.00 | 0.00% | 0.75 | **53** |
| **Reconnect** | 0 | $0 | $0.00 | 100.00% | 0.70 | **0** |
| **Macro** | 0 | $0 | $0.00 | 100.00% | 0.20 | **0** |

### Scorecard Takeaway:
- **Rank 1: Detector Gap** dominates the entire landscape by a factor of >4x over all other classes combined.
- **Rank 2: Representation Gap** represents the second primary barrier, where detected opportunities cannot formulate action tranches.
- **Rank 3: Opponent Preemption** holds significant secondary potential under rival delivery pressure.
- **Ranks 4-9**: Reconnect, Patch formulation, Horizon, and Macro policies are **NOT** the bottleneck. Trajectory compilation and simulation infrastructure are already highly performant.
