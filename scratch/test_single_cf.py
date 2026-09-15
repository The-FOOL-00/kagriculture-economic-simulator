import sys
import os
import copy
import numpy as np
from kaggle_environments import make

V54_PATH = os.path.abspath("external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py")

import importlib.util
def load_v54():
    spec = importlib.util.spec_from_file_location("v54_test", V54_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.agent, mod._V54_ROUTE

def test_variant(seed, variant):
    agent_p0, route_p0 = load_v54()
    agent_p1, _ = load_v54()
    
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.reset()

    total_morn_mov = 0
    total_morn_prod = 0
    strawb_sold = 0
    wheat_sold = 0
    milk_sold = 0
    wool_sold = 0
    fert_sold = 0
    unserved_h4 = 0

    for step in range(719):
        obs0 = env.state[0].observation
        farm0 = obs0.farms[0]
        tiles = farm0["tiles"]
        b_size = len(tiles)
        hour = step % 24
        day = step // 24
        is_morn = (hour < 4)

        base_act0 = agent_p0(obs0, env.configuration)
        act1 = agent_p1(env.state[1].observation, env.configuration)

        act0 = copy.deepcopy(base_act0)

        if is_morn:
            if variant == "A":
                # Baseline canonical
                pass

            elif variant == "C":
                # Neutralize livestock chores: mark animals fed & cared
                for y in range(b_size):
                    for x in range(b_size):
                        t = tiles[y][x]
                        if isinstance(t, dict) and "animal" in t:
                            t["fed_today"] = True
                            t["cared_today"] = True
                
                # If farmer was doing livestock chore, redirect to strawberry harvest or water
                farmer_act = act0.get("farmer", ["PASS"])
                if farmer_act and farmer_act[0] in ["FEED", "CARE", "COLLECT_FERTILIZER", "PICKUP"]:
                    # Free farmer: harvest mature strawberry if adjacent/standing, or water
                    fx, fy = farm0["farmer"]
                    cur_t = tiles[fy][fx]
                    if isinstance(cur_t, dict) and cur_t.get("crop") == "STRAWBERRY" and cur_t.get("yield_units", 0) > 0:
                        act0["farmer"] = ["HARVEST"]
                    elif isinstance(cur_t, dict) and cur_t.get("crop") == "STRAWBERRY" and not cur_t.get("watered_today"):
                        act0["farmer"] = ["WATER"]

            elif variant == "D":
                # Strawberry first priority
                # If mature strawberry exists and worker is nearby, harvest first
                pass

            elif variant == "E":
                # Pure movement optimization: remove diagonal / zigzag moves
                pass

        env.step([act0, act1])

        # Track sales
        for m in act0.get("market", []):
            if m and m[0] == "SELL" and len(m) > 2:
                item, qty = m[1], m[2]
                if item == "STRAWBERRY": strawb_sold += qty
                elif item == "WHEAT": wheat_sold += qty
                elif item == "MILK": milk_sold += qty
                elif item == "WOOL": wool_sold += qty
                elif item == "FERTILIZER": fert_sold += qty

        # Track movement and productive
        all_w = [act0.get("farmer", ["PASS"])] + act0.get("hands", [])
        for w in all_w:
            op = w[0] if w else "PASS"
            if op in ["NORTH", "SOUTH", "EAST", "WEST"]:
                if is_morn: total_morn_mov += 1
            elif op != "PASS":
                if is_morn: total_morn_prod += 1

    final_reward = float(env.steps[-1][0].reward or 0.0)
    print(f"Variant {variant} | Reward: ${final_reward:,.0f} | Strawb: {strawb_sold} | Milk: {milk_sold} | MornMov: {total_morn_mov} | MornProd: {total_morn_prod}")
    return final_reward

if __name__ == "__main__":
    for v in ["A", "C"]:
        test_variant(101, v)
