# AUDIT 2.1: ENGINE GROUND TRUTH & SIMULATOR SEMANTICS VERIFICATION
## Definitive Mechanical Rules Verified from C++ `sim.hpp` and Python `kaggle_environments 1.32.7`

This document establishes the verified ground truth of the Kaggriculture game engine, auditing Audit 2's `AUDIT2_ENGINE_FACTS.md` directly against source code in `external_repos/kaggriculture-cppsim/sim/sim.hpp` and official `kaggle_environments/envs/kaggriculture/kaggriculture.py`.

---

## 1. Canonical Ground-Truth Town Shop Table

Town shops unlock every 3 days (steps 72, 144, 216, 288, 360, 432, 504, 576). Instances are sampled **uniform at random with replacement** from 8 possible types (`rng.choice_index(N_SHOPS)`).

| Shop Identifier | Unlock Days | Exact Products Demanded | Demand Multiplier | Verified Evidence Source | Audit 2.1 Verification |
|:---|:---:|:---|:---:|:---|:---:|
| **`BAKERY`** | 3, 6, 9, 12, 15, 18, 21, 24 | `EGG, WHEAT` | 1.0x | `sim.hpp:128`, `kg.SHOPS['BAKERY']` | **VERIFIED** |
| **`BRUNCH_SPOT`** | 3, 6, 9, 12, 15, 18, 21, 24 | `EGG, WHEAT, STRAWBERRY` | 1.0x | `sim.hpp:129`, `kg.SHOPS['BRUNCH_SPOT']` | **VERIFIED** |
| **`FARMERS_MARKET`**| 3, 6, 9, 12, 15, 18, 21, 24 | `WHEAT, CARROT, TOMATO, STRAWBERRY` | 1.0x | `sim.hpp:130`, `kg.SHOPS['FARMERS_MARKET']` | **VERIFIED** |
| **`ICE_CREAM_SHOP`**| 3, 6, 9, 12, 15, 18, 21, 24 | `STRAWBERRY, MILK, WHEAT` | 1.0x | `sim.hpp:131`, `kg.SHOPS['ICE_CREAM_SHOP']` | **VERIFIED** |
| **`PET_CAFE`** | 3, 6, 9, 12, 15, 18, 21, 24 | `CARROT` (Strictly single product) | **2.0x** | `sim.hpp:132, 137`, `kg.SHOPS['PET_CAFE']` | **VERIFIED** |
| **`PIZZA_SHOP`** | 3, 6, 9, 12, 15, 18, 21, 24 | `MILK, TOMATO, WHEAT` (All 3 required) | 1.0x | `sim.hpp:133`, `kg.SHOPS['PIZZA_SHOP']` | **VERIFIED** |
| **`SMOOTHIE_SHOP`** | 3, 6, 9, 12, 15, 18, 21, 24 | `STRAWBERRY, MILK` | 1.0x | `sim.hpp:134`, `kg.SHOPS['SMOOTHIE_SHOP']` | **VERIFIED** |
| **`YARN_STORE`** | 3, 6, 9, 12, 15, 18, 21, 24 | `WOOL` (Strictly single product) | **2.0x** | `sim.hpp:135, 137`, `kg.SHOPS['YARN_STORE']` | **VERIFIED** |

---

## 2. Comparison: Ground Truth vs Research Models vs Audit 2

| Shop | Ground Truth | Flawed Research Model (`shop_transition_model.py`) | Audit 1 Assessment | Audit 2 Correction | Audit 2.1 Final Status |
|:---|:---|:---|:---|:---|:---:|
| **`BAKERY`** | `['EGG', 'WHEAT']` | `['WHEAT', 'EGG']` | Match | Verified Match | **VERIFIED MATCH** |
| **`BRUNCH_SPOT`** | `['EGG', 'WHEAT', 'STRAWBERRY']` | `['EGG', 'MILK', 'STRAWBERRY']` | Fabricated (Added Milk, omitted Wheat) | Confirmed Error | **VERIFIED FABRICATION** |
| **`FARMERS_MARKET`** | `['WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY']` | `['CARROT', 'TOMATO', 'STRAWBERRY', 'MELON']` | Fabricated (Added Melon, omitted Wheat) | Confirmed Error | **VERIFIED FABRICATION** |
| **`ICE_CREAM_SHOP`** | `['STRAWBERRY', 'MILK', 'WHEAT']` | `['MILK', 'STRAWBERRY']` | Incomplete (Omitted Wheat) | Confirmed Error | **VERIFIED INCOMPLETE** |
| **`PET_CAFE`** | `['CARROT']` (2.0x) | `['CARROT', 'MILK']` | Fabricated (Added Milk) | Confirmed Error | **VERIFIED FABRICATION** |
| **`PIZZA_SHOP`** | `['MILK', 'TOMATO', 'WHEAT']` | `['WHEAT', 'TOMATO']` | Incomplete (Omitted Milk) | Confirmed Error | **VERIFIED INCOMPLETE** |
| **`SMOOTHIE_SHOP`** | `['STRAWBERRY', 'MILK']` | `['CARROT', 'STRAWBERRY', 'MELON']` | Fabricated (Added Carrot/Melon, omitted Milk) | Confirmed Error | **VERIFIED FABRICATION** |
| **`YARN_STORE`** | `['WOOL']` (2.0x) | `['WOOL']` | Match | Verified Match | **VERIFIED MATCH** |

### Downstream Contamination Analysis
Because 6 of the 8 shop demand profiles were misstated in `shop_transition_model.py`:
1. **Value of Information (VoI) Contamination**: Any tree search, dynamic program, or heuristic valuing early shop unlocks based on `shop_transition_model.py` was solving the wrong game.
2. **Crop Portfolio Contamination**: The model assumed Pizza worlds required only Wheat and Tomato, leading researchers to hypothesize that Tomato specialization alone could satisfy Pizza demand. In reality, Pizza requires Milk ($3/8$ base probability), meaning Tomato specialization without dairy infrastructure failed composite shop demands.
3. **Audit 2 Conclusion**: Audit 2 correctly identified that all downstream Markov decision models and VoI derivations built on `shop_transition_model.py` are contaminated and must remain discarded.

---

## 3. Labor & Hiring Cost Mechanics (Fibonacci Truth vs $200 Hallucination)

In `sim.hpp` lines 658–663 and `kaggriculture.py`:
```cpp
void do_hire(Farm& f) {
    int cost = cfg.hire_mult * fib(f.hires_today);
    if (f.money < cost || f.n_units >= MAX_UNITS) { f.tel_refused_hire += 1; return; }
    f.money -= cost; f.total_spend += cost;
    f.tel_hire_paid += cost;
    f.hires_today += 1;
    ...
}
```
Where `cfg.hire_mult = 1`, and `fib(n)` is the standard Fibonacci sequence:
$$\text{fib}(0)=1, \; \text{fib}(1)=1, \; \text{fib}(2)=2, \; \text{fib}(3)=3, \; \text{fib}(4)=5, \; \text{fib}(5)=8, \; \text{fib}(6)=13, \; \text{fib}(7)=21, \; \text{fib}(8)=34, \; \text{fib}(9)=55, \; \text{fib}(10)=89$$

### Cumulative Daily Cost Schedule

| Daily Hire # | Marginal Cost (Engine) | Cumulative Cost (Engine) | Prior Research Myth ($200/hand) | Discrepancy Factor |
|:---:|:---:|:---:|:---:|:---:|
| **1st Hire** | $1.00 | $1.00 | $200.00 | 200.0x |
| **2nd Hire** | $1.00 | $2.00 | $400.00 | 200.0x |
| **3rd Hire** | $2.00 | $4.00 | $600.00 | 150.0x |
| **4th Hire** | $3.00 | **$7.00** | **$800.00** | **114.3x** |
| **5th Hire** | $5.00 | $12.00 | $1,000.00 | 83.3x |
| **6th Hire** | $8.00 | $20.00 | $1,200.00 | 60.0x |
| **7th Hire** | $13.00 | $33.00 | $1,400.00 | 42.4x |
| **8th Hire** | $21.00 | $54.00 | $1,600.00 | 29.6x |
| **9th Hire** | $34.00 | $88.00 | $1,800.00 | 20.5x |
| **10th Hire** | $55.00 | $143.00 | $2,000.00 | 14.0x |
| **11th Hire** | $89.00 | **$232.00** | **$2,200.00** | **9.5x** |

### Origin of the $200 Myth
The myth arose because `closed_loop_v2.py` line 148, `liquidity_controller.py` line 32, and `economic_state.py` line 101 implemented a conservative internal agent heuristic:
```python
hiring_obligation = (len(obs["farms"][player]["hands"]) + 1) * 200.0
```
This was an agent-level liquidity buffer designed to reserve cash for potential future actions. Early researchers and Audit 1 confused this agent reserve heuristic with an engine rule, claiming that the engine required $200 per hand.

---

## 4. Market Order Execution (`MAX_ORDERS = 10`)

Directly verified from `sim.hpp` lines 551–575:
```cpp
void process_market(const Action& a0, const Action& a1) {
    int nq[2];
    for (int p = 0; p < 2; ++p) nq[p] = std::min(acts[p]->n_orders, cfg.max_orders);
    int max_len = std::max(nq[0], nq[1]);
    for (int i = 0; i < max_len; ++i) { ... }
}
```

### Verified Engine Rules
1. **Per-Player Limit**: The limit of 10 applies independently to each player (`p = 0` and `p = 1`).
2. **Silent Truncation**: Orders at array index $\ge 10$ are dropped silently without raising exceptions or logging errors.
3. **Slot Consumption**:
   - `['HIRE']`: Takes 1 slot.
   - `['BUY_LAND']`: Takes 1 slot.
   - `['BUY_SEED', crop, qty]`: Takes 1 slot regardless of `qty`.
   - `['BUY_ANIMAL', animal, qty]`: Takes 1 slot regardless of `qty`.
   - `['SELL', item, qty]`: Takes 1 slot regardless of `qty`.
4. **Execution Order**: Strictly preserved according to array index order. The engine does NOT reorder or prioritize orders.
5. **Failed Order Slot Consumption**: An order that fails to execute due to lack of cash, shed capacity, or market inventory still consumes one of the 10 order slots.

---

## 5. Crop Lifecycle & Rot Kinetics

Verified from `sim.hpp` lines 710–727 and 770–776:
1. **Ongoing Crops (Strawberry, Tomato)**:
   - Yield up to 4 harvest cycles (`max_yield = 4`).
   - Lifespan expires at dawn of the day after harvest 4:
     $$\text{max\_lifespan\_step} = (\text{next\_day} + 1) \times 24$$
2. **Rot Kinetics**:
   - Starting at $\text{max\_lifespan\_step}$, on every step where $(\text{step} - \text{max\_lifespan\_step}) \% 2 == 0$ (every even step):
     $$\text{yield\_units} -= 1$$
   - When $\text{yield\_units} \le 0$, line 725 instantly replaces the tile with a weed:
     $$\text{Tile } w; \quad w.\text{kind} = \text{T\_WEED}; \quad t = w;$$
   - Consequence: An expired, unharvested ongoing crop rots at **1 unit every 2 turns (12 units per day)**, decaying to weeds within 24 to 48 steps.

---

## 6. Weed Generation & RNG Stream Coupling

Verified from `sim.hpp` lines 155–165 and 729–750:
1. At `end_of_day(day)`, `spawn_weeds(f, rng)` executes **before** town shop unlocking (`rng.choice_index(N_SHOPS)`).
2. `spawn_weeds` iterates over every tile and consumes one random draw per **empty tile** (`rng.next_double() < cfg.weed_chance`).
3. An agent with 50 empty tiles consumes 50 draws; an agent with 20 empty tiles consumes 20 draws.
4. Consequently, in unpinned simulation, **farming decisions alter future town shop sequences across identical seeds**.
5. As documented by simulator author `destbreso`, suppressing a single planting on Day 0 re-rolls all 8 town shops, creating artificial score variations of $\pm \$25,000$ that are simulation artifacts. Shop pinning (`--pin-shops`) is required for true policy evaluation.

---

## 7. Engine Fact Audit Summary

| Fact | Audit 2 Statement | Source Code Ground Truth | Audit 2.1 Status |
|:---|:---|:---|:---:|
| 8 Town Shops | Sampled with replacement | `sim.hpp:748` (`rng.choice_index(8)`) | **VERIFIED TRUE** |
| Unlock Cadence | Steps 72, 144, ..., 576 | `sim.hpp:149, 745` | **VERIFIED TRUE** |
| Shop Demands | 6 of 8 misstated in old model | `sim.hpp:127-136`, `kg.SHOPS` | **VERIFIED TRUE** |
| Hiring Cost | Fibonacci sequence ($1, 1, 2...$) | `sim.hpp:659` (`cfg.hire_mult * fib(hires)`) | **VERIFIED TRUE** |
| Market Limit | `MAX_ORDERS = 10` silent drop | `sim.hpp:554` (`min(n_orders, 10)`) | **VERIFIED TRUE** |
| Rot Kinetics | 1 unit/2 turns on even steps | `sim.hpp:724-725` | **VERIFIED TRUE** |
| Weed Coupling | Empty tiles shift shop draw | `sim.hpp:735, 748` | **VERIFIED TRUE** |
| Shed Limit | 100 units hard limit | `sim.hpp:147` | **VERIFIED TRUE** |
