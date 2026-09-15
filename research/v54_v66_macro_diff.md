# V54 vs V66 Source-Level Macro Differential

## Overview

- **Total Timesteps**: 719
- **Total Differing Timesteps**: 524 (72.9%)
- **First Differing Timestep**: Step 0 (Day 0, Hour 0)
- **Last Differing Timestep**: Step 718 (Day 29, Hour 22)

## Action Category Comparison

| Action Category | V54 Total Route Units | V66 Total Route Units | Difference (V66 - V54) | Timesteps with Differing Volume |
| :--- | :---: | :---: | :---: | :---: |
| **HIRE** | 290 | 290 | +0 | 0 |
| **BUY_SEED** | 243 | 249 | +6 | 183 |
| **BUY_ANIMAL** | 14 | 14 | +0 | 2 |
| **LAND** | 2 | 2 | +0 | 0 |
| **PLANT** | 243 | 243 | +0 | 0 |
| **WATER** | 1,138 | 1,172 | +34 | 37 |
| **HARVEST** | 469 | 467 | -2 | 1 |
| **FEED** | 326 | 326 | +0 | 14 |
| **CARE** | 333 | 351 | +18 | 31 |
| **MILK** | 0 | 0 | +0 | 0 |
| **WOOL** | 0 | 0 | +0 | 0 |
| **FERTILIZER** | 338 | 338 | +0 | 10 |
| **SELL** | 1,523 | 1,468 | -55 | 238 |
| **MOVE** | 3,170 | 3,473 | +303 | 201 |
| **PASS** | 882 | 514 | -368 | 238 |
| **BUY_PRODUCT** | 245 | 204 | -41 | 12 |

## Major Architectural Differences

### Route Architecture: _V56_BACKBONE_ROUTE
- **Source / File**: `Kaito Fukami / mohui666` / [`candidate_v62_composite_bakery_yarn.py`](candidate_v62_composite_bakery_yarn.py:1968, 2122)
- **Active Timesteps**: Steps 0 to 718
- **V54 Behavior**: r007-1-flow3-h2q4 offline route prior
- **V66 Behavior**: e103819410-islet-full offline route prior
- **Economic Purpose**: Higher throughput crop/livestock scheduling derived from Islet GA branch
- **Empirical Evidence**: 524 out of 719 timesteps differ in planned actions

### Wheat Procurement: Step 0 Opening Order
- **Source / File**: `mohui666` / [`candidate_v62_composite_bakery_yarn.py`](candidate_v62_composite_bakery_yarn.py:1968)
- **Active Timesteps**: Steps 0 to 1
- **V54 Behavior**: No market action at Step 0; buys 5 wheat at Step 1
- **V66 Behavior**: Submits BUY_PRODUCT WHEAT 5 at Step 0
- **Economic Purpose**: Locks in turn-0 wheat purchase price before market moves or opponent trades
- **Empirical Evidence**: r66[0]['market'] == [['BUY_PRODUCT', 'WHEAT', 5]] vs r54[0]['market'] == []

### Crop Purchases: _v60_seed_trim
- **Source / File**: `mohui666` / [`candidate_v62_composite_bakery_yarn.py`](candidate_v62_composite_bakery_yarn.py:4090)
- **Active Timesteps**: Steps 72 to 360
- **V54 Behavior**: Executes static strawberry seed buy orders regardless of remaining planting capacity
- **V66 Behavior**: Dynamically trims strawberry seed buys to min(order, remaining_plant_chores - inventory)
- **Economic Purpose**: Prevents dead capital trapped in unplanted strawberry seeds late in planting cycle
- **Empirical Evidence**: Active in V60/V62 wrapper wrapping backbone route

### Shed Overflow Prevention: _v60_shed_guard
- **Source / File**: `mohui666` / [`candidate_v62_composite_bakery_yarn.py`](candidate_v62_composite_bakery_yarn.py:4135)
- **Active Timesteps**: Steps 23 to 695
- **V54 Behavior**: No shed capacity projection at hour 23; relies on static sales
- **V66 Behavior**: Projects daily 23h shed drop and issues pre-emptive sell orders if total units > 100
- **Economic Purpose**: Prevents waste of valuable farm products when workers return to shed overnight
- **Empirical Evidence**: Checked every step where hour == 23

### Terminal Units Realization: _route_loaded_units
- **Source / File**: `mohui666` / [`candidate_v66_meta_closed_loop.py`](candidate_v66_meta_closed_loop.py:409)
- **Active Timesteps**: Steps 713 to 716
- **V54 Behavior**: Workers continue standard pathing through steps 713-718 without cargo return override
- **V66 Behavior**: Routes workers holding sellable goods back to shed on steps 713-716 based on distance
- **Economic Purpose**: Ensures all carried wool, milk, and crops reach shed before episode ends
- **Empirical Evidence**: Orders replaced with _MOVE_TOWARD shed access if distance == departure_distance

### Liquidation: _TERMINAL_MARKET
- **Source / File**: `mohui666` / [`candidate_v66_meta_closed_loop.py`](candidate_v66_meta_closed_loop.py:451)
- **Active Timesteps**: Steps 718 to 718
- **V54 Behavior**: Residual controller terminal rule collision on final turn
- **V66 Behavior**: Forces complete liquidation sell orders for all shed inventory on step 718 with replace=True
- **Economic Purpose**: Converts 100% of remaining farm inventory to cash on the final turn
- **Empirical Evidence**: step == 718: action = _TERMINAL_MARKET(obs, action, rule='collision', replace=True)

### Livestock Purchases & Placement: Livestock Schedule
- **Source / File**: `Kaito Fukami` / [`candidate_v62_composite_bakery_yarn.py`](candidate_v62_composite_bakery_yarn.py:1968)
- **Active Timesteps**: Steps 1 to 192
- **V54 Behavior**: Day 0: 2 cows, 2 sheep. Day 4: 1 cow. Day 7: 2 cows. Day 8: 1 cow. Total 6 cows, 2 sheep.
- **V66 Behavior**: Day 0: 2 cows, 2 sheep. Day 4: 1 cow. Day 6: 2 cows. Day 8: 1 cow. Adjusted placement.
- **Economic Purpose**: Earlier cow purchase on Day 6 accelerates milk production cycle
- **Empirical Evidence**: Cow purchases on steps 144 vs 168

### Worker Hiring: Labor Hiring Schedule
- **Source / File**: `Kaito Fukami` / [`candidate_v62_composite_bakery_yarn.py`](candidate_v62_composite_bakery_yarn.py:1968)
- **Active Timesteps**: Steps 1 to 624
- **V54 Behavior**: Day 0: 5 hands. Day 1: 0 hands. Day 2: 3 hands. Day 5: 6 hands. Day 8: 7 hands. Peak 15.
- **V66 Behavior**: Day 0: 5 hands. Day 1: 3 hands. Day 5: 6 hands. Day 7: 7 hands. Peak 15.
- **Economic Purpose**: Earlier hiring on Day 1 (3 hands vs 0) provides early labor for pasture expansion
- **Empirical Evidence**: HIRE order count at steps 24-25

### Crop Planting: Strawberry Planting Schedule
- **Source / File**: `Kaito Fukami` / [`candidate_v62_composite_bakery_yarn.py`](candidate_v62_composite_bakery_yarn.py:1968)
- **Active Timesteps**: Steps 120 to 288
- **V54 Behavior**: Plants 38 strawberry plants across Days 5 to 11 in quadrant 1 and 2
- **V66 Behavior**: Plants 38 strawberry plants with compact layout and adjusted watering timing
- **Economic Purpose**: Minimizes watering transit distances between strawberry patches
- **Empirical Evidence**: Coordinate analysis of PLANT orders

