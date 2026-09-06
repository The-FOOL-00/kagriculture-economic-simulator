"""
Strict Causal Isolation Factorial Study on Dynamic Feed Arbitrage.
Runs 50 paired seeds (both seats = 100 matches per treatment per opponent)
across all causal factor combinations against closed-loop and open-loop meta opponents.
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

import scratch.causal_feed_arbitrage_agents as cfa
import candidates.slot2_aethel_refined_v2 as v2
import candidates.slot1_titan_control as titan_v1
import opponents.live_flooder_v1 as lf
import opponents.replay_crop_dusta as cd
import opponents.replay_kawatta_taido as kw
import opponents.replay_whyme_labs as whyme

OPPONENTS = {
    "aethel_v2_closed": {
        "agent": v2.agent,
        "name": "Aethel_Refined_V2",
        "type": "CLOSED_LOOP",
        "desc": "Baseline V2 champion self-play mirror"
    },
    "live_flooder_v1": {
        "agent": lf.agent,
        "name": "LiveFlooder_V1",
        "type": "CLOSED_LOOP",
        "desc": "Dynamic feedback wool flooder"
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
    "replay_whyme_labs": {
        "agent": whyme.agent,
        "name": "Replay_Whyme_Labs",
        "type": "OPEN_LOOP",
        "desc": "Recorded replay tape of #5 Champion match 104824599"
    },
}

TREATMENTS = {
    "A_BASE_V2": {
        "agent_fn": cfa.agent_A,
        "name": "Factor A: Base V2 (Frozen)",
        "desc": "Exact frozen baseline"
    },
    "B_DYN_LIQ": {
        "agent_fn": cfa.agent_B,
        "name": "Factor B: Dynamic Liquidation Only",
        "desc": "Liquidate eligible shed items when cash+potential >= $4k for early Q3"
    },
    "C_EXT_WHEAT": {
        "agent_fn": cfa.agent_C,
        "name": "Factor C: External Wheat Feed Only",
        "desc": "Buy cheap market wheat when buffer < 20 units; 8 cows"
    },
    "D_COWS_10": {
        "agent_fn": cfa.agent_D10,
        "name": "Factor D10: 10 Cows Only",
        "desc": "Scale cows to 10 with standard wheat farming"
    },
    "D_COWS_12": {
        "agent_fn": cfa.agent_D12,
        "name": "Factor D12: 12 Cows Only",
        "desc": "Scale cows to 12 with standard wheat farming"
    },
    "D_COWS_13": {
        "agent_fn": cfa.agent_D13,
        "name": "Factor D13: 13 Cows Only",
        "desc": "Scale cows to 13 with standard wheat farming"
    },
    "E_LIQ_WHEAT": {
        "agent_fn": cfa.agent_E,
        "name": "Factor E: Dyn Liq + Ext Wheat (B + C)",
        "desc": "Early Q3 dynamic liquidation + market wheat feed; 8 cows"
    },
    "F_LIQ_COWS": {
        "agent_fn": cfa.agent_F,
        "name": "Factor F: Dyn Liq + 12 Cows (B + D)",
        "desc": "Early Q3 dynamic liquidation + 12 cows; standard farm wheat"
    },
    "G_WHEAT_COWS": {
        "agent_fn": cfa.agent_G,
        "name": "Factor G: Ext Wheat + 12 Cows (C + D)",
        "desc": "Market wheat feed + 12 cows; standard T255 Q3"
    },
    "H_ALL_THREE_12C": {
        "agent_fn": cfa.agent_H,
        "name": "Factor H12: All Three (B + C + D12)",
        "desc": "Dyn Liq + Ext Wheat + 12 Cows"
    },
    "H_ALL_THREE_13C": {
        "agent_fn": cfa.agent_H13,
        "name": "Factor H13: All Three (B + C + D13)",
        "desc": "Dyn Liq + Ext Wheat + 13 Cows"
    },
    "SCHED_LIQ_D8": {
        "agent_fn": cfa.agent_SchedD8,
        "name": "Fixed Scheduled D8 Liquidation",
        "desc": "Fixed liquidation on Day 8 vs state-triggered dynamic liquidation"
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
        
        # Checkpoints for cash trajectory: Day 5 (120), Day 8 (192), Day 10 (240), Day 15 (360), Day 30 (719)
        checkpoints = [120, 168, 192, 200, 216, 240, 255, 360, 719]
        cp_cash = {}
        cp_quads = {}
        
        q3_step = -1
        total_wheat_bought = 0
        total_milk_sold = 0
        starvation_events = 0
        invalid_actions = 0
        
        for s_idx, step_entry in enumerate(env.steps):
            obs = step_entry[0]["observation"]
            farms = obs.get("farms", [])
            if len(farms) > our_player:
                f_us = farms[our_player]
                quads = f_us.get("unlocked_quadrants", [])
                if len(quads) >= 3 and q3_step == -1:
                    q3_step = s_idx
                    
                if s_idx in checkpoints:
                    cp_cash[f"cash_{s_idx}"] = float(f_us.get("money", 0))
                    cp_quads[f"quads_{s_idx}"] = len(quads)
                    
                # Check animal starvation (consecutive_unfed >= 2)
                for row in f_us.get("tiles", []):
                    for tile in row:
                        if isinstance(tile, dict) and tile.get("consecutive_unfed", 0) >= 2:
                            starvation_events += 1
                            
            # Check market orders in step action
            act_entry = step_entry[our_player]
            act = act_entry.get("action")
            if isinstance(act, dict):
                for ma in act.get("market", []):
                    if isinstance(ma, list) and len(ma) >= 3:
                        if ma[0] == "BUY_PRODUCT" and ma[1] == "WHEAT":
                            total_wheat_bought += int(ma[2])
                        elif ma[0] == "SELL" and ma[1] == "MILK":
                            total_milk_sold += int(ma[2])
                            
            # Check error status
            if act_entry.get("status") == "ERROR":
                invalid_actions += 1

        final_step = env.steps[-1]
        r_us = float(final_step[our_player]["reward"] or 0)
        r_opp = float(final_step[opp_player]["reward"] or 0)
        
        # Count final cows and sheep
        f_final = final_step[0]["observation"]["farms"][our_player]
        final_cows = sum(1 for row in f_final.get("tiles", []) for t in row if isinstance(t, dict) and t.get("animal") == "COW")
        final_sheep = sum(1 for row in f_final.get("tiles", []) for t in row if isinstance(t, dict) and t.get("animal") == "SHEEP")
        
        won = 1 if r_us > r_opp else (0.5 if r_us == r_opp else 0)
        margin = r_us - r_opp
        
        return {
            "treatment": t_key,
            "opponent": opp_key,
            "seed": seed,
            "swapped": swapped,
            "reward_us": r_us,
            "reward_opp": r_opp,
            "margin": margin,
            "won": won,
            "q3_step": q3_step if q3_step != -1 else 720,
            "final_cows": final_cows,
            "final_sheep": final_sheep,
            "wheat_bought": total_wheat_bought,
            "milk_sold": total_milk_sold,
            "starvation_events": starvation_events,
            "invalid_actions": invalid_actions,
            "cp_cash": cp_cash,
            "cp_quads": cp_quads,
            "elapsed": elapsed
        }
    except Exception as e:
        return {
            "treatment": t_key,
            "opponent": opp_key,
            "seed": seed,
            "swapped": swapped,
            "error": str(e),
            "reward_us": 0.0,
            "reward_opp": 0.0,
            "margin": 0.0,
            "won": 0,
            "q3_step": 720,
            "final_cows": 0,
            "final_sheep": 0,
            "wheat_bought": 0,
            "milk_sold": 0,
            "starvation_events": 0,
            "invalid_actions": 1,
            "cp_cash": {},
            "cp_quads": {},
            "elapsed": 0
        }

def run_study(seeds=50, max_workers=None):
    if max_workers is None:
        max_workers = min(16, os.cpu_count() or 4)
        
    print(f"Starting Causal Feed Arbitrage Study: {len(TREATMENTS)} treatments x {len(OPPONENTS)} opponents x {seeds} seeds x 2 seats")
    total_matches = len(TREATMENTS) * len(OPPONENTS) * seeds * 2
    print(f"Total Matches to run: {total_matches} (Workers: {max_workers})")
    
    tasks = []
    # Use deterministic matched seed list
    seed_list = [1000 + i * 37 for i in range(seeds)]
    
    for t_key in TREATMENTS:
        for opp_key in OPPONENTS:
            for seed in seed_list:
                for swapped in [False, True]:
                    tasks.append((t_key, opp_key, seed, swapped))
                    
    t0 = time.time()
    results = []
    completed = 0
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_run_single_match, task): task for task in tasks}
        for future in as_completed(futures):
            res = future.result()
            results.append(res)
            completed += 1
            if completed % 200 == 0 or completed == total_matches:
                elapsed = time.time() - t0
                rate = completed / max(0.1, elapsed)
                print(f"Progress: {completed}/{total_matches} matches ({completed/total_matches*100:.1f}%) in {elapsed:.1f}s ({rate:.1f} matches/sec)")
                
    total_time = time.time() - t0
    print(f"\nAll {total_matches} matches completed in {total_time:.1f}s ({total_matches/total_time:.1f} matches/sec).")
    
    # Save raw results
    out_file = "scratch/feed_arbitrage_factorial_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f)
    print(f"Saved results to {out_file}")
    
    return results

if __name__ == "__main__":
    run_study(seeds=50)
