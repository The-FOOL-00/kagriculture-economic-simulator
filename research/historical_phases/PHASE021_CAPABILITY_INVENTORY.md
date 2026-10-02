# PHASE 021: FORMAL CAPABILITY INVENTORY

**Date**: 2026-09-20  
**Phase**: PHASE021 — AEC Capability, Action-Space & Dependency Completeness Audit  
**Chassis / Engine Ground Truth**: C++ `sim.hpp` (bit-exact 1.32.7) / `kagsim.cpp` / Python runtime  

---

## 1. Executive Summary

This inventory audits all 18 unit operations, 7 market order operations, and 6 environment-driven state transitions defined in Kagriculture. Each transition is evaluated against AEC’s representational expressiveness, counterfactual simulation fidelity, composability, and potential to generate downstream economic blockages.

---

## 2. Unit Operations Capability Ledger

| Action Name | Actor | Preconditions | Postconditions & State Changes | Affected Inventory & Resources | Observable | Representable | Composable | CF Support | Downstream Blockage Risk |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **`PASS`** | Farmer, Hands | None | Unit stays stationary. No state changes. | None | Yes | Yes | Yes | Exact | None |
| **`NORTH`** | Farmer, Hands | `ny >= 0` | `pos_y -= 1`. Unit moves up. Legal onto locked tiles. | None | Yes | Yes | Yes | Exact | Collision if co-located with non-cooperating unit. |
| **`SOUTH`** | Farmer, Hands | `ny < board_size` | `pos_y += 1`. Unit moves down. | None | Yes | Yes | Yes | Exact | Collision risk. |
| **`EAST`** | Farmer, Hands | `nx < board_size` | `pos_x += 1`. Unit moves right. | None | Yes | Yes | Yes | Exact | Collision risk. |
| **`WEST`** | Farmer, Hands | `nx >= 0` | `pos_x -= 1`. Unit moves left. | None | Yes | Yes | Yes | Exact | Collision risk. |
| **`PICKUP`** | Farmer, Hands | `is_shed_adjacent(x,y)`, `arg < N_ITEMS`, `n > 0` | Transfers `min(n, shed[arg])` from `f.shed` to `f.inv[u]`. | `f.shed[arg] -= take`, `f.inv[u][arg] += take` | Yes | Partial | Partial | Exact | Depletes shed stock needed for `SELL` or `FEED`. |
| **`DROP`** | Farmer, Hands | `is_shed_adjacent(x,y)` | Transfers all items from `f.inv[u]` to `f.shed` up to capacity. Excess discarded! | `f.inv[u]` cleared, `f.shed` updated, `f.discarded` credited | Yes | Partial | No (AEC lacks multi-step route-to-shed) | Exact | If shed is full (`shed_total == 100`), goods are permanently destroyed! |
| **`PLACE`** | Farmer, Hands | On empty coop/pasture (animal) OR shed-adjacent (commodity) | Places animal on structure OR places `n` units into shed. | `f.inv[u][arg] -= n`, `f.shed[arg] += n` | Yes | Partial | No | Exact | Misplaced animal locks tile permanently (cannot be dug up). |
| **`PLANT`** | Farmer, Hands | `tile.kind == T_EMPTY`, `seeds[crop] > 0`, atomic validation | `tile.kind = T_PLANT`, `consecutive_dry = 1`, `yield_units = ongoing ? 0 : 1`. | `f.seeds[crop] -= 1` | Yes | Partial (Farmer only) | No | Exact | **Atomic failure**: If sum of PLANT requests > seeds held, ALL PLANTs of that crop fail turn-wide! |
| **`WATER`** | Farmer, Hands | `tile.kind == T_PLANT`, `!watered_today` | Sets `watered_today = true`. For non-ongoing crops in window: increments `yield_units`. | None | Yes | Partial (Farmer only) | No | Exact | Missing a watering step permanently reduces terminal yield. |
| **`HARVEST`** | Farmer, Hands | `tile.yield_units > 0`, age >= `first_yield_day` | Transfers `yield_units` into `f.inv[u]`. For non-ongoing: `tile = T_EMPTY`. | `f.inv[u][crop] += yield`, tile yield reset to 0 | Yes | Single-step only | **NO** | Exact | **HIGH (CARGO TRAP)**: Produce enters worker backpack. If worker is farmhand, goods are inaccessible for market/planting until day-end! |
| **`FERTILIZE`**| Farmer, Hands | `tile.kind == T_PLANT`, `f.inv[u][FERTILIZER] >= 1` | Sets `fertilized_until_day = day + 2`. Doubles watering yield increments. | `f.inv[u][FERTILIZER] -= 1` | Yes | No | No | Exact | Fails silently if worker has no fertilizer in personal backpack. |
| **`DIG`** | Farmer, Hands | `tile.kind != T_EMPTY`, `!tile.has_animal` | Clears tile to `T_EMPTY`. Removes weeds or existing crops. | Destroys growing crops with 0 salvage! | Yes | Yes | No | Exact | Sunk-cost destruction if applied to productive crop plots. |
| **`BUILD_COOP`**| Farmer, Hands | `tile.kind == T_EMPTY`, `!is_locked` | Creates `T_COOP` on tile. | None | Yes | No | No | Exact | Locks tile permanently for coop use. |
| **`BUILD_PASTURE`**| Farmer, Hands| `tile.kind == T_EMPTY`, `!is_locked` | Creates `T_PASTURE` on tile. | None | Yes | No | No | Exact | Locks tile permanently for pasture use. |
| **`FEED`** | Farmer, Hands | `tile.has_animal`, `!fed_today`, `f.inv[u][WHEAT] >= 1` | Sets `fed_today = true`. Enables daily animal yield and fertilizer. | `f.inv[u][WHEAT] -= 1` | Yes | Partial | No | Exact | **Silent Failure**: Fails if worker backpack lacks WHEAT. 2 consecutive unfed days = animal escapes! |
| **`COLLECT_FERTILIZER`**| Farmer, Hands| `tile.has_animal`, `fertilizer_available` | Collects 1 fertilizer into `f.inv[u]`. | `f.inv[u][FERTILIZER] += 1`, tile cleared | Yes | No | No | Exact | Cargo stays in backpack until dropped. |
| **`CARE`** | Farmer, Hands | `tile.has_animal`, `!cared_today` | Sets `cared_today = true`. Increments `pending_care_bonus`. | None | Yes | Partial | No | Exact | Wasted action if animal is not fed on the same day. |

---

## 3. Market Operations Capability Ledger

| Order Name | Preconditions | Postconditions & Market Mechanics | Affected State Variables | Observable | Representable | Composable | CF Support | Downstream Blockage Risk |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **`HIRE`** | `money >= cost`, `n_units < MAX_UNITS` | Adds 1 auxiliary farmhand for current day. Spawns at free shed-access tile. Cost follows Fibonacci series. | `money -= cost`, `n_units += 1`, `hires_today += 1` | Yes | Partial | No | Exact | High cost escalation ($300, $500, $800...) if over-hired. |
| **`BUY_LAND`** | `money >= price`, quadrants remaining | Unlocks next quadrant (NE, SW, SE) at costs ($1000, $2000, $4000). | `money -= price`, `n_quadrants += 1`, tiles unlocked | Yes | No | No | Exact | Premature land purchase drains capital needed for seeds. |
| **`BUY_SEED`** | `money >= price * n` | Adds seeds directly to `f.seeds[crop]`. Deducts purchase cost. | `money -= cost`, `seeds[crop] += n` | Yes | Partial | Yes | Exact | Over-purchasing seeds locks liquid cash without return. |
| **`BUY_PRODUCT`**| `money >= price * n`, `shed_total < 100` | Adds product to `f.shed[item]`. Increases market inventory and depresses buy prices. | `money -= cost`, `shed[item] += n`, `shed_total += n` | Yes | Partial | Yes | Exact | Can overflow shed capacity, causing harvested crops to discard. |
| **`BUY_ANIMAL`** | `money >= cost`, appropriate empty structure | Adds animal to shed or structure. | `money -= cost` | Yes | No | No | Exact | Stranded animal if no coop/pasture is available. |
| **`SELL`** | `f.shed[item] >= n` | Sells produce from shed to shared market pool. Decreases market inventory, depresses price. | `f.shed[item] -= n`, `money += revenue` | Yes | **YES (Live Foundation)** | Yes | Exact | **Shed Requirement**: Can ONLY sell from `f.shed`. Goods in unit backpacks cannot be sold! |

---

## 4. Environment-Driven Temporal State Transitions

| Transition Name | Trigger Frequency | Mechanics & Rule Invariants | State Effects | Impact on AEC Decision Integrity |
| :--- | :---: | :--- | :--- | :--- |
| **`daily_refresh_plants`** | Every 24 turns (Step 23, 47, ...) | Unwatered plants increment `consecutive_dry`. If `>= 2`, plant dies and turns into `T_WEED`. Watered plants reset dry counter. Ongoing crops increment yield if interval met. | Crop yield updates, weed transitions | Premature harvesting of non-ongoing crops (e.g. WHEAT at yield 1 instead of 3) forfeits future daily growth! |
| **`daily_refresh_animals`** | Every 24 turns | Unfed animals increment `consecutive_dry`. If `>= 2`, animal escapes! Fed animals produce product and deposit fertilizer. Care adds bonus. | Animal yield, fertilizer spawned, possible escape | Feed failure cascade causes permanent loss of capital asset ($300-$500). |
| **`spawn_weeds`** | Every 24 turns | Every `T_EMPTY` tile rolls `rng.random() < 0.005` to spawn a weed. | `tile.kind = T_WEED` | Harvesting a non-ongoing crop leaves tile empty; if not replanted immediately, tile risks weed infestation. |
| **`drop_inventories`** | Every 24 turns | All units `u = 0..n-1` dump backpacks into `f.shed` up to `shed_capacity - shed_total`. **Excess is permanently discarded** (`f.discarded += excess`). | Backpacks cleared, shed filled or excess lost | Late-game multi-worker harvests can overflow shed at day-end, destroying high-value crops silently! |
| **`daily_reset_units`** | Every 24 turns | **ALL AUXILIARY FARMHANDS DESPAWN** (`f.n_units = 1`). Farmer resets position to `(4, 4)`. `hires_today = 0`. All unit backpacks cleared. | Only Unit 0 survives into next day | **CRITICAL CAPABILITY BOUNDARY**: Farmhands are ephemeral 1-day agents. Any long-horizon multi-day coordination assuming farmhand persistence is invalid. |
| **`town_consume`** | Every turn | Unlocked shops consume goods from market inventory, inflating market prices over time. | Market inventories drop, prices appreciate | Front-loading sells before shop consumption destroys price appreciation advantage. |

---

## 5. Architectural Capability Gaps Identified

From the formal inventory above, three severe interface and capability gaps emerge:
1. **The Backpack-to-Shed Handoff Gap**: In Kagriculture, unit inventories and shed inventory are strictly decoupled. Selling, seed inventory, and feed access require shed presence or specific backpack contents. AEC currently lacks a multi-step route-to-shed + deposit sequence.
2. **The Diurnal Ephemerality Boundary**: Auxiliary farmhands exist only for the 24 turns of the day in which they are hired. They cannot be assigned persistent, multi-day roles, and their actions must align with their daily lifecycle.
3. **Biological Growth Window Sensitivity**: Non-ongoing crops (WHEAT, CARROT, MELON) have a growth window where daily watering scales `yield_units` from 1 up to `max_yield` (up to 4 or 6). Harvesting as soon as `yield_units >= 1` is an economic catastrophe that destroys future compound yield.
