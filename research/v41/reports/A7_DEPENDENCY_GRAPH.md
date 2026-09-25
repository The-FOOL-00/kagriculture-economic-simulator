# A7 / V35 Stateful Chore Chassis Dependency Graph & Invariant Analysis

**Document ID:** `research/v41/reports/A7_DEPENDENCY_GRAPH.md`  
**Date:** 2026-09-25  
**Repository:** `Kagriculture`  
**Scope:** Reverse-engineering the mechanical state machine, internal invariant assumptions, and causal failure cascades of the incumbent A7 / V35 controller.

---

## 1. Architectural Overview of the A7 Chore Chassis

The A7 controller (and its V35 opening variant) is a hybrid control system consisting of:
1. **The Core Tape:** A pre-computed, step-by-step action schedule spanning 719 turns for the farmer and all hired farm hands.
2. **The Reactive Layer Shell:** A suite of procedural filters wrapped around the tape:
   - `_hand_align`: Adapts the tape's worker list to the current physical hand count.
   - `_weed_repair`: Converts obstructed moves or actions on weed tiles into `DIG` operations, queueing the displaced action.
   - `_budget_guard`: Audits projected purchase costs at 72-turn block boundaries (`step % 72 == 0`) and injects market sales to fund scheduled expenses.
   - `_room_guard`: Enforces shed inventory caps at hour 23 (`step % 24 == 23`).
   - `_clamp_sells`: Restricts market `SELL` orders to verified shed stock.
   - `_sell_lead`: Advances planned sales by one turn when town consumption allows.
   - `_front_run`: Detects scheduled opponent sales and leads them.
   - `_terminal_liquidation`: Unconditionally flushes all marketable goods at step 718.

---

## 2. Formal Causal Dependency Graph

```mermaid
graph TD
    subgraph LAND ["LAND (Quadrants & Geometry)"]
        L1[Unlocked Quadrants: 1..4]
        L2[Tile Grid Status: Empty / Locked / Crop / Pasture]
        L3[Worker Spatial Reachability & Walkway Topology]
    end

    subgraph WORKERS ["LABOR & WORKER ALLOCATION"]
        W1[Headcount N: Farmer + Hands]
        W2[Worker Waypoints & Trajectory Queues]
        W3[Spatial Assignments: Field 1..K]
        W4[Daily Fibonacci Wage Burden: Sum Fib(hires)]
    end

    subgraph CROPS ["CROP CYCLE & CHORES"]
        C1[Planting Timing: Seed Availability in Hand]
        C2[Daily Watering Invariant: Watered within 24h]
        C3[Weed Suppression: Zero Unweeded Plots]
        C4[Harvest Execution: Emptying Mature Yield to Cargo]
        C5[Shed Deposit: Ferrying Cargo to Shed]
    end

    subgraph ANIMALS ["LIVESTOCK PRODUCTION"]
        A1[Structure Precondition: Coop / Pasture Built]
        A2[Daily Feeding Invariant: 1 Wheat per Animal / Day]
        A3[Daily Care / Shearing / Milking Chores]
        A4[Perishable Yield: Milk / Wool Generation]
    end

    subgraph MARKET ["MARKET & LIQUIDITY"]
        M1[Working Capital Reserve: >= $125 - $200 Buffer]
        M2[72-Step Budget Guard: Suffix Sum Funding]
        M3[Commodity Spot Prices: Wheat, Milk, Wool, Strawberry]
        M4[Terminal Inventory Realization: Steps 690 - 718]
    end

    L1 --> L2
    L2 --> L3
    L3 --> W2
    W1 --> W2
    W1 --> W4
    W4 --> M1

    W2 --> C1
    C1 --> C2
    C2 --> C4
    C4 --> C5
    C5 --> M4

    W2 --> A2
    A2 --> A3
    A3 --> A4
    A4 --> C5

    M1 --> M2
    M2 --> W1
    M2 --> L1
    M4 --> M1
```

---

## 3. Deep Invariant Analysis Across Subsystems

### A. LAND Invariants
1. **Quadrant Unlock Monotonicity:** Quadrants cost $1,000, $2,000, and $4,000 sequentially. The tape hard-codes the exact steps at which cash must be available to unlock quadrants.
2. **Fixed Coordinate Mapping:** The tape encodes unit actions using relative Cartesian directions (`NORTH`, `SOUTH`, `EAST`, `WEST`). If a unit's position is shifted by 1 tile due to an obstacle or displaced action, all subsequent directional moves navigate to the wrong destination until realigned.

### B. WORKER & LABOR Invariants
1. **Headcount-to-Chore Bijection:** The tape maps `hands[k]` to a specific sub-region of the farm. Worker 0 (farmer) handles central logistics and initial planting; Hand 1 handles quadrant 1 watering; Hand 2 handles quadrant 2 watering, etc.
2. **The `_hand_align` Hazard:**
   - If actual hands $< K$: `_hand_align` truncates the command vector:
     ```python
     action["hands"] = hands[:expected]
     ```
     The chores assigned to missing workers vanish entirely.
   - If actual hands $> K$: `_hand_align` pads extra workers with `["PASS"]`:
     ```python
     hands.extend([["PASS"] for _ in range(expected - len(hands))])
     ```
     The extra worker permanently passes, contributing zero labor while incurring exponential daily wage drains.

### C. CROP Invariants
1. **The 24-Hour Watering Rule:** A planted crop must be watered every calendar day. Missing a single watering cycle delays maturation by 24 turns or causes crop withering.
2. **The Weed Colonization Cascade:** If a crop tile is neglected or an unplanted plot is left empty, weeds germinate. Weeds block subsequent `PLANT` and `BUILD` operations, forcing `_weed_repair` to divert the worker into `DIG` routines, disrupting the tick-exact timing of the remaining chore chain.

### D. ANIMAL & LIVESTOCK Invariants
1. **Feed Security Precondition:** Dairy cows and sheep consume 1 unit of wheat daily. If wheat inventory is zero, animals starve, production halts, and health declines.
2. **Structure Requirement:** Animals cannot be placed on raw land; they require a dedicated `BUILD_PASTURE` or `BUILD_COOP` tile action performed beforehand.

### E. MARKET & CAPITAL Invariants
1. **The 72-Turn Budget Invariant:** At `step % 72 == 0`, `_budget_guard` calculates:
   $$\text{Shortfall} = \text{Budget}(\text{step} \dots \text{step}+72) - \text{Liquid Cash} - \text{Planned Suffix Sells}$$
   If $\text{Shortfall} > 0$, it forcibly dumps unprotected shed inventory at the current spot price. An unexpected capital drain triggers an emergency liquidation of raw commodities at suboptimal prices.

---

## 4. State Mutation Impact Matrix

| State Mutation | Affected Systems | Invariant Broken | Consequence | Replan Required? |
| :--- | :--- | :--- | :--- | :--- |
| **Buy Plot Early** | `LAND`, `MARKET` | Quadrant Cost Escalation, Cash Reserve | Budget guard shortfall, premature inventory dump, tiles idle | **YES** (full chore re-routing) |
| **Defer Plot** | `LAND`, `MARKET` | Land Availability Schedule | Workers walk into locked quadrants (`LOCKED` tile no-op) | **YES** |
| **Hire Extra Worker** | `WORKERS`, `MARKET` | Labor Allocation Bijection, Wage Budget | Worker idles on `PASS`, wage drain of $50–$300/day | **YES** (task queue assignment) |
| **Freeze / Cancel Hire** | `WORKERS`, `CROPS` | Hand Alignment, Field Maintenance | Chores truncated, crops unwatered, weeds spawn | **YES** (CRITICAL) |
| **Buy Unscheduled Animal** | `ANIMALS`, `MARKET` | Structure & Feed Security | Animal stuck in shed, $400 capital burned | **YES** |
| **Buy Unscheduled Seeds** | `CROPS`, `MARKET` | Seed Allocation, Chore Queue | Seeds sit unplanted, capital wasted | **YES** |
| **Sell Existing Shed Stock** | `MARKET` | None (if within capacity & unallocated) | Increased cash liquidity, zero physical desynchronization | **NO** (`SAFE_ATOMIC`) |
| **Adjust Sell Order Price/Time** | `MARKET` | Market Queue Slot (max 10 orders) | Changes execution priority in trade matching | **NO** (`SAFE_ATOMIC`) |

---

## 5. Architectural Implications for V41

1. **Strategic Isolation:** The RL policy must never directly mutate land, labor, or animal inventories without engaging a dynamic replanning engine.
2. **Atomic Interventions:** Market liquidation, inventory sales, and order timing do not break the physical chore state machine and can be executed as `SAFE_ATOMIC` interventions.
3. **Safe Replan Bridge:** If a physical intervention (such as land expansion) is proposed, it must pass through a `StateAwareExecutor` that synthesizes valid worker chore routes for the altered topology before the action is dispatched to the environment.
