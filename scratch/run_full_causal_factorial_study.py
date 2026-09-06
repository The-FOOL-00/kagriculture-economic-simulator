"""
=============================================================================
STRICT CAUSAL ISOLATION FACTORIAL BENCHMARK HARNESS
=============================================================================
Executes 50 paired seeds (both seats = 100 games per treatment per opponent)
across 8 factorial treatment arms against 4 benchmark opponents.

Opponent Classifications:
1. Replay Crop Dusta: OPEN-LOOP (Recorded Replay Tape from episode 104824599)
2. Replay KawattaTaido: OPEN-LOOP (Recorded Replay Tape from episode 104817623)
3. LiveFlooder V1: CLOSED-LOOP (State-adaptive wool flooder & dynamic harvester)
4. Aethel V1 / Titan: CLOSED-LOOP (Full 4-layer state-feedback crop titan)

Tracks full tick-level macroeconomic telemetry:
- Q3 affordability at T216
- Actual Q3 unlock step
- Day 5, 9, 10, 15, 20, 25, 30 cash
- Worker & livestock trajectories
- Town shop demand profiles
- Causal effect sizes and interaction terms
=============================================================================
"""

import os
import sys
import time
import json
import math
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
from kaggle_environments import make

project_root = r"c:\Users\Sundareswaran\Kagriculture"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import scratch.causal_agents as ca
import candidates.slot2_aethel_refined_v2 as v2
import candidates.slot1_titan_control as titan_v1
import opponents.live_flooder_v1 as lf
import opponents.replay_crop_dusta as cd
import opponents.replay_kawatta_taido as kw

OPPONENTS = {
    "live_flooder_v1": {
        "agent": lf.agent,
        "name": "LiveFlooder_V1",
        "type": "CLOSED_LOOP",
        "desc": "Dynamic feedback-driven sheep/wool flooder"
    },
    "aethel_v1_titan": {
        "agent": titan_v1.agent,
        "name": "Aethel_Prime_V1",
        "type": "CLOSED_LOOP",
        "desc": "4-Layer closed-loop production anchor"
    },
    "replay_crop_dusta": {
        "agent": cd.agent,
        "name": "Replay_Crop_Dusta",
        "type": "OPEN_LOOP",
        "desc": "Recorded replay tape of #2 Champion match 104824599"
    },
    "replay_kawatta_taido": {
        "agent": kw.agent,
        "name": "Replay_Kawatta_Taido",
        "type": "OPEN_LOOP",
        "desc": "Recorded replay tape of #4 Flooder match 104817623"
    },
}

TREATMENTS = {
    "BASE_V2": {
        "agent_fn": ca.agent_base,
        "name": "Base V2 (Frozen)",
        "desc": "Exact frozen baseline"
    },
    "Q3_ONLY": {
        "agent_fn": ca.agent_q3_only,
        "name": "Treatment 1: Q3 Velocity Only",
        "desc": "Unlock Q3 at T216 if money >= $4,000"
    },
    "SHOP_ONLY": {
        "agent_fn": ca.agent_shop_only,
        "name": "Treatment 2: Shop Sync Only",
        "desc": "Observe town shops and adapt midgame planting"
    },
    "LIVESTOCK_ONLY": {
        "agent_fn": ca.agent_livestock_only,
        "name": "Treatment 3: Livestock Spec Only",
        "desc": "Branch animal purchases (Cow / Sheep / Balanced) based on shops"
    },
    "Q3_SHOP": {
        "agent_fn": ca.agent_q3_shop,
        "name": "Factorial: Q3 + Shop",
        "desc": "Q3 velocity + Shop synchronization"
    },
    "Q3_LIVESTOCK": {
        "agent_fn": ca.agent_q3_livestock,
        "name": "Factorial: Q3 + Livestock",
        "desc": "Q3 velocity + Dynamic livestock specialization"
    },
    "SHOP_LIVESTOCK": {
        "agent_fn": ca.agent_shop_livestock,
        "name": "Factorial: Shop + Livestock",
        "desc": "Shop synchronization + Livestock specialization"
    },
    "FULL_FACTORIAL": {
        "agent_fn": ca.agent_full_factorial,
        "name": "Factorial: Q3 + Shop + Livestock",
        "desc": "All three factors combined"
    },
}


def _run_single_match(item):
    t_key, opp_key, seed, swapped = item
    t_agent = TREATMENTS[t_key]["agent_fn"]
    o_agent = OPPONENTS[opp_key]["agent"]
    
    agent0 = o_agent if swapped else t_agent
    agent1 = t_agent if swapped else o_agent
    
    our_player = 1 if swapped else 0
    opp_player = 0 if swapped else 1
    
    cfg = {"episodeSteps": 720, "seed": seed}
    env = make("kaggriculture", configuration=cfg, debug=False)
    
    t0 = time.time()
    try:
        env.run([agent0, agent1])
        elapsed = time.time() - t0
        
        # Collect telemetry at checkpoints
        checkpoints = [72, 120, 144, 168, 192, 216, 240, 255, 256, 360, 480, 600, 719]
        cp_data = {}
        
        for cp in checkpoints:
            if cp < len(env.steps):
                step_entry = env.steps[cp]
                obs = step_entry[0]["observation"]
                farms = obs.get("farms", [])
                if len(farms) > our_player:
                    f_us = farms[our_player]
                    f_opp = farms[opp_player]
                    cp_data[f"m_{cp}"] = float(f_us.get("money", 0))
                    cp_data[f"q_{cp}"] = len(f_us.get("unlocked_quadrants", []))
                    cp_data[f"h_{cp}"] = len(f_us.get("hands", []))
                    
                    # Count animals at key steps
                    if cp in (240, 360, 480):
                        tiles = f_us.get("tiles", []) or []
                        cows = sum(1 for row in tiles for t in row if isinstance(t, dict) and t.get("animal") == "COW")
                        sheep = sum(1 for row in tiles for t in row if isinstance(t, dict) and t.get("animal") == "SHEEP")
                        cp_data[f"cows_{cp}"] = cows
                        cp_data[f"sheep_{cp}"] = sheep
                        
        # Determine actual Q3 purchase step
        actual_q3_step = None
        for s_idx in range(len(env.steps)):
            obs = env.steps[s_idx][0]["observation"]
            farms = obs.get("farms", [])
            if len(farms) > our_player:
                if len(farms[our_player].get("unlocked_quadrants", [])) >= 3:
                    actual_q3_step = s_idx
                    break
                    
        # Town shops on Day 3 & 6
        shops_d3 = []
        shops_d6 = []
        if len(env.steps) > 72:
            shops_d3 = (env.steps[72][0]["observation"].get("town") or {}).get("unlocked_shops", []) or []
        if len(env.steps) > 144:
            shops_d6 = (env.steps[144][0]["observation"].get("town") or {}).get("unlocked_shops", []) or []
            
        final_us = float(env.steps[-1][our_player].get("reward", 0) or 0)
        final_opp = float(env.steps[-1][opp_player].get("reward", 0) or 0)
        margin = final_us - final_opp
        win = 1.0 if final_us > final_opp else (0.0 if final_opp > final_us else 0.5)
        
        m_216 = cp_data.get("m_216", 0.0)
        t216_satisfied = bool(m_216 >= 4000.0)
        
        return {
            "t_key": t_key,
            "opp_key": opp_key,
            "seed": seed,
            "swapped": swapped,
            "final_us": final_us,
            "final_opp": final_opp,
            "margin": margin,
            "win": win,
            "m_216": m_216,
            "t216_satisfied": t216_satisfied,
            "actual_q3_step": actual_q3_step,
            "m_120": cp_data.get("m_120", 0.0),
            "m_240": cp_data.get("m_240", 0.0),
            "m_360": cp_data.get("m_360", 0.0),
            "m_480": cp_data.get("m_480", 0.0),
            "m_600": cp_data.get("m_600", 0.0),
            "q_216": cp_data.get("q_216", 1),
            "q_256": cp_data.get("q_256", 1),
            "q_360": cp_data.get("q_360", 1),
            "h_240": cp_data.get("h_240", 0),
            "h_360": cp_data.get("h_360", 0),
            "cows_360": cp_data.get("cows_360", 0),
            "sheep_360": cp_data.get("sheep_360", 0),
            "shops_d3": shops_d3,
            "shops_d6": shops_d6,
            "elapsed": elapsed,
            "error": None
        }
    except Exception as e:
        return {
            "t_key": t_key,
            "opp_key": opp_key,
            "seed": seed,
            "swapped": swapped,
            "final_us": 0.0,
            "final_opp": 0.0,
            "margin": 0.0,
            "win": 0.0,
            "m_216": 0.0,
            "t216_satisfied": False,
            "actual_q3_step": None,
            "elapsed": 0.0,
            "error": str(e)
        }


def run_full_study(seeds=range(10000, 10050), max_workers=8):
    print("=" * 80)
    print("STARTING STRICT CAUSAL ISOLATION FACTORIAL BENCHMARK")
    print(f"Seeds: {len(seeds)} paired seeds (seeds {min(seeds)}..{max(seeds)})")
    print(f"Total Matches: {len(TREATMENTS)} treatments x {len(OPPONENTS)} opponents x {len(seeds)*2} matches = {len(TREATMENTS)*len(OPPONENTS)*len(seeds)*2} games")
    print(f"Parallel Workers: {max_workers}")
    print("=" * 80)
    
    tasks = []
    for t_key in TREATMENTS:
        for opp_key in OPPONENTS:
            for seed in seeds:
                tasks.append((t_key, opp_key, seed, False))  # Player 0
                tasks.append((t_key, opp_key, seed, True))   # Player 1 (swapped)
                
    results = []
    t_start = time.time()
    completed = 0
    total = len(tasks)
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_run_single_match, task): task for task in tasks}
        for future in as_completed(futures):
            res = future.result()
            results.append(res)
            completed += 1
            if completed % 100 == 0 or completed == total:
                elapsed = time.time() - t_start
                rate = completed / max(1, elapsed)
                remain = (total - completed) / max(0.01, rate)
                print(f"Progress: {completed}/{total} matches ({completed/total*100:.1f}%) | Rate: {rate:.1f} games/s | ETA: {remain:.0f}s", flush=True)
                
    # Save raw results
    output_path = r"c:\Users\Sundareswaran\Kagriculture\scratch\causal_factorial_raw_results.json"
    with open(output_path, "w") as fp:
        json.dump(results, fp, indent=2)
    print(f"\nRaw results saved to {output_path}")
    
    return results


if __name__ == "__main__":
    run_full_study(seeds=range(10000, 10050), max_workers=8)
