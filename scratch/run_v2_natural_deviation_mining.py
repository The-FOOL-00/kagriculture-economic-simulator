"""
scratch/run_v2_natural_deviation_mining.py
=============================================================================
Phase 1 & Phase 2: Natural Deviation Mining & Taxonomy Classification
=============================================================================
Runs 500 complete games across diverse matchups and seeds:
- V2 vs Starter (200 matches)
- V2 vs V2 Mirror (100 matches)
- V2 vs Live Flooder (100 matches)
- V2 vs Aethel V1 (50 matches)
- V2 vs Top Meta Replay/Bot (50 matches)

Uses non-invasive callback instrumentation to capture exact turn-by-turn
state and deviations without runner artifacts.
=============================================================================
"""

import sys
import os
sys.path.insert(0, os.path.abspath("."))

import time
import json
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np

import kaggle_environments
import candidates.slot2_aethel_refined_v2 as v2
import agents.candidate_a_aethel_v1 as aethel_v1

TURNS_PER_DAY = 24
_TRACE = v2._TRACE

def get_opponent_path_or_fn(opp_name):
    if opp_name == "starter":
        return None # Built-in default
    elif opp_name == "v2":
        return "candidates/slot2_aethel_refined_v2.py"
    elif opp_name == "aethel_v1":
        return "agents/candidate_a_aethel_v1.py"
    elif opp_name == "live_flooder":
        return "opponents/live_flooder_v1.py"
    elif opp_name == "top_meta":
        return "opponents/o12_top_meta.py"
    return None

def analyze_single_game(args):
    seed, opp_name, player_slot = args
    cfg = {"seed": seed, "episodeSteps": 720}
    env = kaggle_environments.make("kaggriculture", configuration=cfg, debug=False)

    game_deviations = []
    step_telemetry = []

    # State tracking
    def instrumented_v2_agent(obs, config=None):
        step = int(obs.get("step", 0) or 0)
        player = int(obs.get("player", 0) or 0)
        farm = (obs.get("farms") or [{}])[player]
        private = obs.get("private") or {}
        market = obs.get("market") or {}
        prices = market.get("prices") or {}
        
        day = step // TURNS_PER_DAY
        hour = step % TURNS_PER_DAY
        
        money = float(farm.get("money", 0))
        farmer_pos = tuple(farm.get("farmer", [4, 4]))
        hands = [tuple(h) for h in farm.get("hands", [])]
        all_workers = [farmer_pos] + hands
        tiles = farm.get("tiles") or []
        unlocked = farm.get("unlocked_quadrants") or []
        
        # Call V2 agent to get action
        act = v2.agent(obs, config)
        trace_act = _TRACE[step] if step < len(_TRACE) else {}
        
        # 1. Check Land Unlock Timing
        if step == 169 and len(unlocked) < 2:
            game_deviations.append({
                "type": "D3",
                "category": "delayed_land_unlock_1",
                "step": step,
                "day": day,
                "hour": hour,
                "detail": f"Quadrant NE not unlocked after step 168 (unlocked: {unlocked})"
            })
        if step == 256 and len(unlocked) < 3:
            game_deviations.append({
                "type": "D3",
                "category": "delayed_land_unlock_2",
                "step": step,
                "day": day,
                "hour": hour,
                "detail": f"Quadrant SW not unlocked after step 255 (unlocked: {unlocked})"
            })

        # 2. Check Crop Growth & Watering Health
        if hour == 23 and tiles:
            for r_idx, row in enumerate(tiles):
                for c_idx, t in enumerate(row):
                    if isinstance(t, dict) and t.get("kind") == "PLANT":
                        consec_unwatered = t.get("consecutive_unwatered", 0)
                        if consec_unwatered >= 2: # At risk of withering/stalling
                            game_deviations.append({
                                "type": "D4",
                                "category": "critical_unwatered_crop",
                                "step": step,
                                "day": day,
                                "hour": hour,
                                "pos": f"{c_idx},{r_idx}",
                                "crop": t.get("crop"),
                                "consec": consec_unwatered,
                                "detail": f"{t.get('crop')} at ({c_idx},{r_idx}) unwatered for {consec_unwatered} consecutive days"
                            })

        # 3. Check Livestock Starvation / Health
        if hour == 23 and tiles:
            for r_idx, row in enumerate(tiles):
                for c_idx, t in enumerate(row):
                    if isinstance(t, dict) and t.get("kind") == "PASTURE":
                        animal = t.get("animal")
                        consec_unfed = t.get("consecutive_unfed", 0)
                        if animal and consec_unfed >= 2: # At risk of starvation
                            game_deviations.append({
                                "type": "D6",
                                "category": "critical_unfed_livestock",
                                "step": step,
                                "day": day,
                                "hour": hour,
                                "pos": f"{c_idx},{r_idx}",
                                "animal": animal,
                                "consec": consec_unfed,
                                "detail": f"{animal} at ({c_idx},{r_idx}) unfed for {consec_unfed} consecutive days"
                            })

        # 4. Check Liquidity Shortfall for Critical Buys
        if trace_act.get("market") and step in (0, 24, 168, 255):
            for order in trace_act.get("market", []):
                if isinstance(order, list) and len(order) >= 3 and order[0].startswith("BUY"):
                    item = order[1]
                    qty = int(order[2])
                    cost_est = prices.get(item, 0) * qty
                    if money < cost_est:
                        game_deviations.append({
                            "type": "D8",
                            "category": "critical_buy_liquidity_shortfall",
                            "step": step,
                            "day": day,
                            "hour": hour,
                            "item": item,
                            "qty": qty,
                            "money": money,
                            "cost_est": cost_est,
                            "detail": f"Cash ${money:.1f} < cost ${cost_est:.1f} for planned {item} x{qty} at step {step}"
                        })

        return act

    opp_arg = get_opponent_path_or_fn(opp_name)
    agents_list = [instrumented_v2_agent, opp_arg] if player_slot == 0 else [opp_arg, instrumented_v2_agent]

    try:
        env.run(agents_list)
        final_step = env.steps[-1]
        raw_r0 = float(final_step[0].reward or 0.0)
        raw_r1 = float(final_step[1].reward or 0.0)
        v2_score = raw_r0 if player_slot == 0 else raw_r1
        opp_score = raw_r1 if player_slot == 0 else raw_r0
        margin = v2_score - opp_score
        win = 1 if margin > 0 else (0 if margin == 0 else -1)
    except Exception as e:
        print(f"Error in game seed {seed}: {e}")
        traceback.print_exc()
        v2_score, opp_score, margin, win = 0.0, 0.0, 0.0, -1

    return {
        "seed": seed,
        "opp_name": opp_name,
        "player_slot": player_slot,
        "v2_score": v2_score,
        "opp_score": opp_score,
        "margin": margin,
        "win": win,
        "deviation_count": len(game_deviations),
        "deviations": game_deviations
    }

def run_mining_suite(num_games=500, max_workers=6):
    print("=" * 80)
    print(f"STARTING V2 NATURAL DEVIATION MINING SUITE ({num_games} complete games)")
    print("=" * 80)

    tasks = []
    base_seed = 1000
    
    # 200 Starter
    for i in range(200):
        tasks.append((base_seed + i, "starter", i % 2))
    
    # 100 V2 Mirror
    for i in range(100):
        tasks.append((base_seed + 200 + i, "v2", i % 2))
        
    # 100 Live Flooder
    for i in range(100):
        tasks.append((base_seed + 300 + i, "live_flooder", i % 2))
        
    # 50 Aethel V1
    for i in range(50):
        tasks.append((base_seed + 400 + i, "aethel_v1", i % 2))
        
    # 50 Top Meta
    for i in range(50):
        tasks.append((base_seed + 450 + i, "top_meta", i % 2))

    t_start = time.time()
    results = []
    completed = 0

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(analyze_single_game, t) for t in tasks]
        for f in as_completed(futures):
            try:
                res = f.result()
                results.append(res)
            except Exception as e:
                print(f"Error in match: {e}")
            completed += 1
            if completed % 50 == 0 or completed == len(tasks):
                elapsed = time.time() - t_start
                rate = completed / elapsed
                print(f"Mined {completed}/{len(tasks)} games ({completed/len(tasks)*100:.1f}%) | {rate:.2f} games/s | Elapsed: {elapsed:.1f}s")

    total_time = time.time() - t_start
    print(f"\nCompleted {len(results)} matches in {total_time:.2f}s ({len(results)/total_time:.2f} games/s)")

    out_path = "scratch/natural_deviations_500games.json"
    with open(out_path, "w") as fp:
        json.dump(results, fp, indent=2)
    print(f"Saved raw mined telemetry to {out_path}")

    return results

if __name__ == "__main__":
    run_mining_suite(num_games=500, max_workers=6)
