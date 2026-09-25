# SPDX-License-Identifier: MIT
import os, sys
sys.path.insert(0, os.path.abspath("."))
from kaggle_environments import make
from scripts.v32_common import load_agent

def inspect_step712():
    a7 = load_agent("E9_AST")
    dmit = load_agent("E8_DMITRII")
    env = make("kaggriculture", configuration={"seed": 249677})
    env.run([lambda o, c=None: a7.act(o, c), lambda o, c=None: dmit.act(o, c)])

    obs = env.steps[712][0]["observation"]
    farm = obs["farms"][0]
    priv = obs["private"]

    print("=== STEP 712 STATE ===")
    print("Money:", farm["money"])
    print("Shed:", {k: v for k, v in priv["shed"].items() if v > 0})
    print("Farmer pos:", farm["farmer"], "inv:", {k: v for k, v in priv["inventories"][0].items() if v > 0})
    for idx, (h, inv) in enumerate(zip(farm["hands"], priv["inventories"][1:])):
        non_zero = {k: v for k, v in inv.items() if v > 0}
        print(f"Hand {idx+1} pos: {h}, inv: {non_zero}")

    tiles_with_yield = []
    for y in range(10):
        for x in range(10):
            t = farm["tiles"][y][x]
            if isinstance(t, dict):
                y_u = t.get("yield_units", 0)
                fert = t.get("fertilizer_available", False)
                if y_u > 0 or fert:
                    tiles_with_yield.append((x, y, t))

    print(f"\nTiles with yield/fert at 712: {len(tiles_with_yield)}")
    for x, y, t in tiles_with_yield:
        print(f"  ({x},{y}): kind={t.get('kind')}, crop={t.get('crop')}, animal={t.get('animal')}, yield={t.get('yield_units')}, fert={t.get('fertilizer_available')}")

    # Now let's see what happened between 712 and 719 in A7 baseline:
    # Which of these tiles were harvested by A7?
    # What items were dropped in the shed by A7?
    # What items were sold by A7?
    print("\n=== A7 BASELINE TERMINAL EXECUTION (712-718) ===")
    for s in range(712, 719):
        action = env.steps[s][0]["action"]
        farmer_act = action.get("farmer")
        hands_act = action.get("hands")
        market_act = action.get("market")
        print(f"Step {s}:")
        print(f"  Farmer: {farmer_act}")
        # print only non-pass hand actions
        active_hands = [(h_idx+1, a) for h_idx, a in enumerate(hands_act) if a != ["PASS"]]
        print(f"  Active hands: {active_hands}")
        print(f"  Market: {market_act}")

    # At step 719 (final)
    obs_end = env.steps[719][0]["observation"]
    farm_end = obs_end["farms"][0]
    priv_end = obs_end["private"]
    print("\n=== STEP 719 FINAL STATE ===")
    print("Final Cash:", farm_end["money"])
    print("Final Shed:", {k: v for k, v in priv_end["shed"].items() if v > 0})
    for idx, inv in enumerate(priv_end["inventories"]):
        nz = {k: v for k, v in inv.items() if v > 0}
        if nz:
            print(f"Worker {idx} carried: {nz}")

    # End tiles
    tiles_end = []
    for y in range(10):
        for x in range(10):
            t = farm_end["tiles"][y][x]
            if isinstance(t, dict):
                y_u = t.get("yield_units", 0)
                fert = t.get("fertilizer_available", False)
                if y_u > 0 or fert:
                    tiles_end.append((x, y, t))
    print(f"Tiles with remaining yield/fert at 719: {len(tiles_end)}")
    for x, y, t in tiles_end:
        print(f"  ({x},{y}): kind={t.get('kind')}, crop={t.get('crop')}, animal={t.get('animal')}, yield={t.get('yield_units')}, fert={t.get('fertilizer_available')}")

if __name__ == "__main__":
    inspect_step712()
