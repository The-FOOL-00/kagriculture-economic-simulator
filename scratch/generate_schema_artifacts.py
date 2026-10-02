import json
import os

schema_json = {
    "engine_version": "1.32.7",
    "observation_root_fields": [
        "player", "step", "day", "hour", "remainingOverageTime",
        "farms", "market", "town", "private"
    ],
    "field_classifications": {
        "PUBLIC_STATE": [
            {
                "field": "observation.farms[opp_idx].money",
                "type": "float",
                "description": "Opponent current cash balance"
            },
            {
                "field": "observation.farms[opp_idx].farmer",
                "type": "List[int, int]",
                "description": "Opponent farmer (x, y) coordinates on their farm grid"
            },
            {
                "field": "observation.farms[opp_idx].hands",
                "type": "List[List[int, int]]",
                "description": "Opponent hired farm hands (x, y) positions"
            },
            {
                "field": "observation.farms[opp_idx].unlocked_quadrants",
                "type": "List[str]",
                "description": "Opponent unlocked land quadrants (e.g. ['NW', 'NE'])"
            },
            {
                "field": "observation.farms[opp_idx].hires_today",
                "type": "int",
                "description": "Number of workers opponent hired on current day"
            },
            {
                "field": "observation.farms[opp_idx].tiles",
                "type": "List[List[Union[None, str, dict]]]",
                "description": "Full 10x10 spatial farm grid of opponent showing land status, structures, plants, animals"
            },
            {
                "field": "observation.market.prices",
                "type": "Dict[str, int]",
                "description": "Shared market clearing prices for all commodities"
            },
            {
                "field": "observation.market.inventory",
                "type": "Dict[str, int]",
                "description": "Shared central market inventory volumes"
            },
            {
                "field": "observation.town.unlocked_shops",
                "type": "List[str]",
                "description": "List of active shops in town"
            },
            {
                "field": "observation.step",
                "type": "int",
                "description": "Current simulation step (0 to 719)"
            },
            {
                "field": "observation.day",
                "type": "int",
                "description": "Current simulation day (0 to 29)"
            },
            {
                "field": "observation.hour",
                "type": "int",
                "description": "Current simulation hour of the day (0 to 23)"
            },
            {
                "field": "observation.remainingOverageTime",
                "type": "float",
                "description": "Remaining overage clock in seconds"
            }
        ],
        "DERIVED_FROM_PUBLIC_STATE": [
            {
                "signal": "opponent_cow_count",
                "derivation": "sum(1 for row in opp_tiles for t in row if isinstance(t, dict) and t.get('animal') == 'COW')",
                "description": "Active cows currently placed in opponent pastures"
            },
            {
                "signal": "opponent_sheep_count",
                "derivation": "sum(1 for row in opp_tiles for t in row if isinstance(t, dict) and t.get('animal') == 'SHEEP')",
                "description": "Active sheep currently placed in opponent pastures"
            },
            {
                "signal": "opponent_goose_count",
                "derivation": "sum(1 for row in opp_tiles for t in row if isinstance(t, dict) and t.get('animal') == 'GOOSE')",
                "description": "Active geese currently placed in opponent coops"
            },
            {
                "signal": "opponent_pasture_count",
                "derivation": "sum(1 for row in opp_tiles for t in row if isinstance(t, dict) and t.get('kind') == 'PASTURE')",
                "description": "Total pasture structures built by opponent"
            },
            {
                "signal": "opponent_coop_count",
                "derivation": "sum(1 for row in opp_tiles for t in row if isinstance(t, dict) and t.get('kind') == 'COOP')",
                "description": "Total coop structures built by opponent"
            },
            {
                "signal": "opponent_hand_count",
                "derivation": "len(observation.farms[opp_idx].hands)",
                "description": "Total active hired workers on opponent farm"
            },
            {
                "signal": "opponent_unlocked_tiles",
                "derivation": "sum(1 for row in opp_tiles for t in row if t != 'LOCKED')",
                "description": "Total accessible land area in tiles (25, 50, 75, or 100)"
            },
            {
                "signal": "opponent_unharvested_milk",
                "derivation": "sum(t.get('yield_units', 0) for row in opp_tiles for t in row if isinstance(t, dict) and t.get('animal') == 'COW')",
                "description": "Milk accumulated on opponent cow tiles awaiting collection"
            },
            {
                "signal": "opponent_fed_cows_today",
                "derivation": "sum(1 for row in opp_tiles for t in row if isinstance(t, dict) and t.get('animal') == 'COW' and t.get('fed_today'))",
                "description": "Cows successfully fed by opponent today"
            },
            {
                "signal": "opponent_cared_cows_today",
                "derivation": "sum(1 for row in opp_tiles for t in row if isinstance(t, dict) and t.get('animal') == 'COW' and t.get('cared_today'))",
                "description": "Cows groomed/cared for by opponent today"
            },
            {
                "signal": "opponent_inferred_milk_sales",
                "derivation": "delta(market.inventory['MILK']) - our_milk_sales + town_consumption['MILK']",
                "description": "Inferred volume of milk dumped to market by opponent between steps"
            },
            {
                "signal": "opponent_cash_velocity",
                "derivation": "opp_money[t] - opp_money[t - window]",
                "description": "Rate of opponent capital accumulation or expenditure"
            }
        ],
        "PRIVATE_STATE": [
            {
                "field": "observation.private.shed",
                "accessibility": "OWN_AGENT_ONLY",
                "description": "Own farm shed storage contents"
            },
            {
                "field": "observation.private.seeds",
                "accessibility": "OWN_AGENT_ONLY",
                "description": "Own farm seeds inventory"
            },
            {
                "field": "observation.private.inventories",
                "accessibility": "OWN_AGENT_ONLY",
                "description": "Own farmer and hands backpack inventories"
            }
        ],
        "UNAVAILABLE": [
            {
                "item": "opponent_shed_contents",
                "reason": "Opponent private shed is isolated in opponent private state; omitted from our observation dictionary"
            },
            {
                "item": "opponent_worker_backpacks",
                "reason": "Opponent hand backpack inventories are in opponent private state; omitted from our observation dictionary"
            },
            {
                "item": "opponent_seed_inventory",
                "reason": "Opponent seed stock is in opponent private state; omitted from our observation dictionary"
            },
            {
                "item": "opponent_pending_market_orders",
                "reason": "Actions are executed synchronously by the interpreter each step; unexecuted orders are never visible"
            },
            {
                "item": "opponent_identity",
                "reason": "Engine observations do not provide agent names, Kaggle usernames, Elo, or version metadata"
            },
            {
                "item": "opponent_future_strategy_tape",
                "reason": "Future moves are private to the opponent policy"
            }
        ]
    }
}

os.makedirs("research/v54/observation", exist_ok=True)

with open("research/v54/observation/PUBLIC_OPPONENT_STATE_SCHEMA.json", "w") as f:
    json.dump(schema_json, f, indent=2)

markdown_content = f"""# V54 Public Opponent State Schema & Observability Audit

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
"""

with open("research/v54/observation/PUBLIC_OPPONENT_STATE_SCHEMA.md", "w") as f:
    f.write(markdown_content.strip() + "\n")

print("Generated PUBLIC_OPPONENT_STATE_SCHEMA.json and .md")
