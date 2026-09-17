# AEC Counterfactual Fidelity Audit & Semantic Forensic Analysis

**Audit Identifier:** `AUDIT-AEC-CF-001`  
**Date:** 2026-09-17  
**Triggering Event:** Falsification of `EXP-AEC-002` (Mean paired terminal margin delta -$0.92, 95% lower bound -$2.07)  
**Governance Scope:** Pre-development forensic audit of `aec/counterfactual/`, `aec/ir/`, `aec/patches/`, `aec/opportunities/`, and simulator integration.  
**Holdout Status:** Seeds `340050–340199` **100% VIRGIN & UNTOUCHED**.

---

## 1. Executive Summary

This audit establishes the exact causal and microeconomic root causes behind the failure of `FRONTLOAD_ORDERS` in EXP-AEC-002. Through independent step-by-step forensic reconstruction of historical tournament traces on seeds `340214` and `340224`, we identified four fundamental architectural divergence points between the Real Game Engine (`kagsim` / `kg_env_dump.py`) and the AEC Counterfactual Simulator (`aec/counterfactual/simulator.py`):

1. **Intra-Basket Endogenous Price Impact Blindness:** In multi-order baskets containing both BUY and SELL orders for the same commodity, buying first increases the clearing price received by subsequent sells. Frontloading sells forfeits this demand-induced price elevation.
2. **Opponent Model Phantom Dumping:** The `OpponentPressureModel` in `aec/counterfactual/opponent_pressure.py` synthesized speculative 66-unit wheat dumping orders at offset 0 whenever heuristic sale pressure crossed 0.5. In real games, the opponent (Frozen V3) was not dumping, but buying concurrently. This caused the simulator to predict a false $+\$34.00$ front-running profit where the real engine lost $-\$9.00$.
3. **Continuation Invalidation by Worker Freezing:** When candidate patches mutated worker routes (e.g. `LOCAL_WEED_DIG`), the simulator detected a position discrepancy against the static V3 backbone route tape and forced all subsequent worker commands to `["PASS"]`, artificially guaranteeing economic failure for any route-altering patch.
4. **Multi-Day Lifecycle Omissions:** Multi-step rollouts applied plant decay but failed to simulate daily crop growth, animal production yields, or end-of-day wheat feeding at day boundaries.

---

## 2. Forensic Reconstruction: Seeds 340214 and 340224

Reconstruction was performed on historical EXP-AEC-002 traces without re-executing prospective matches or touching protected holdouts.

### 2.1 Seed 340224 Detailed Trace

- **Initial State at Step 574:**
  - Liquid Cash: $\$80,830.00$
  - Market Wheat Inventory: $9,708$ units (Market Price: $\$42.00$)
  - Farm Shed Wheat: $5$ units, Fertilizer: $1$ unit
- **Turn 575 Baseline Market Queue:**
  $$Q_{\text{base}} = [[\text{BUY\_PRODUCT}, \text{WHEAT}, 16], [\text{SELL}, \text{WHEAT}, 2], [\text{BUY\_PRODUCT}, \text{FERTILIZER}, 11]]$$
- **Turn 575 Candidate Market Queue (Frontloaded):**
  $$Q_{\text{cand}} = [[\text{SELL}, \text{WHEAT}, 2], [\text{BUY\_PRODUCT}, \text{WHEAT}, 16], [\text{BUY\_PRODUCT}, \text{FERTILIZER}, 11]]$$
- **Real Opponent Market Queue (Frozen V3 Mirror):**
  $$Q_{\text{opp}} = [[\text{BUY\_PRODUCT}, \text{WHEAT}, 16], [\text{SELL}, \text{WHEAT}, 2], [\text{BUY\_PRODUCT}, \text{FERTILIZER}, 11]]$$

#### Step-by-Step Execution Dynamics at Turn 575:
1. **Under Baseline Execution:**
   - In Slot 0: Both Player 0 and Opponent submit `BUY_PRODUCT WHEAT 16`.
   - Both players buy wheat in lockstep, consuming 32 units total from the market. Inventory drops from $9,708 \to 9,676$. Price rises from $\$42 \to \$44$.
   - In Slot 1: Both players submit `SELL WHEAT 2`.
   - Both sell at the newly elevated price of $\$44.00$, capturing maximum revenue.
   - Net Cash Delta for Player 0: $-\$773.00$.
2. **Under Frontloaded Execution (AEC Candidate):**
   - In Slot 0: Player 0 submits `SELL WHEAT 2`, while Opponent submits `BUY_PRODUCT WHEAT 16`.
   - Player 0 sells its 2 units against the Opponent's first 2 buy units. Market inventory remains flat ($9,708$). Player 0 sells at the uninflated price of $\$42.00$ (receiving only $\$84$ instead of $\$88$).
   - Opponent continues buying the remaining 14 units in Slot 0, driving the price up to $\$43.00$.
   - In Slot 1: Player 0 submits `BUY_PRODUCT WHEAT 16`, while Opponent submits `SELL WHEAT 2`.
   - Now Player 0 buys wheat after the Opponent has already shifted the price up, paying an inflated price. Meanwhile, the Opponent sells its 2 units at the inflated price!
   - Net Cash Delta for Player 0: $-\$782.00$.
3. **Realized Economic Impact at Step 575:**
   $$\Delta \text{Cash} = -\$782.00 - (-\$773.00) = -\$9.00$$
   Player 0 surrendered $\$9.00$ in margin directly to the Opponent on turn 575 alone!
4. **Repeat at Step 647 on Seed 340224:**
   - The identical mechanism occurred at Step 647, costing an additional $-\$8.00$ in net cash margin.
   - Downstream compounding produced the final observed terminal loss of **$-\$31.00$** on Seed `340224`.

### 2.2 Seed 340214 Detailed Trace
- **Step 575:**
  - Player 0 had 20 wheat in shed and submitted:
    $$\text{Baseline: } [[\text{BUY}, \text{WHEAT}, 16], [\text{SELL}, \text{WHEAT}, 13], [\text{BUY}, \text{FERT}, 11]]$$
    $$\text{Candidate: } [[\text{SELL}, \text{WHEAT}, 13], [\text{BUY}, \text{WHEAT}, 16], [\text{BUY}, \text{FERT}, 11]]$$
  - Realized diff at step 575 was $\$0.00$ because the high sell volume ($13$ units) closely matched the opponent's concurrent buy volume ($16$ units), resulting in price neutralization.
- **Step 647:**
  - Player 0 submitted `BUY 15, SELL 6` vs candidate `SELL 6, BUY 15`.
  - Opponent submitted `BUY 15, SELL 6`.
  - Realized diff: **$-\$8.00$**.
  - Downstream compounding produced the final observed terminal loss of **$-\$15.00$** on Seed `340214`.

### 2.3 Why Did the Simulator Predict $+\$34.00$ and $+\$48.00$?
In `aec/counterfactual/simulator.py`:
```python
opp_market = opp_model.generate_simulated_opponent_market(econ_state.step, offset)
execute_market_lockstep(rollout, action.get("market", []), opp_market)
```
In `aec/counterfactual/opponent_pressure.py`:
```python
if pressure >= 0.5 and forecast_qty >= 1.0:
    if offset == 0:
        sell_qty = max(1, min(100, int(forecast_qty)))
        orders.append(["SELL", item, sell_qty])
```
Because the opponent had harvested wheat in earlier turns, `OpponentState` showed high historical wheat production, setting `pressure >= 0.5` and `forecast_qty = 66.0`.
The simulator synthesized an artificial rival order: `['SELL', 'WHEAT', 66]` at offset 0.
- If Player 0 delayed selling to Slot 1 (Baseline), the 66-unit rival dump was simulated as executing in Slot 0, severely depressing the simulated wheat price before Player 0 sold.
- If Player 0 sold in Slot 0 (Candidate), Player 0's sell was simulated as front-running the 66-unit dump.
- **Result:** The simulator hallucinated a massive $+\$34.00$ to $+\$48.00$ advantage that existed only in the simulation's fictitious rival model!

---

## 3. Systematic Audit of Opportunity Families

| Family | Status | Primary Semantic Weakness | Continuation Failure Mode |
|---|---|---|---|
| `FRONTLOAD_ORDERS` | **RETIRED / FALSIFIED** | Unconditional reordering ignores endogenous intra-basket price impact and concurrent rival trading. | N/A (1-step market action). |
| `LOCAL_WEED_DIG` | **QUARANTINED** | Worker moves or digs on step 0, desynchronizing from pre-recorded V3 backbone route tape. | Simulator detects spatial divergence at step 1+ and freezes worker with `PASS` for all subsequent turns. |
| `DYNAMIC_SHADOW_HARVEST` | **QUARANTINED** | Rerouting idle worker to harvest mature crop invalidates future waypoint sequence. | Simulator freezes worker upon divergence; ignores downstream cargo drop-off logistics. |
| `CARGO_FERRY_PRIORITY` | **QUARANTINED** | Diverting worker to shed earlier alters inventory arrival timing and depot route. | Worker frozen at next step; shed delivery and subsequent field return not replanned. |
| `OPPONENT_PREEMPT_SELL` | **QUARANTINED** | Relies on speculative `OpponentPressureModel` dump timing heuristics. | High probability of selling into an unthreatened market, depressing own future harvest prices. |
| `EMERGENCY_FEED_PURCHASE` | **QUARANTINED** | Evaluates wheat feed purchase without checking animal feed consumption lifecycle. | Multi-day rollout does not execute `_end_of_day` animal starvation or yield deduction. |
| `TERMINAL_HARVEST_SWEEP` | **QUARANTINED** | Harvests crops in steps 696–717 without evaluating whether worker can reach shed before step 718. | Cargo left in worker hands at game end produces $\$0.00$ revenue (terminal destruction). |
| `TOWN_CYCLE` | **QUARANTINED** | Speculates on town shop absorption ticks without modeling multi-player supply saturation. | Price rebounds may be preempted by concurrent rival deliveries. |
| `TERMINAL_LIQUIDATION` | **VERIFIED DEFENSE** | Liquidates shed at step 718 under exact 1-step terminal conversion rules. | Valid; 1-step horizon matches game termination rules exactly. |
| `PHASE_SHUTDOWN` | **VERIFIED DEFENSE** | Halts unviable seed planting past maturation cutoff steps. | Valid; eliminates dead-capital expenditure with zero downstream dependency divergence. |

---

## 4. Architectural Remedies & Requirements

To achieve true causal fidelity, the following architectural improvements must be implemented:

1. **Explicit Market Order Dependency Graph (`aec/ir/dependency_graph.py`):**
   - Represent action baskets as directed acyclic graphs (DAGs) with explicit causal edges:
     - `SAME_ASSET_MARKET_COUPLING`: Direct price feedback between BUY and SELL of the same asset.
     - `CASH_COUPLING`: Cash consumption in order $i$ affecting feasibility of order $j$.
     - `SHED_CAPACITY_COUPLING`: Shed inventory constraints.
2. **Deterministic Conservative Opponent Modeling:**
   - Eliminate speculative phantom dumps.
   - Support `CONSERVATIVE_NEUTRAL` (isolated clearing) and `BASELINE_MIRROR` (symmetric baseline continuation).
3. **Adaptive Local Replanning (Resolving Continuation Invalidation):**
   - When a worker's route is altered, compute a local reconnect path back to the planned backbone waypoint instead of freezing the worker with `PASS`.
   - Preserve unaffected workers and backbone macro plans intact.
4. **Multi-Day Engine Lifecycle Fidelity:**
   - Integrate daily crop growth and animal production hooks when rollout horizons cross day boundaries.
5. **Strict Counterfactual Fidelity Certification:**
   - Add `COUNTERFACTUAL_FIDELITY: VERIFIED / PARTIAL / UNKNOWN / FAILED` to safety certificates.
   - Require `VERIFIED` before committing any economically consequential patch.
