# V54 Public Opponent State Schema & Observability Audit

**Engine Version**: `kaggle-environments` 1.32.7  
**Simulation Harness**: `FastKagricultureSim` (bit-exact official interpreter wrapper)  
**Governance Constraint**: Only legally observable public state and signals derived from public state may be used. No hidden opponent fields. No opponent identity lookups.

---

## 1. Executive Summary

In Kagriculture 1.32.7, the game state passed to an agent's `agent(observation, configuration)` callback is partitioned into two visibility domains:

1. **Shared & Spatial Observation (`observation`)**:
   - `farms`: An array containing both `farms[0]` and `farms[1]`. Both players have full, continuous visibility into each other's money, worker locations, unlocked quadrants, daily hires, and full 10x10 tile arrays (including structures, crop growth stages, animal placements, and daily feeding/caring flags).
   - `market`: Shared market clearing prices and central market inventory for all 9 commodities.
   - `town`: List of unlocked town shops.
   - `step`, `day`, `hour`: Exact simulation clock.
2. **Private Observation (`observation.private`)**:
   - Isolated per player. Player 0 cannot observe Player 1's shed storage, seed bags, or worker backpack contents.

Therefore, **we have continuous, legal visibility into the opponent's physical farm investments, animal counts, pasture locations, worker counts, cash, and shared market pricing**.

---

## 2. Exhaustive Field Classification

| Field / Signal | Source Location | Classification | Legal For Policy Use? |
|---|---|:---:|:---:|
| `opponent_money` | `observation.farms[opp].money` | `PUBLIC_STATE` | **YES** |
| `opponent_farmer_pos` | `observation.farms[opp].farmer` | `PUBLIC_STATE` | **YES** |
| `opponent_hands_pos` | `observation.farms[opp].hands` | `PUBLIC_STATE` | **YES** |
| `opponent_hand_count` | `len(observation.farms[opp].hands)` | `DERIVED_FROM_PUBLIC_STATE` | **YES** |
| `opponent_unlocked_quadrants` | `observation.farms[opp].unlocked_quadrants` | `PUBLIC_STATE` | **YES** |
| `opponent_unlocked_land_tiles` | Count of non-`LOCKED` tiles in `farms[opp].tiles` | `DERIVED_FROM_PUBLIC_STATE` | **YES** |
| `opponent_cow_count` | Count of `tile['animal'] == 'COW'` in `farms[opp].tiles` | `DERIVED_FROM_PUBLIC_STATE` | **YES** |
| `opponent_sheep_count` | Count of `tile['animal'] == 'SHEEP'` in `farms[opp].tiles` | `DERIVED_FROM_PUBLIC_STATE` | **YES** |
| `opponent_goose_count` | Count of `tile['animal'] == 'GOOSE'` in `farms[opp].tiles` | `DERIVED_FROM_PUBLIC_STATE` | **YES** |
| `opponent_pasture_count` | Count of `tile['kind'] == 'PASTURE'` in `farms[opp].tiles` | `DERIVED_FROM_PUBLIC_STATE` | **YES** |
| `opponent_coop_count` | Count of `tile['kind'] == 'COOP'` in `farms[opp].tiles` | `DERIVED_FROM_PUBLIC_STATE` | **YES** |
| `opponent_unharvested_milk` | Sum of `tile['yield_units']` on cow tiles | `DERIVED_FROM_PUBLIC_STATE` | **YES** |
| `opponent_cow_fed_state` | `tile['fed_today']` flags on cow tiles | `DERIVED_FROM_PUBLIC_STATE` | **YES** |
| `opponent_cow_care_state` | `tile['cared_today']` flags on cow tiles | `DERIVED_FROM_PUBLIC_STATE` | **YES** |
| `shared_market_prices` | `observation.market.prices` | `PUBLIC_STATE` | **YES** |
| `shared_market_inventory` | `observation.market.inventory` | `PUBLIC_STATE` | **YES** |
| `shared_town_shops` | `observation.town.unlocked_shops` | `PUBLIC_STATE` | **YES** |
| `game_time (step/day/hour)` | `observation.step / day / hour` | `PUBLIC_STATE` | **YES** |
| `inferred_opponent_milk_sales` | Step-to-step market inventory balance delta | `DERIVED_FROM_PUBLIC_STATE` | **YES** |
| `own_shed_inventory` | `observation.private.shed` | `PRIVATE_STATE` (Self) | **YES (for self)** |
| `own_seeds` | `observation.private.seeds` | `PRIVATE_STATE` (Self) | **YES (for self)** |
| `own_worker_inventories` | `observation.private.inventories` | `PRIVATE_STATE` (Self) | **YES (for self)** |
| `opponent_shed_inventory` | Opponent private state | `UNAVAILABLE` | **NO (ILLEGAL)** |
| `opponent_worker_inventories`| Opponent private state | `UNAVAILABLE` | **NO (ILLEGAL)** |
| `opponent_seeds` | Opponent private state | `UNAVAILABLE` | **NO (ILLEGAL)** |
| `opponent_market_orders` | Transient action payload | `UNAVAILABLE` | **NO (ILLEGAL)** |
| `opponent_identity / username`| Competition environment | `UNAVAILABLE` | **NO (ILLEGAL)** |

---

## 3. Key Findings for COWSWAP Decision at Step 150

1. **Exact Animal Visibility**: At Step 150 (and at every step prior), we know **exactly** how many Cows, Sheep, and Geese the opponent has physically placed on their board.
2. **Pasture Infrastructure**: We know how many pastures the opponent has constructed, whether they have expanded their land quadrants, and how many farm hands they have hired to maintain livestock.
3. **Unharvested Output**: We can inspect whether the opponent's cows have accumulated milk units on their tiles, and whether those cows are being fed and groomed.
4. **Market Pressure**: We have continuous visibility into the shared milk market inventory and clearing price.
5. **No Speculation Required**: We do NOT need to guess or probe opponent shed contents; their physical herd on the board provides an open, deterministic, legally observable signal.

All subsequent V54 policies will adhere strictly to this public schema.
