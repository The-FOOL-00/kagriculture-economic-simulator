import sys, os
sys.path.insert(0, os.path.abspath('.'))
import multiprocessing as mp
import kaggle_environments
import numpy as np
import scipy.stats as stats
import json

from candidates.candidate_closed_loop_execution_v1 import agent as cl_v1_agent
import candidates.slot2_aethel_refined_v2 as v2_mod
from candidates.candidate_cl_aethel_grandmaster import agent as gm_agent

# Opponents
import opponents.live_flooder_v1 as flooder
import opponents.adversarial_champion_killer as ack
import opponents.o9_market_aggressor as mkt_agg
import opponents.o10_anti_melon as anti_melon
import opponents.o12_top_meta as top_meta
import opponents.replay_whyme_labs as whyme
import opponents.replay_crop_dusta as crop_dusta

OPPONENT_REGISTRY = {
    "Live_Flooder": flooder.agent,
    "Champion_Killer": ack.agent,
    "Market_Aggressor": mkt_agg.agent,
    "Anti_Melon": anti_melon.agent,
    "Top_Meta": top_meta.agent,
    "Replay_Whyme": whyme.agent,
    "Replay_CropDusta": crop_dusta.agent,
    "Frozen_V2": v2_mod.agent,
    "Starter": kaggle_environments.environments['kaggriculture']['agents']['starter']
}

def play_match(args):
    opp_name, seed, seat = args
    opp_fn = OPPONENT_REGISTRY[opp_name]
    cand_fn = cl_v1_agent
    
    try:
        env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        if seat == 0:
            env.run([cand_fn, opp_fn])
            r_cand = float(env.steps[-1][0]["reward"] or 0)
            r_opp = float(env.steps[-1][1]["reward"] or 0)
        else:
            env.run([opp_fn, cand_fn])
            r_cand = float(env.steps[-1][1]["reward"] or 0)
            r_opp = float(env.steps[-1][0]["reward"] or 0)
            
        margin = r_cand - r_opp
        return {
            "opp": opp_name,
            "seed": seed,
            "seat": seat,
            "r_cand": r_cand,
            "r_opp": r_opp,
            "margin": margin,
            "win": 1 if margin > 0 else 0,
            "loss": 1 if margin < 0 else 0,
            "tie": 1 if margin == 0 else 0
        }
    except Exception as e:
        return {
            "opp": opp_name,
            "seed": seed,
            "seat": seat,
            "r_cand": 0.0,
            "r_opp": 0.0,
            "margin": 0.0,
            "win": 0, "loss": 1, "tie": 0, "error": str(e)
        }

def run_suite():
    opp_list = ["Live_Flooder", "Champion_Killer", "Market_Aggressor", "Anti_Melon", "Top_Meta", "Replay_Whyme", "Replay_CropDusta", "Frozen_V2", "Starter"]
    
    # 500 Dev seeds, 500 Holdout seeds
    dev_seeds = list(range(10000, 10500))
    holdout_seeds = list(range(20000, 20500))
    
    print(f"Executing Large-Scale Tournament: {len(dev_seeds)} Dev games, {len(holdout_seeds)} Holdout games...")
    
    tasks_dev = []
    for i, s in enumerate(dev_seeds):
        opp = opp_list[i % len(opp_list)]
        seat = (i // len(opp_list)) % 2
        tasks_dev.append((opp, s, seat))
        
    tasks_holdout = []
    for i, s in enumerate(holdout_seeds):
        opp = opp_list[i % len(opp_list)]
        seat = (i // len(opp_list)) % 2
        tasks_holdout.append((opp, s, seat))
        
    cpu_count = min(12, mp.cpu_count())
    print(f"Running Dev split with {cpu_count} workers...")
    with mp.Pool(processes=cpu_count) as pool:
        res_dev = pool.map(play_match, tasks_dev)
        
    print(f"Running Holdout split with {cpu_count} workers...")
    with mp.Pool(processes=cpu_count) as pool:
        res_holdout = pool.map(play_match, tasks_holdout)
        
    def aggregate_results(res_list):
        by_opp = {}
        for r in res_list:
            opp = r["opp"]
            if opp not in by_opp:
                by_opp[opp] = {"margins": [], "r_cand": [], "r_opp": [], "wins": 0, "losses": 0, "ties": 0}
            by_opp[opp]["margins"].append(r["margin"])
            by_opp[opp]["r_cand"].append(r["r_cand"])
            by_opp[opp]["r_opp"].append(r["r_opp"])
            by_opp[opp]["wins"] += r["win"]
            by_opp[opp]["losses"] += r["loss"]
            by_opp[opp]["ties"] += r["tie"]
            
        summary = {}
        for opp, d in by_opp.items():
            m = np.array(d["margins"])
            cand = np.array(d["r_cand"])
            opp_m = np.array(d["r_opp"])
            tot = len(m)
            w = d["wins"]
            l = d["losses"]
            t = d["ties"]
            mean_m = float(np.mean(m))
            median_m = float(np.median(m))
            std_m = float(np.std(m))
            ci95 = float(1.96 * std_m / np.sqrt(tot)) if tot > 1 else 0.0
            p5 = float(np.percentile(m, 5))
            p10 = float(np.percentile(m, 10))
            worst = float(np.min(m))
            
            # paired t-test
            t_stat, p_val = stats.ttest_1samp(m, 0)
            
            summary[opp] = {
                "games": tot,
                "record": f"{w}W-{l}L-{t}T",
                "win_rate": float(w / tot * 100),
                "cand_mean": float(np.mean(cand)),
                "opp_mean": float(np.mean(opp_m)),
                "mean_margin": mean_m,
                "median_margin": median_m,
                "std": std_m,
                "ci95": ci95,
                "p5": p5,
                "p10": p10,
                "worst": worst,
                "p_value": float(p_val)
            }
            print(f"  vs {opp:<18}: {summary[opp]['record']} ({summary[opp]['win_rate']:5.1f}%) | Cand Mean=${summary[opp]['cand_mean']:>8.1f} | Opp Mean=${summary[opp]['opp_mean']:>8.1f} | Margin=${mean_m:>+8.1f} +/- ${ci95:>6.1f} (p={p_val:.2e})")
        return summary
        
    print("\n--- DEVELOPMENT SPLIT SUMMARY (500 matches) ---")
    sum_dev = aggregate_results(res_dev)
    
    print("\n--- HOLDOUT SPLIT SUMMARY (500 matches) ---")
    sum_holdout = aggregate_results(res_holdout)
    
    with open('scratch/large_scale_tournament_v1_results.json', 'w') as f:
        json.dump({
            "dev_summary": sum_dev,
            "holdout_summary": sum_holdout
        }, f, indent=2)
    print("\nSaved large-scale results to scratch/large_scale_tournament_v1_results.json")

if __name__ == "__main__":
    run_suite()
