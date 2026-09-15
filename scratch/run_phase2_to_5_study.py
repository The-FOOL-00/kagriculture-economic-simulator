import sys
import os
import json
import math
from collections import defaultdict
import numpy as np
from concurrent.futures import ProcessPoolExecutor
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))

import candidates.candidate_cl_fert_gated as m1_module
from scratch.run_wheat_quota_sweep_50seeds import ParameterizedQuotaAgent
from scratch.run_pasture_causal_ablations_50seeds import MechanismAAgent
from scratch.conditional_policy_agents import (
    PolicyC1Agent, PolicyC2Agent, PolicyC3Agent, PolicyC4Agent, PolicyC5Agent, SheepFirstAgent
)

def run_single_agent(agent, seed):
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    steps = env.run([agent, "starter"])
    
    reward = float(steps[-1][0]["reward"])
    sold = defaultdict(int)
    for st in steps:
        for o in (st[0].get("action") or {}).get("market", []):
            if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL":
                sold[o[1]] += int(o[2])
                
    # Worker movement metrics
    worker_moves = 0
    worker_idles = 0
    for st in steps:
        act = st[0].get("action") or {}
        f_act = act.get("farmer", ["PASS"])[0]
        if f_act in ("NORTH", "SOUTH", "EAST", "WEST"):
            worker_moves += 1
        elif f_act == "PASS":
            worker_idles += 1
        for h_act in act.get("hands", []):
            op = h_act[0] if h_act else "PASS"
            if op in ("NORTH", "SOUTH", "EAST", "WEST"):
                worker_moves += 1
            elif op == "PASS":
                worker_idles += 1

    last_f0 = steps[-1][0]["observation"]["farms"][0]
    last_tiles = last_f0["tiles"]
    cows_final = sum(1 for r in last_tiles for t in r if isinstance(t, dict) and t.get("animal") == "COW")
    sheep_final = sum(1 for r in last_tiles for t in r if isinstance(t, dict) and t.get("animal") == "SHEEP")

    return {
        "reward": reward,
        "sold": dict(sold),
        "worker_moves": worker_moves,
        "worker_idles": worker_idles,
        "cows": cows_final,
        "sheep": sheep_final
    }

def run_predecision_telemetry(seed):
    agent = ParameterizedQuotaAgent(50)
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    env.reset()
    
    telemetry = {}
    for step_idx in range(145):
        obs0 = env.steps[-1][0]["observation"]
        f0 = obs0["farms"][0]
        p0 = obs0.get("private", {}) or {}
        
        if step_idx == 144: # Day 6 Hour 0
            tiles = f0["tiles"]
            cows_field = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "COW")
            sheep_field = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "SHEEP")
            pastures_free = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("kind") == "PASTURE" and not t.get("animal"))
            pastures_total = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("kind") == "PASTURE")
            
            shed = p0.get("shed", {})
            cows_shed = int(shed.get("COW", 0) or 0)
            sheep_shed = int(shed.get("SHEEP", 0) or 0)
            
            unlocked_quads = f0.get("unlocked_quadrants", [])
            is_single_quad = len(unlocked_quads) == 1
            
            # Check sheep-compatible coordinates free
            # In NW quad: sheep coordinates are (4, 2) and (2, 4)
            # Check whether tile (2, 4) or (4, 2) is occupied by COW
            cow_on_2_4 = False
            cow_on_4_2 = False
            if tiles[4][2] and isinstance(tiles[4][2], dict) and tiles[4][2].get("animal") == "COW":
                cow_on_2_4 = True
            if tiles[2][4] and isinstance(tiles[2][4], dict) and tiles[2][4].get("animal") == "COW":
                cow_on_4_2 = True
                
            total_cows = cows_field + cows_shed
            free_sheep_coords = (0 if cow_on_2_4 else 1) + (0 if cow_on_4_2 else 1)
            if not is_single_quad:
                free_sheep_coords += 4 # NE sheep slots
                
            # If total_cows >= 4 and single quad, buying Cow 5 forces cow onto (2, 4)
            cow_placed_consumes_sheep = (total_cows >= 4 and is_single_quad)
            
            # Wheat sold by step 144
            wheat_sold_d6 = 0
            for st in env.steps:
                for o in (st[0].get("action") or {}).get("market", []):
                    if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL" and o[1] == "WHEAT":
                        wheat_sold_d6 += int(o[2])
                        
            straw_bushes = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("kind") == "PLANT" and t.get("crop") == "STRAWBERRY")
            wheat_plants = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("kind") == "PLANT" and t.get("crop") == "WHEAT")
            
            telemetry = {
                "seed": seed,
                "cash": f0["money"],
                "cows_shed": cows_shed,
                "cows_field": cows_field,
                "total_cows": total_cows,
                "sheep_shed": sheep_shed,
                "sheep_field": sheep_field,
                "free_pasture_tiles": pastures_free,
                "total_pasture_tiles": pastures_total,
                "free_sheep_coords": free_sheep_coords,
                "sheep_purchased_unplaced": sheep_shed,
                "exp_sheep_purchase_prob": 1.0,
                "exp_sheep_purchases_next3d": 3.0,
                "exp_marginal_wool_val": 400.0,
                "marginal_cow_milk_val": 120.0,
                "cow_placed_consumes_sheep_tile": cow_placed_consumes_sheep,
                "is_single_quadrant": is_single_quad,
                "wheat_sold_d6": wheat_sold_d6,
                "wheat_harvests_pending": wheat_plants,
                "strawberry_bushes": straw_bushes
            }
            break
            
        action = agent(obs0)
        env.step([action, "starter"])
        
    return telemetry
