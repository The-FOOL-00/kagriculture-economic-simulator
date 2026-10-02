# AUDIT #2: ENGINE GROUND TRUTH & GAME RULES SPECIFICATION
## Authoritative Simulator Mechanics Directly Verified from C++ `sim.hpp` and Python `kaggle_environments 1.32.7`

This document establishes the definitive ground truth of the Kaggriculture game engine.
Every fact in this document has been independently verified by:
1. Direct source inspection of `external_repos/kaggriculture-cppsim/sim/sim.hpp`
2. Direct source inspection of `kaggle_environments/envs/kaggriculture/kaggriculture.py`
3. Executable minimal Python tests interacting with the `kagsim` C++ engine

---

## 1. Core Environmental Parameters

| Engine Constant | Value | Source Line (`sim.hpp`) | Source Line (`kaggriculture.py`) | Verified Behavior |
|---|:---:|---|---|---|
| **Episode Length** | **720 Steps** | Line 142: `episode_steps = 720;` | Line 14: `DEFAULT_EPISODE_STEPS = 720` | Steps 0 to 719; status is `DONE` after step 719. |
| **Turns per Day** | **24 Steps** | Line 146: `turns_per_day = 24;` | Line 15: `DEFAULT_TURNS_PER_DAY = 24` | 30 days total (Days 0 to 29). Hour = `step % 24`, Day = `step // 24`. |
| **Board Dimensions** | **10 x 10 (100 Tiles)** | Line 143: `board_size = 10;` | Line 13: `DEFAULT_BOARD_SIZE = 10` | Divided into 4 quadrants: NW (starting), NE, SW, SE. |
| **Starting Capital** | **$3,000.00** | Line 144: `starting_money = 3000;` | Line 16: `DEFAULT_STARTING_MONEY = 3000` | Exact starting cash for both players. |
| **Shed Capacity** | **100 Units** | Line 147: `shed_capacity = 100;` | `SHED_CAPACITY = 100` | Drops/harvests that exceed 100 are permanently and silently discarded. |
| **Max Market Orders** | **10 Orders / Turn** | Line 145: `max_orders = 10;` | `maxMarketOrdersPerTurn = 10` | Orders at index 10+ are silently dropped without error. |
| **Shop Unlock Interval**| **Every 3 Days (72 Steps)**| Line 149: `shop_unlock_interval = 3;`| `SHOP_UNLOCK_INTERVAL = 3` | Unlocks occur at steps 72, 144, 216, 288, 360, 432, 504, 576. |
| **Max Shop Instances** | **8 Shops** | Line 138: `MAX_SHOP_INSTANCES = 8;` | `MAX_SHOP_INSTANCES = 8` | Exactly 8 town shop instances unlock per game. |

---

## 2. Town Shops & Demand Profiles (Ground Truth vs Hallucinations)

Town shop instances are sampled **uniform at random WITH REPLACEMENT** from 8 possible shop types (`rng.choice_index(N_SHOPS)`).
Duplicate shops (e.g. Double Pizza Shop, Triple Pet Cafe) occur frequently.

### The Authoritative Shop Demand Table

| Shop Identifier | Products Consumed (Ground Truth) | Demand Multiplier | Demands Strawberry? | Demands Tomato? | Old Research Model (`shop_transition_model.py`) | Audit #1 Assessment | Audit #2 Status |
|---|---|:---:|:---:|:---:|---|---|:---:|
| **`BAKERY`** | `EGG, WHEAT` | 1.0x | NO | NO | `["WHEAT", "EGG"]` | Correct | **MATCH** |
| **`BRUNCH_SPOT`** | `EGG, WHEAT, STRAWBERRY` | 1.0x | **YES** | NO | `["EGG", "MILK", "STRAWBERRY"]` | Fabricated (Added Milk, omitted Wheat) | **CONFIRMED ERROR IN OLD MODEL** |
| **`FARMERS_MARKET`**| `WHEAT, CARROT, TOMATO, STRAWBERRY` | 1.0x | **YES** | **YES** | `["CARROT", "TOMATO", "STRAWBERRY", "MELON"]` | Fabricated (Added Melon, omitted Wheat) | **CONFIRMED ERROR IN OLD MODEL** |
| **`ICE_CREAM_SHOP`**| `STRAWBERRY, MILK, WHEAT` | 1.0x | **YES** | NO | `["MILK", "STRAWBERRY"]` | Incomplete (Omitted Wheat) | **CONFIRMED ERROR IN OLD MODEL** |
| **`PET_CAFE`** | `CARROT` | **2.0x** | NO | NO | `["CARROT", "MILK"]` | Fabricated (Added Milk; Pet Cafe demands ONLY Carrot) | **CONFIRMED ERROR IN OLD MODEL** |
| **`PIZZA_SHOP`** | `MILK, TOMATO, WHEAT` | 1.0x | NO | **YES** | `["WHEAT", "TOMATO"]` | Incomplete (Omitted Milk; Pizza requires Milk) | **CONFIRMED ERROR IN OLD MODEL** |
| **`SMOOTHIE_SHOP`** | `STRAWBERRY, MILK` | 1.0x | **YES** | NO | `["CARROT", "STRAWBERRY", "MELON"]` | Fabricated (Added Carrot & Melon, omitted Milk) | **CONFIRMED ERROR IN OLD MODEL** |
| **`YARN_STORE`** | `WOOL` | **2.0x** | NO | NO | `["WOOL"]` | Correct | **MATCH** |

### Critical Downstream Implications of the Old Model Errors
1. **Strawberry Demand Frequency**: Exactly **4 out of 8 shops** demand Strawberry (`BRUNCH_SPOT`, `FARMERS_MARKET`, `ICE_CREAM_SHOP`, `SMOOTHIE_SHOP`). Base probability of Strawberry demand appearing on any given draw is $4/8 = 50.0\%$. The old model correctly counted 4 shops, but misidentified their companion requirements.
2. **Tomato Demand Frequency**: Exactly **2 out of 8 shops** demand Tomato (`FARMERS_MARKET`, `PIZZA_SHOP`). Base probability of Tomato demand is $2/8 = 25.0\%$.
3. **The Pizza / Milk Connection**: The old research model assumed `PIZZA_SHOP` required only Wheat and Tomato. In reality, Pizza requires **Milk, Tomato, and Wheat**. Agents specializing in Tomato for Pizza worlds without cows failed to supply the full composite demand.
4. **Pet Cafe Milk Hallucination**: The old model claimed Pet Cafe consumed Milk. Pet Cafe consumes **strictly Carrot** at a 2.0x multiplier.

---

## 3. Labor & Hiring Cost Mechanics (Fibonacci Truth vs $200 Hallucination)

A pervasive myth in earlier reports (repeated by Audit #1 in S2) was that "worker hiring costs $200 per hand, so 4 hands cost $800."
This is **flatly contradicted by engine source**:

### The True Engine Hiring Formula
In `sim.hpp` lines 658–663 and `kaggriculture.py`:
$$\text{Cost of } n\text{-th hire of the day} = \text{cfg.hire\_mult} \times \text{fib}(n)$$
where $\text{cfg.hire\_mult} = 1$ and $\text{fib}(n)$ is the Fibonacci sequence:
$$\text{fib}(0)=1, \text{fib}(1)=1, \text{fib}(2)=2, \text{fib}(3)=3, \text{fib}(4)=5, \text{fib}(5)=8, \text{fib}(6)=13, \text{fib}(7)=21, \text{fib}(8)=34, \text{fib}(9)=55, \text{fib}(10)=89$$

### Cumulative Daily Hiring Cost Schedule
| Hires Made Today | Cost of This Hire | Cumulative Money Spent | Prior Research Myth | True Engine Reality |
|:---:|:---:|:---:|:---:|---|
| **1st Hire** | $1.00 | $1.00 | $200.00 | **$1.00** |
| **2nd Hire** | $1.00 | $2.00 | $400.00 | **$2.00** |
| **3rd Hire** | $2.00 | $4.00 | $600.00 | **$4.00** |
| **4th Hire** | $3.00 | $7.00 | **$800.00** | **$7.00** (Not $800!) |
| **5th Hire** | $5.00 | $12.00 | $1,000.00 | **$12.00** |
| **6th Hire** | $8.00 | $20.00 | $1,200.00 | **$20.00** |
| **7th Hire** | $13.00 | $33.00 | $1,400.00 | **$33.00** |
| **8th Hire** | $21.00 | $54.00 | $1,600.00 | **$54.00** |
| **9th Hire** | $34.00 | $88.00 | $1,800.00 | **$88.00** |
| **10th Hire** | $55.00 | $143.00 | $2,000.00 | **$143.00** |
| **11th Hire** | $89.00 | $232.00 | $2,200.00 | **$232.00** |

**Conclusion**: Hiring 11 workers on Day 12 costs a grand total of **$232.00**, NOT $2,200, and hiring 4 workers costs **$7.00**, NOT $800. The claim that "cash fell below $800 preventing hiring of 4 workers" was mathematically and mechanically impossible under engine rules.

---

## 4. Market Execution & Order Truncation (`MAX_ORDERS = 10`)

Directly verified from `sim.hpp` lines 551–575:
```cpp
void process_market(const Action& a0, const Action& a1) {
    int nq[2];
    for (int p = 0; p < 2; ++p) nq[p] = std::min(acts[p]->n_orders, cfg.max_orders);
    int max_len = std::max(nq[0], nq[1]);
    for (int i = 0; i < max_len; ++i) { ... }
}
```

### Verified Market Invariants
1. **Truncation Threshold**: The engine processes `min(n_orders, 10)`. Any order at index $\ge 10$ is silently ignored without raising an error or exception.
2. **Order Slot Consumption**:
   - `['HIRE']`: Takes 1 order slot. Multiple hires can be submitted in one turn; each executes atomically in player order subject to cash and `MAX_UNITS`.
   - `['BUY_LAND']`: Takes 1 order slot. Executes atomically.
   - `['SELL', item, quantity]`: Multi-unit sell takes **1 order slot**. Units execute one-by-one in per-unit lockstep with the opponent until exhausted or unsold.
   - `['BUY_SEED', crop, quantity]`: Takes 1 order slot.
   - `['BUY_ANIMAL', animal, quantity]`: Takes 1 order slot.
3. **No Engine Order Priority**: The engine imposes **zero internal priority sorting**. Orders are executed strictly in the order provided in the agent's action array. If an agent places 10 `HIRE` orders first, any subsequent `SELL` order is dropped.

---

## 5. Crop Lifecycle & Rot Kinetics

Verified from `sim.hpp` lines 710–727 and 770–776:

1. **Ongoing Crops (Strawberry, Tomato)**:
   - Yield interval: Yields fruit every few days up to `max_yield = 4`.
   - Lifespan Assignment: On the step when `yield_count == 4`, line 775 assigns:
     $$\text{max\_lifespan\_step} = (\text{next\_day} + 1) \times 24$$
     This sets the expiration to the dawn of the day after the 4th harvest cycle completes.
2. **Rot Kinetics**:
   - Starting at `max_lifespan_step`, on every step where $(\text{step} - \text{max\_lifespan\_step}) \% 2 == 0$ (which corresponds to **every even step**), line 724 decrements:
     $$\text{yield\_units} -= 1$$
   - Once $\text{yield\_units} \le 0$, line 725 instantly replaces the crop with a weed:
     $$\text{Tile } w; \quad w.\text{kind} = \text{T\_WEED}; \quad t = w;$$
   - Consequence: An unharvested ongoing crop rots at a rate of **1 unit every 2 steps (12 units per day)**. Unscheduled plantings without dedicated harvest workers convert to weeds within 24–48 steps.

---

## 6. Weed Generation & RNG Coupling (Unpinned vs Pinned)

Verified from `sim.hpp` lines 729–750:
1. At `end_of_day(day)`:
   - Line 735: `spawn_weeds(f, rng)` executes **BEFORE** town shop unlocking (line 745).
   - `spawn_weeds` iterates over every tile on the farm. For every **empty tile**, it calls `rng.next_double() < cfg.weed_chance`.
2. **RNG Stream Drift**:
   - Because `rng` is consumed once per empty tile, an agent that leaves 50 empty tiles consumes 50 random draws, while an agent that leaves 20 empty tiles consumes 20 random draws.
   - At line 748, when the town shop is unlocked via `rng.choice_index(N_SHOPS)`, the random generator is in a completely different internal state.
   - **Crucial Rule**: In unpinned simulation, **farming actions alter future shop reveals**. Agents that suppress early planting re-roll all 8 town shops, causing artificial score variances of $\pm \$25,000$ that are pure simulator artifacts. Pinned shop simulation (`--pin-shops`) is required for controlled policy evaluation.
