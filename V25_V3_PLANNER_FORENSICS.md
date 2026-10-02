# V25 — V3 Planner Forensics & Failure Mechanism Decomposition

## Executive Architectural Summary

V3 (`submission_Vj_kc_v3.tar.gz`) is a layered hybrid architecture consisting of:
1. **The Dmitrii / yhay81 Precomputed Base Tape Engine**: At its core (`_R108_DATA`), V3 contains precomputed action tapes (`_ROUTES`) indexed by initial shop-pair unlock patterns (`_R108_SHOP_ROUTES`).
2. **The 26-Wrapper Override Chassis (`parent_v43.py`)**: A chain of 26 sequentially nested wrapper functions that intercept, overwrite, or splice specific game phases (EXP-149, EXP-154, EXP-155, EXP-167, EXP-182, EXP-193, EXP-216, EXP-260).
3. **The Frontloading & Horizon Extension Shell (`main.py`)**: Extends pre-sale reservation horizon to 24 turns (`_R37_HORIZONS`) and reorders market execution queues.

---

## Systematic Decomposition of V3 Planning Mechanisms

### 1. Opening Capital Allocation & Purchases
- **Input State**: `step == 0`, `observation['town']['unlocked_shops']`, `farms[player]['money'] == 2500`.
- **Decision Rule**:
  - Turn 0: Hardcoded probe sequence `[['BUY_PRODUCT', 'WHEAT', 5], ['BUY_PRODUCT', 'WHEAT', 10], ['SELL', 'WHEAT', 60]]`.
  - Turn 1: Bulk order `['SELL', 'WHEAT', 13], ['BUY_PRODUCT', 'WHEAT', 5], ['HIRE'] * 5, ['BUY_ANIMAL', 'COW', 2], ['BUY_ANIMAL', 'SHEEP', 2]`.
- **Downstream Assumptions**: Assumes market will absorb wheat sales at profitable margin; commits initial $2,500 into 5 farmhands and 4 livestock units immediately.
- **Reversibility**: **Irreversible**. Capital converted to farmhands and livestock cannot be liquidated.
- **Coupling Impact**: Locks the economy into high initial labor wages ($50/worker/day) from Day 1.

---

### 2. Labor Dispatch & The Root of Worker Idleness
- **Input State**: Positions of 5 farmhands, tile state grid, private inventories.
- **Decision Rule**:
  - Functions `_proposals` and `_r53_labor_assignment` evaluate prospective task bundles:
    ```python
    bundles = []
    for tile in farm['tiles']:
        # only HARVEST and COLLECT_FERTILIZER are bundled!
        if tile.get('yield_units', 0) > 0: ...
        if tile.get('fertilizer_available'): ...
    ```
  - Route compilation:
    ```python
    route = _walk(cursor, xy) + ops + _return(cursor)
    # CRUCIAL BOTTLENECK:
    route += [['PASS']] * (horizon - offset - len(route))
    ```
- **Why Idle `['PASS']` Occurs**:
  1. **Bundle Exclusivity**: V3's proposal engine *only* schedules routes for `HARVEST` and `COLLECT_FERTILIZER`. Daily maintenance tasks (`WATER`, `FEED`, `CARE`) are handled by separate, rigid sub-handlers that fire only under specific conditions.
  2. **Horizon Padding**: Whenever a farmhand finishes its harvest route before the 24-step horizon elapses, V3 pads the entire remainder of the schedule with `['PASS']`.
  3. **No Secondary Dispatch**: There is zero opportunistic fallback logic to check if the idle worker is standing next to an unwatered plant or hungry animal.
- **Coupling Impact**: Produces 38.4% idle worker turns in early game, directly causing delayed crop watering and forfeited compounding.

---

### 3. Livestock Sizing & Pasture Spatial Topology
- **Input State**: Tile map, animal counts, cash runway.
- **Decision Rule**:
  - Livestock purchases are governed by EXP-167 ("Two Coins, One Sheep") and EXP-216.
  - V3 limits Cow purchases to ~6–7 units.
  - Pastures are built on first available tiles without proximity clustering constraints.
- **Why Top Agents Outperform V3**:
  - Top agents (Cluster A: DSM, Vadim Vasilenko) purchase **10–13 Cows** on Days 0–2 and place pastures in an immediate 1-tile perimeter around the farmhouse.
  - V3's dispersed pastures force workers to spend 3–4 transit turns traveling to feed and care for each animal, whereas elite agents complete feeding in 1 transit step.

---

### 4. Crop Selection & Velocity
- **Input State**: Day number, seed inventory, plot availability.
- **Decision Rule**:
  - Wheat is primary volume crop.
  - Tomato investment is strictly restricted to Days 18–22 (EXP-155).
  - Secondary crop defaults to Strawberry.
- **Why Top Agents Outperform V3**:
  - Top agents heavily cultivate **Carrot** (33–85 units). Carrots mature in 3 days with low water sensitivity, generating rapid reinvestable cash flow by Day 5–10 ($28k–$42k bank).
  - V3's Strawberry choices tie up capital and labor for 5–7 days per cycle with high drought penalties.

---

### 5. Multi-Turn Planning Invariants & Why Post-Hoc Patching Fails
- **State Coupling**:
  - V3 maintains internal route cursors (`_last_called_step`, `chassis.routes`, `_in_flight_patch`).
  - When an external heuristic intercepts a worker action (e.g. replacing `['PASS']` with `['WATER']` or movement):
    1. The simulator moves the worker or changes its energy/state.
    2. On step $t+1$, V3's internal planner expects the worker to be at position $(x, y)$, but the worker is at $(x', y')$.
    3. The next planned step in the route tape becomes physically illegal (e.g. moving through a wall or harvesting an empty tile).
    4. V3 catches the error and falls back to full `['PASS']` loops or crashes.
- **Verdict**: **Post-hoc action mutation is fundamentally incompatible with V3's coupled multi-turn planner.**
- **Requirement for V25**: Planning changes must occur **at the macro objective level BEFORE routes are compiled**.
