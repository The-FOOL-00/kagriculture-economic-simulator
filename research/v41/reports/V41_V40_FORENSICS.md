# V41 Forensics: Root-Cause Deconstruction of V40 Macro Action Failures

**Document ID:** `research/v41/reports/V41_V40_FORENSICS.md`  
**Date:** 2026-09-25  
**Repository:** `Kagriculture`  
**Mission:** Provide an exhaustive, mechanically verifiable forensic explanation of why V40 suffered 28 casualties out of 40 tournament matches (-$12,416 mean paired cash delta) despite 97.7% behavioral cloning accuracy and active PPO exploration.

---

## 1. Executive Forensic Summary

In V40, an RL policy was trained over a 16-action discrete macro space. While FastKagricultureSim achieved 100% bit-for-bit parity and high throughput (470 SPS), the deployed interface between the RL macro action and the underlying execution chassis was completely uncoupled:

```text
RL Macro Action Proposal
          │
          ▼
Direct State Mutation (Inject / Filter Market Orders)
          │
          ▼
Rigid Pre-Computed Chore Tape Player (A7 / V3 Chassis)
          │
          ▼
Catastrophic Desynchronization Cascade (Missing Workers, Idle Land, Bounced Orders, Dead Crops)
```

The incumbent baseline (A7 / V35) is **not an adaptive reactive planner**; it is fundamentally a **719-step pre-computed tape replay engine** wrapped with small local reactive guards (`hand_align`, `weed_repair`, `budget_guard`). Every worker movement, waypoint, planting, watering, and harvesting operation is strictly scheduled under the immutable assumption of exact land quadrants, worker headcounts, seed inventories, and cash flows.

Mutating resource state without regenerating the underlying movement and chore plan invalidates the chassis's core assumptions, leading directly to the -$12,416 cash destruction observed in V40.

---

## 2. Answers to the 13 Mandated Forensic Questions

### 1. Exactly which V40 macro actions caused casualties?
Empirical ablation on clean DEV seed 249635 against `E8_DMITRII` demonstrates the exact loss attribution:
- **Action 4 (`FREEZE_HIRING`):** Caused a **-$11,466** cash collapse.
- **Action 1 (`EXPAND_LAND_NOW`):** Caused an **-$8,615** cash collapse.
- **Action 15 (`AGGRESSIVE_REINVEST`):** Caused a **-$787** cash collapse.
- **Action 6 (`LIVESTOCK_SHEEP`):** Caused a **-$567** cash collapse.
- **Action 5 (`LIVESTOCK_COW`):** Caused a **-$467** cash collapse.
- **Action 7 (`CROP_FOCUS_MELON`):** Caused a **-$320** cash collapse.
- **Action 8 (`CROP_FOCUS_CARROT`):** Caused a **-$120** cash collapse.

In tournament play, whenever the RL policy or BC policy deviated from `BASELINE_EXPERT` (even with 97.7% imitation fidelity), firing `FREEZE_HIRING` or `EXPAND_LAND_NOW` guaranteed an immediate casualty against top deterministic baselines (`E2_A7`, `E8_DMITRII`, `E0_V3`).

### 2. Which macro actions modify land?
- **Action 1 (`EXPAND_LAND_NOW`):** Enqueues `["BUY_LAND"]` ahead of the tape's scheduled quadrant unlock.
- **Action 2 (`DEFER_EXPANSION`):** Filters out `["BUY_LAND"]` from the tape's market queue.

### 3. Which modify workers?
- **Action 3 (`HIRE_WORKER_NOW`):** Enqueues `["HIRE"]` on step `% 24 == 0` when unbudgeted.
- **Action 4 (`FREEZE_HIRING`):** Filters out `["HIRE"]` when the tape scheduled a worker acquisition.

### 4. Which modify production allocation?
- **Action 5 (`LIVESTOCK_COW`):** Buys Cow ($400) without pasture or feeding chore support.
- **Action 6 (`LIVESTOCK_SHEEP`):** Buys Sheep ($500) without pasture or shearing chore support.
- **Action 7 (`CROP_FOCUS_MELON`):** Buys Melon seeds ($80/seed) that are never planted by the wheat-focused chore tape.
- **Action 8 (`CROP_FOCUS_CARROT`):** Buys Carrot seeds ($20/seed) that are never planted.
- **Action 15 (`AGGRESSIVE_REINVEST`):** Spends idle capital on seeds and cows that idle in the shed.

### 5. Which modify market behaviour?
- **Action 9 (`HARVEST_AND_CARE_PRIORITY`):** Market/prioritization flag.
- **Action 10 (`MARKET_FRONT_RUN_SELL`):** Flushes high-value inventory when spot prices peak.
- **Action 11 (`MARKET_ACCUMULATE_HOLD`):** Suppresses selling of depressed goods.
- **Action 12 (`EARLY_SHED_LIQUIDATION`):** Flushes shed inventory at mid-late game.
- **Action 13 (`TERMINAL_FULL_LIQUIDATION`):** Flushes all marketable commodities at endgame.
- **Action 14 (`PRESERVE_LIQUIDITY_BUFFER`):** Removes speculative purchases to safeguard cash buffer.

### 6. Which interventions desynchronize A7?
Any intervention that changes **land ownership**, **worker headcount**, or **pre-allocated working capital**:
- `FREEZE_HIRING` desynchronizes worker indexing: the tape expects $W$ hands, but only $W-1$ exist. `_hand_align` truncates the command list, discarding all chores assigned to hand $W$.
- `HIRE_WORKER_NOW` desynchronizes worker assignments: a new worker is created for whom the tape has no instructions; `_hand_align` pads with `["PASS"]`, creating a permanently idle worker whose daily Fibonacci wage drains farm capital.
- `EXPAND_LAND_NOW` desynchronizes quadrant pricing and cash reserves: buying early makes subsequent scheduled quadrant purchases cost double ($2,000 instead of $1,000; $4,000 instead of $2,000). The route's budget guard fails, bouncing critical seed and animal purchases.
- `LIVESTOCK_COW/SHEEP` and `CROP_FOCUS_MELON/CARROT` desynchronize capital allocation: cash is converted into physical seeds/animals that the tape is not programmed to plant, feed, or harvest.

### 7. At what exact state transitions does desynchronization begin?
- For `FREEZE_HIRING`: Exactly at the hour the hire was scheduled (e.g. Step 240 / Day 10). The next morning (Step 241), the field designated for the new hand is never watered. Within 24 steps, the crop starts drying; by 48 steps, weeds spawn on the unharvested plot, permanently destroying the quadrant's yield curve.
- For `EXPAND_LAND_NOW`: Immediately upon order execution. Cash drops by $1,000–$2,000, causing subsequent budget guard checks at step boundaries (`step % 72 == 0`) to trigger emergency fire-sales of unprotected stock at depressed prices.

### 8. Can A7 be safely replanned after a resource-changing intervention?
**Not within the static A7 tape replay chassis.** A7 has no dynamic pathfinding, task scheduling, or spatial assignment engine. It is a frozen 719-step action tape.  
However, the repository contains **`aec` (Adaptive Execution Compiler)** with `EventTriggeredReplanner`, `TrajectoryReconnect`, and `TacticalPlanner`, which can dynamically regenerate valid routes and worker waypoint trajectories from any arbitrary state.

### 9. Which interventions can be applied without any replan?
**Pure inventory and market liquidation actions:**
- `TERMINAL_FULL_LIQUIDATION` (Steps 690–718)
- `MARKET_FRONT_RUN_SELL` (conditional on held inventory)
- `EARLY_SHED_LIQUIDATION` (conditional on shed capacity)
- `DEFER_EXPANSION` (only if done cleanly without budget guard cascading)
- `PRESERVE_LIQUIDITY_BUFFER` (canceling unexecuted speculative orders)

These actions touch only market order buffers and already-harvested goods in the shed. They do not alter worker coordinates, tile statuses, or upcoming crop maintenance cycles.

### 10. Which interventions require replan?
- Acquiring new land (`BUY_LAND`)
- Acquiring new labor (`HIRE`)
- Changing crop species (planting `MELON` or `CARROT` instead of `WHEAT`)
- Introducing livestock (`COW`, `SHEEP`, `GOOSE`)
- Reassigning workers to emergency harvest or weeding

### 11. Which interventions should be permanently prohibited?
- **Uncontrolled `FREEZE_HIRING` without dynamic reallocation:** Freezing labor while executing a multi-worker chore schedule is guaranteed suicide.
- **Uncoordinated `BUY_ANIMAL` or `BUY_SEED` without worker dispatch:** Buying assets that workers are not routed to cultivate or tend is pure capital burning.
- **Unrestricted coarse macro actions:** Macro actions that blindly strip or add raw market strings without verifying downstream execution invariants.

### 12. Which V40 changes were economically useful but mechanically unsafe?
- **Mid-game land expansion:** When liquid cash exceeds $12,000, acquiring additional land has high theoretical return (demonstrated +$11,000 in solo counterfactuals), but in V40 it desynchronized the budget guard and left tiles uncultivated.
- **Crop diversification into melons:** Melons have high profit margins ($80 seed -> $250+ harvest), but without a melon-aware chore planner, the seeds sat in the shed.

### 13. Which V40 decisions can be converted into safe atomic interventions?
1. **Dynamic Liquidation Policy:** Generalizing V39's Step 694 rule into a state-aware liquidation operator that monitors market price momentum, competitor inventory dumps, and shed perishability.
2. **Selective Market Order Insertion:** Injecting atomic sell orders only for items already deposited in the shed, without interfering with base chore queues.
3. **Counterfactual-Gated Deviations:** Running short-horizon simulation rollouts before executing any strategic departure to verify that the proposed intervention dominates the baseline without causing downstream casualties.

---

## 3. Forensic Conclusion

V40 failed not because RL cannot learn economic principles, but because **macro actions were treated as direct environmental mutations rather than proposals to a verified, state-aware controller**.

The V41 architecture directly rectifies this:
1. All physical interventions require formal safety verification.
2. Market-safe interventions are isolated into atomic, non-destructive primitives.
3. Every strategic proposal must pass an exact counterfactual gate before execution.
4. If a proposal fails validation, the system cleanly defaults to the zero-casualty incumbent (V35/V39).
