"""
Full 1,000-Seed Tournament Runner (500 Dev + 500 Holdout)
=========================================================
Runs Candidate against 11 strategic archetypes & elite replays:
- 500 Development Seeds (10,000 - 10,499)
- 500 Holdout Seeds (20,000 - 20,499)
Alternates player seats (Seat 0 vs Seat 1).
"""

import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
import json
import numpy as np
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed

from candidates.slot2_aethel_refined_v2 import agent as v2_agent
from opponents.live_flooder_v1 import agent as flooder_agent
from opponents.adversarial_champion_killer import agent as killer_agent
from opponents.o9_market_aggressor import agent as aggressor_agent
from opponents.o10_anti_melon import agent as anti_melon_agent
from opponents.o12_top_meta import agent as top_meta_agent
from opponents.replay_whyme_labs import agent as whyme_agent
from opponents.replay_crop_dusta import agent as dusta_agent
from opponents.replay_kawatta_taido import agent as kawatta_agent
from opponents.replay_mtn import agent as mtn_agent
from opponents.replay_yuan800 import agent as yuan_agent

OPPONENTS = [
    ("Live Flooder", flooder_agent, "Dynamic"),
    ("Champion Killer", killer_agent, "Dynamic"),
    ("Market Aggressor", aggressor_agent, "Dynamic"),
    ("Anti-Melon", anti_melon_agent, "Dynamic"),
    ("Top Meta", top_meta_agent, "Dynamic"),
    ("Frozen V2", v2_agent, "Live Production"),
    ("Replay Whyme", whyme_agent, "Elite Replay"),
    ("Replay Kawatta", kawatta_agent, "Elite Replay"),
    ("Replay Crop Dusta", dusta_agent, "Elite Replay"),
    ("Replay MTN", mtn_agent, "Elite Replay"),
    ("Replay Yuan800", yuan_agent, "Elite Replay"),
]

def _run_single_match(item):
    cand_fn, opp_fn, opp_name, opp_cat, seed, cand_seat = item
    if cand_seat == 0:
        agents = [cand_fn, opp_fn]
    else:
        agents = [opp_fn, cand_fn]
        
    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    try:
        env.run(agents)
        steps = env.steps
        r0 = float(steps[-1][0].reward or 0.0)
        r1 = float(steps[-1][1].reward or 0.0)
        
        cand_reward = r0 if cand_seat == 0 else r1
        opp_reward = r1 if cand_seat == 0 else r0
        margin = cand_reward - opp_reward
        
        win = 1 if cand_reward > opp_reward else 0
        loss = 1 if opp_reward > cand_reward else 0
        tie = 1 if cand_reward == opp_reward else 0
        
        return {
            "opp_name": opp_name,
            "opp_cat": opp_cat,
            "seed": seed,
            "cand_reward": cand_reward,
            "opp_reward": opp_reward,
            "margin": margin,
            "win": win,
            "loss": loss,
            "tie": tie
        }
    except Exception as e:
        return {
            "opp_name": opp_name,
            "opp_cat": opp_cat,
            "seed": seed,
            "cand_reward": 0.0,
            "opp_reward": 0.0,
            "margin": 0.0,
            "win": 0,
            "loss": 1,
            "tie": 0
        }

def run_partition_tournament(cand_fn, partition_name, seeds, max_workers=12):
    tasks = []
    for opp_name, opp_fn, opp_cat in OPPONENTS:
        for i, s in enumerate(seeds):
            cand_seat = i % 2
            tasks.append((cand_fn, opp_fn, opp_name, opp_cat, s, cand_seat))
            
    print(f"\n>>> Running {partition_name} Partition: {len(tasks)} matches ({len(seeds)} seeds x {len(OPPONENTS)} opponents)...")
    results_by_opp = defaultdict(list)
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_run_single_match, t) for t in tasks]
        completed = 0
        for f in as_completed(futures):
            res = f.result()
            results_by_opp[res["opp_name"]].append(res)
            completed += 1
            if completed % max(1, len(tasks) // 10) == 0 or completed == len(tasks):
                print(f"Progress: {completed}/{len(tasks)} ({completed/len(tasks)*100:.1f}%)")
                
    summary = []
    print("\n" + "=" * 95)
    print(f"{partition_name.upper()} RESULTS SUMMARY ({len(seeds)} Seeds)")
    print("=" * 95)
    print(f"{'Opponent':<20} | {'Category':<14} | {'Matches':<7} | {'Win Rate':<9} | {'Cand Reward':<20} | {'Opp Reward':<20} | {'Margin'}")
    print("-" * 95)
    
    for opp_name, opp_fn, opp_cat in OPPONENTS:
        list_m = results_by_opp[opp_name]
        c_r = [m["cand_reward"] for m in list_m]
        o_r = [m["opp_reward"] for m in list_m]
        margins = [m["margin"] for m in list_m]
        wins = sum(m["win"] for m in list_m)
        win_rate = wins / len(list_m) * 100.0
        
        row = {
            "opp_name": opp_name,
            "opp_cat": opp_cat,
            "matches": len(list_m),
            "win_rate": win_rate,
            "cand_mean": float(np.mean(c_r)),
            "cand_std": float(np.std(c_r)),
            "opp_mean": float(np.mean(o_r)),
            "opp_std": float(np.std(o_r)),
            "margin_mean": float(np.mean(margins)),
            "margin_std": float(np.std(margins))
        }
        summary.append(row)
        print(f"{opp_name:<20} | {opp_cat:<14} | {len(list_m):<7} | {win_rate:7.1f}%  | ${np.mean(c_r):9.1f} ± ${np.std(c_r):7.1f} | ${np.mean(o_r):9.1f} ± ${np.std(o_r):7.1f} | ${np.mean(margins):+9.1f}")
        
    print("=" * 95)
    return summary

if __name__ == "__main__":
    from scratch.build_coordinated_candidate import agent as cand_fn
    dev_seeds = list(range(10000, 10500)) # 500 Dev
    holdout_seeds = list(range(20000, 20500)) # 500 Holdout
    
    dev_summary = run_partition_tournament(cand_fn, "Development (500 Seeds)", dev_seeds, max_workers=14)
    holdout_summary = run_partition_tournament(cand_fn, "Holdout (500 Seeds)", holdout_seeds, max_workers=14)
    
    with open("scratch/full_1000seed_tournament_results.json", "w") as f:
        json.dump({"dev": dev_summary, "holdout": holdout_summary}, f, indent=2)
