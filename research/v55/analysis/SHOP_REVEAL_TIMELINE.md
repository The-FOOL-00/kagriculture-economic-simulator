# V55 Shop Reveal Mechanics & Exact Timeline Audit

**Engine Version**: `kaggle-environments` 1.32.7 (`kaggriculture.py`)  
**Simulation Harness**: `FastKagricultureSim` (bit-exact official interpreter wrapper)  
**Investigation**: Ground-truth engine audit of shop generation, revelation timing, and consumption dynamics.

---

## 1. Engine Implementation Facts (Code Inspection of `kaggriculture.py`)

### 1.1 Shop Unlock Schedule
- **Trigger**: Line 867-886 in `_end_of_day(state, env, day)`.
- **Interval**: Governed by `townShopUnlockInterval` configuration (default: **3 days = 72 simulation steps**).
- **Condition**: Fires at the conclusion of day $D$ where $(D + 1) \% 3 == 0$.
- **Exact Unlock Steps**:
  - **Shop 1**: Step **72** (Day 3, Hour 0)
  - **Shop 2**: Step **144** (Day 6, Hour 0)
  - **Shop 3**: Step **216** (Day 9, Hour 0)
  - **Shop 4**: Step **288** (Day 12, Hour 0)
  - **Shop 5**: Step **360** (Day 15, Hour 0)
  - **Shop 6**: Step **432** (Day 18, Hour 0)
  - **Shop 7**: Step **504** (Day 21, Hour 0)
  - **Shop 8**: Step **576** (Day 24, Hour 0)
- **Cap**: `MAX_SHOP_INSTANCES = 8` (Line 118). After Step 576, no further shops unlock.

### 1.2 Pseudo-Random Sampling with Replacement
- **Mechanism**: Line 871, 891:
  ```python
  rng = random.Random((seed * 1_000_003) ^ day)
  town["unlocked_shops"].append(rng.choice(sorted(SHOPS)))
  ```
- **Duplicate Instances**: **Explicitly permitted**. The same shop can appear multiple times (e.g., Seed 250436 has two `PIZZA_SHOP` instances, Seed 250439 has two `ICE_CREAM_SHOP` and two `SMOOTHIE_SHOP` instances).
- **Independent Consumption**: Each instance of a duplicate shop consumes independently every cycle.

### 1.3 Observation Visibility
- **Field**: `observation.town["unlocked_shops"]` (a Python list of string shop names).
- **Callback Timing**: The newly appended shop is **immediately visible in the observation passed to `agent(observation, configuration)` at Hour 0 of the unlock step** (e.g. at Step 216, `observation.town["unlocked_shops"]` contains the 3rd shop before any agent action is submitted).

### 1.4 Consumption Timing & Multipliers
- **Frequency**: Line 733-736 in `_town_consume(env, state, step)`:
  `shop_interval = max(1, int(get(cfg, "townShopSellInterval", 4)))`
  Consumption occurs every **4 steps** (`if step % 4 == 0`).
- **Immediate First Consumption**: Because unlock steps are divisible by 24 (and thus divisible by 4: $72 \% 4 == 0$, $216 \% 4 == 0$), **the new shop executes its very first consumption on the exact step it appears** (during post-action resolution).
- **Consumption Multiplier**:
  - **Single-product shop** (`PET_CAFE` for Carrot, `YARN_STORE` for Wool): **2 units** consumed per 4 steps (0.5 units/step).
  - **Multi-product shop** (all others): **1 unit of each required product** consumed per 4 steps (0.25 units/step per product).

---

## 2. Complete Shop Demand Catalog

| Shop Name | Required Commodities | Multiplier | Consumption Rate | Total Consumption from Step 216 to 719 | Total Consumption from Step 288 to 719 |
|---|---|:---:|:---:|:---:|:---:|
| **`PIZZA_SHOP`** | `['MILK', 'TOMATO', 'WHEAT']` | 1 | 0.25 units/step | **125 units** per product | **107 units** per product |
| **`ICE_CREAM_SHOP`** | `['STRAWBERRY', 'MILK', 'WHEAT']` | 1 | 0.25 units/step | **125 units** per product | **107 units** per product |
| **`SMOOTHIE_SHOP`** | `['STRAWBERRY', 'MILK']` | 1 | 0.25 units/step | **125 units** per product | **107 units** per product |
| **`BAKERY`** | `['EGG', 'WHEAT']` | 1 | 0.25 units/step | **125 units** per product | **107 units** per product |
| **`BRUNCH_SPOT`** | `['EGG', 'WHEAT', 'STRAWBERRY']`| 1 | 0.25 units/step | **125 units** per product | **107 units** per product |
| **`FARMERS_MARKET`**| `['WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY']` | 1 | 0.25 units/step | **125 units** per product | **107 units** per product |
| **`PET_CAFE`** | `['CARROT']` | 2 | 0.50 units/step | **250 units** Carrot | **214 units** Carrot |
| **`YARN_STORE`** | `['WOOL']` | 2 | 0.50 units/step | **250 units** Wool | **214 units** Wool |

---

## 3. Ground-Truth Shop Unlock Trajectories for Critical Seeds

| Step | Day:Hour | Seed 250416 (Negative Control) | Seed 250436 (COWSWAP Loss L07) | Seed 250439 (COWSWAP Loss L09) |
|:---:|:---:|:---|:---|:---|
| **72** | 3:00 | `BRUNCH_SPOT` (Egg, Wheat, Strawb) | `BRUNCH_SPOT` (Egg, Wheat, Strawb) | `BRUNCH_SPOT` (Egg, Wheat, Strawb) |
| **144** | 6:00 | `FARMERS_MARKET` (Wheat, Car, Tom, Str) | `FARMERS_MARKET` (Wheat, Car, Tom, Str) | `BAKERY` (Egg, Wheat) |
| **216** | 9:00 | **`PET_CAFE`** (Carrot) | **`PIZZA_SHOP`** (Milk, Tom, Wheat) | **`ICE_CREAM_SHOP`** (Str, Milk, Wheat) |
| **288** | 12:00| **`ICE_CREAM_SHOP`** (Str, Milk, Wheat) | **`PIZZA_SHOP`** (Milk, Tom, Wheat) | **`ICE_CREAM_SHOP`** (Str, Milk, Wheat) |
| **360** | 15:00| `BAKERY` (Egg, Wheat) | `SMOOTHIE_SHOP` (Str, Milk) | `PIZZA_SHOP` (Milk, Tom, Wheat) |
| **432** | 18:00| `FARMERS_MARKET` (Wheat, Car, Tom, Str) | `ICE_CREAM_SHOP` (Str, Milk, Wheat) | `SMOOTHIE_SHOP` (Str, Milk) |
| **504** | 21:00| `PIZZA_SHOP` (Milk, Tom, Wheat) | `YARN_STORE` (Wool) | `SMOOTHIE_SHOP` (Str, Milk) |
| **576** | 24:00| `ICE_CREAM_SHOP` (Str, Milk, Wheat) | `SMOOTHIE_SHOP` (Str, Milk) | `PIZZA_SHOP` (Milk, Tom, Wheat) |
| **Total Milk Shops** | - | **3 Milk Shops (Late)** | **5 Milk Shops (Persistent)** | **6 Milk Shops (Overwhelming)** |

---

## 4. Key Takeaways for V55 Continuation Architecture

1. **Exact Post-Reveal Checkpoint**: Step **216** is the very first step in the entire match where an agent can legally observe whether the environment rolled a Milk shop (`PIZZA_SHOP` on 250436, `ICE_CREAM_SHOP` on 250439) vs a non-milk shop (`PET_CAFE` on 250416).
2. **Step 288 Reinforcement**: Step **288** reveals the 4th shop, cementing whether the milk duopoly has compounded demand.
3. **Continuation Window**:
   - At Step 216, exactly **503 steps remain** (over 20 days).
   - At Step 288, exactly **431 steps remain** (nearly 18 days).
   - These horizons are long enough for post-reveal economic adjustments to compound if physically viable within V49's choreographic constraints.
