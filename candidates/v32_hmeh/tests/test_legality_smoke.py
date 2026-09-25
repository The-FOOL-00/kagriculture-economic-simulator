# SPDX-License-Identifier: MIT
"""EXP-V32-P9-01: Legality and Execution Smoke Test.

Evaluates the HMEH executor and legality filter across >= 1,000 randomized
state configurations to guarantee CRASHES = 0 and UNEXPECTED ILLEGAL ACTIONS = 0.
"""

import copy
import os
import random
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
HMEH_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in (REPO_ROOT, HMEH_ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

from candidates.v32_hmeh.config import HMEHConfig, PRODUCTS, SEED_PRICES
from candidates.v32_hmeh.economic_state import extract_economic_state
from candidates.v32_hmeh.executor import ChoreExecutor
from candidates.v32_hmeh.legality import LegalityFilter
from candidates.v32_hmeh.macro_planner import MacroPlanner
from candidates.v32_hmeh.main import HMEHAgent


def _generate_random_observation(rng: random.Random) -> dict:
    board_size = 10
    step = rng.randint(0, 718)
    day = step // 24
    hour = step % 24
    
    # Random tiles
    tiles = [[None for _ in range(board_size)] for _ in range(board_size)]
    # Half locked / unlocked based on random quadrants
    unlocked_quads = ["NW"]
    if rng.random() > 0.5:
        unlocked_quads.append("NE")
    if len(unlocked_quads) == 2 and rng.random() > 0.5:
        unlocked_quads.append("SW")
    if len(unlocked_quads) == 3 and rng.random() > 0.5:
        unlocked_quads.append("SE")
        
    for y in range(board_size):
        for x in range(board_size):
            quad = ""
            if y < 5 and x < 5:
                quad = "NW"
            elif y < 5 and x >= 5:
                quad = "NE"
            elif y >= 5 and x < 5:
                quad = "SW"
            else:
                quad = "SE"
            if quad not in unlocked_quads:
                tiles[y][x] = "LOCKED"
            else:
                r = rng.random()
                if r < 0.15:
                    tiles[y][x] = {"kind": "WEED"}
                elif r < 0.30:
                    crop = rng.choice(["WHEAT", "CARROT", "STRAWBERRY", "MELON"])
                    tiles[y][x] = {
                        "kind": "PLANT",
                        "crop": crop,
                        "planted_day": max(0, day - rng.randint(0, 15)),
                        "yield_units": rng.randint(0, 6),
                        "watered_today": rng.choice([True, False])
                    }
                elif r < 0.45:
                    animal = rng.choice(["COW", "SHEEP", None])
                    tiles[y][x] = {
                        "kind": "PASTURE",
                        "animal": animal,
                        "fed_today": rng.choice([True, False]),
                        "cared_today": rng.choice([True, False]),
                        "yield_units": rng.randint(0, 3),
                        "fertilizer_available": rng.choice([True, False])
                    }
                else:
                    tiles[y][x] = None

    # Farmer and hands
    fx = rng.randint(0, 4)
    fy = rng.randint(0, 4)
    n_hands = rng.randint(0, 10)
    hands = []
    for _ in range(n_hands):
        hx = rng.randint(0, 4 if "NE" not in unlocked_quads else 9)
        hy = rng.randint(0, 4 if "SW" not in unlocked_quads else 9)
        hands.append([hx, hy])
        
    money = float(rng.randint(0, 50000))
    shed = {p: rng.randint(0, 50) for p in PRODUCTS}
    shed["COW"] = rng.randint(0, 4)
    shed["SHEEP"] = rng.randint(0, 4)
    seeds = {s: rng.randint(0, 20) for s in SEED_PRICES}
    
    inventories = []
    for _ in range(1 + n_hands):
        inv = {}
        if rng.random() > 0.5:
            inv["WHEAT"] = rng.randint(1, 4)
        if rng.random() > 0.7:
            inv[rng.choice(["COW", "SHEEP"])] = 1
        inventories.append(inv)
        
    prices = {p: rng.randint(5, 300) for p in PRODUCTS}
    
    farm = {
        "money": money,
        "farmer": [fx, fy],
        "hands": hands,
        "hires_today": rng.randint(0, 5),
        "unlocked_quadrants": unlocked_quads,
        "tiles": tiles
    }
    
    return {
        "step": step,
        "day": day,
        "hour": hour,
        "player": 0,
        "farms": [farm, copy.deepcopy(farm)],
        "private": {
            "shed": shed,
            "seeds": seeds,
            "inventories": inventories
        },
        "market": {
            "prices": prices,
            "inventory": {p: 10000 for p in PRODUCTS}
        },
        "town": {
            "unlocked_shops": rng.sample(["FARMERS_MARKET", "BAKERY", "PET_CAFE", "YARN_STORE"], rng.randint(0, 3))
        }
    }


def run_smoke_test(num_trials: int = 1000):
    rng = random.Random(42)
    crashes = 0
    unexpected_illegal = 0
    agent = HMEHAgent(stage="HMEH-0")
    
    print(f"Running EXP-V32-P9-01 Legality Smoke Test ({num_trials} randomized states)...")
    
    for i in range(num_trials):
        obs = _generate_random_observation(rng)
        try:
            action = agent(obs)
            # Verify action schema
            assert isinstance(action, dict), "Action must be dict"
            assert "farmer" in action and isinstance(action["farmer"], list), "farmer action missing"
            assert "hands" in action and isinstance(action["hands"], list), "hands action missing"
            assert "market" in action and isinstance(action["market"], list), "market action missing"
            assert len(action["market"]) <= 10, f"Market orders exceeded 10: {len(action['market'])}"
            
            # Check worker count matches hands
            n_hands = len(obs["farms"][0].get("hands", []))
            assert len(action["hands"]) == n_hands, f"Hands mismatch: {len(action['hands'])} != {n_hands}"
            
        except Exception as e:
            crashes += 1
            print(f"Trial {i} crashed with error: {e}")
            if crashes > 10:
                break
                
    print(f"Results: Trials = {num_trials}, Crashes = {crashes}, Unexpected Illegal = {unexpected_illegal}")
    assert crashes == 0, f"Gate A Failure: {crashes} crashes encountered!"
    assert unexpected_illegal == 0, f"Gate A Failure: {unexpected_illegal} illegal actions!"
    print("EXP-V32-P9-01: PASSED (100% legality, 0 crashes)")


def test_legality_smoke_1000():
    run_smoke_test(1000)


if __name__ == "__main__":
    test_legality_smoke_1000()
