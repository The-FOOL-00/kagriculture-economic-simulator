import sys, os
sys.path.insert(0, os.path.abspath('.'))
import multiprocessing as mp
import kaggle_environments
import numpy as np
import scipy.stats as stats
import json

import candidates.slot2_aethel_refined_v2 as v2_mod
from candidates.candidate_cl_aethel_prime import agent as prime_agent
from candidates.candidate_cl_aethel_grandmaster import agent as gm_agent

# Key opponents
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
    "Starter": kaggle_environments.environments['kaggriculture']['agents']['starter']
}

def play_single_match(args):
    cand_type, opp_name, seed, seat = args
    opp_fn = OPPONENT_REGISTRY[opp_name]
    
    if cand_type == "v2": cand_fn = v2_mod.agent
    elif cand_type == "prime": cand_fn = prime_agent
    elif cand_type == "gm": cand_fn = gm_agent
    else: raise ValueError(f"Unknown cand_type {cand_type}")
    
    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    if seat == 0:
        env.run([cand_fn, opp_fn])
        r_cand = env.steps[-1][0]["reward"]
        r_opp = env.steps[-1][1]["reward"]
    else:
        env.run([opp_fn, cand_fn])
        r_cand = env.steps[-1][1]["reward"]
        r_opp = env.steps[-1][0]["reward"]
        
    margin = r_cand - r_opp
    return {
        "cand": cand_type,
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

def run_tournament():
    opp_list = ["Live_Flooder", "Champion_Killer", "Market_Aggressor", "Anti_Melon", "Top_Meta", "Replay_Whyme", "Replay_CropDusta", "Starter"]
    
    # 500 Development seeds: 10,000 to 10,499
    dev_seeds = list(range(10000, 10500))
    # 500 Holdout seeds: 20,000 to 20,499 (disjoint!)
    holdout_seeds = list(range(20000, 20500))
    
    print(f"Setting up matched tournament: {len(dev_seeds)} Dev games, {len(holdout_seeds)} Holdout games...")
    
    # We evaluate Grandmaster vs the opponents across dev and holdout
    # We also evaluate V2 as baseline benchmark
    
    tasks_dev_gm = []
    tasks_dev_v2 = []
    for i, s in enumerate(dev_seeds):
        opp = opp_list[i % len(opp_list)]
        seat = (i // len(opp_list)) % 2
        tasks_dev_gm.append(("gm", opp, s, seat))
        tasks_dev_v2.append(("v2", opp, s, seat))
        
    tasks_holdout_gm = []
    tasks_holdout_v2 = []
    for i, s in enumerate(holdout_seeds):
        opp = opp_list[i % len(opp_list)]
        seat = (i // len(opp_list)) % 2
        tasks_holdout_gm.append(("gm", opp, s, seat))
        tasks_holdout_v2.append(("v2", opp, s, seat))
        
    print(f"Running Dev Tournament (500 matches for GM, 500 matches for V2)...")
    with mp.Pool(processes=min(10, mp.cpu_count())) as pool:
        res_dev_gm = pool.map(play_single_match, tasks_dev_gm)
        res_dev_v2 = pool.map(play_single_match, tasks_dev_v2)
        
    print(f"Running Holdout Tournament (500 matches for GM, 500 matches for V2)...")
    with mp.Pool(processes=min(10, mp.cpu_count())) as pool:
        res_holdout_gm = pool.map(play_single_match, tasks_holdout_gm)
        res_holdout_v2 = pool.map(play_single_match, tasks_holdout_v2)
        
    def summarize_results(res_list, name):
        rewards = [r["r_cand"] for r in res_list]
        margins = [r["margin"] for r in res_list]
        wins = sum(r["win"] for r in res_list)
        losses = sum(r["loss"] for r in res_list)
        ties = sum(r["tie"] for r in res_list)
        n = len(res_list)
        
        mean_r = float(np.mean(rewards))
        median_r = float(np.median(rewards))
        std_r = float(np.std(rewards))
        mean_m = float(np.mean(margins))
        std_m = float(np.std(margins))
        sem_m = std_m / np.sqrt(n)
        ci95_m = (mean_m - 1.96 * sem_m, mean_m + 1.96 * sem_m)
        
        p5_r = float(np.percentile(rewards, 5))
        p10_r = float(np.percentile(rewards, 10))
        worst_r = float(np.min(rewards))
        
        # Breakdown by opponent
        by_opp = {}
        for opp in opp_list:
            sub = [r for r in res_list if r["opp"] == opp]
            if not sub: continue
            w = sum(x["win"] for x in sub)
            l = sum(x["loss"] for x in sub)
            t = sum(x["tie"] for x in sub)
            by_opp[opp] = {
                "n": len(sub),
                "W-L-T": f"{w}-{l}-{t}",
                "win_rate": w / len(sub),
                "mean_reward": float(np.mean([x["r_cand"] for x in sub])),
                "mean_margin": float(np.mean([x["margin"] for x in sub]))
            }
            
        return {
            "name": name,
            "n": n,
            "W-L-T": f"{wins}-{losses}-{ties}",
            "win_rate": wins / n,
            "mean_reward": mean_r,
            "median_reward": median_r,
            "std_reward": std_r,
            "mean_margin": mean_m,
            "std_margin": std_m,
            "ci95_margin": ci95_m,
            "p5_reward": p5_r,
            "p10_reward": p10_r,
            "worst_reward": worst_r,
            "by_opponent": by_opp
        }

    dev_gm_summary = summarize_results(res_dev_gm, "Grandmaster (Dev N=500)")
    dev_v2_summary = summarize_results(res_dev_v2, "V2 Baseline (Dev N=500)")
    holdout_gm_summary = summarize_results(res_holdout_gm, "Grandmaster (Holdout N=500)")
    holdout_v2_summary = summarize_results(res_holdout_v2, "V2 Baseline (Holdout N=500)")
    
    # Paired t-test on Dev
    gm_dev_rewards = [r["r_cand"] for r in res_dev_gm]
    v2_dev_rewards = [r["r_cand"] for r in res_dev_v2]
    t_stat_dev, p_val_dev = stats.ttest_rel(gm_dev_rewards, v2_dev_rewards)
    
    # Paired t-test on Holdout
    gm_hold_rewards = [r["r_cand"] for r in res_holdout_gm]
    v2_hold_rewards = [r["r_cand"] for r in res_holdout_v2]
    t_stat_hold, p_val_hold = stats.ttest_rel(gm_hold_rewards, v2_hold_rewards)
    
    print("\n" + "="*90)
    print("PHASE 12: LARGE-SCALE MATCHED TOURNAMENT BENCHMARK (N=1,000 GAMES)")
    print("="*90)
    print(f"DEVELOPMENT SPLIT (N=500, Seeds 10000-10499):")
    print(f"  Grandmaster : W-L-T={dev_gm_summary['W-L-T']} ({dev_gm_summary['win_rate']:.1%}) | Mean=${dev_gm_summary['mean_reward']:,.0f} | Median=${dev_gm_summary['median_reward']:,.0f} | Margin=${dev_gm_summary['mean_margin']:+,.0f} [95% CI: ${dev_gm_summary['ci95_margin'][0]:+,.0f}, ${dev_gm_summary['ci95_margin'][1]:+,.0f}]")
    print(f"                P5=${dev_gm_summary['p5_reward']:,.0f} | P10=${dev_gm_summary['p10_reward']:,.0f} | Worst=${dev_gm_summary['worst_reward']:,.0f}")
    print(f"  V2 Baseline : W-L-T={dev_v2_summary['W-L-T']} ({dev_v2_summary['win_rate']:.1%}) | Mean=${dev_v2_summary['mean_reward']:,.0f} | Median=${dev_v2_summary['median_reward']:,.0f} | Margin=${dev_v2_summary['mean_margin']:+,.0f} [95% CI: ${dev_v2_summary['ci95_margin'][0]:+,.0f}, ${dev_v2_summary['ci95_margin'][1]:+,.0f}]")
    print(f"                P5=${dev_v2_summary['p5_reward']:,.0f} | P10=${dev_v2_summary['p10_reward']:,.0f} | Worst=${dev_v2_summary['worst_reward']:,.0f}")
    print(f"  Paired t-test (GM vs V2 Dev): t={t_stat_dev:.3f}, p={p_val_dev:.2e}")
    
    print(f"\nHOLDOUT SPLIT (N=500, Disjoint Seeds 20000-20499):")
    print(f"  Grandmaster : W-L-T={holdout_gm_summary['W-L-T']} ({holdout_gm_summary['win_rate']:.1%}) | Mean=${holdout_gm_summary['mean_reward']:,.0f} | Median=${holdout_gm_summary['median_reward']:,.0f} | Margin=${holdout_gm_summary['mean_margin']:+,.0f} [95% CI: ${holdout_gm_summary['ci95_margin'][0]:+,.0f}, ${holdout_gm_summary['ci95_margin'][1]:+,.0f}]")
    print(f"                P5=${holdout_gm_summary['p5_reward']:,.0f} | P10=${holdout_gm_summary['p10_reward']:,.0f} | Worst=${holdout_gm_summary['worst_reward']:,.0f}")
    print(f"  V2 Baseline : W-L-T={holdout_v2_summary['W-L-T']} ({holdout_v2_summary['win_rate']:.1%}) | Mean=${holdout_v2_summary['mean_reward']:,.0f} | Median=${holdout_v2_summary['median_reward']:,.0f} | Margin=${holdout_v2_summary['mean_margin']:+,.0f} [95% CI: ${holdout_v2_summary['ci95_margin'][0]:+,.0f}, ${holdout_v2_summary['ci95_margin'][1]:+,.0f}]")
    print(f"                P5=${holdout_v2_summary['p5_reward']:,.0f} | P10=${holdout_v2_summary['p10_reward']:,.0f} | Worst=${holdout_v2_summary['worst_reward']:,.0f}")
    print(f"  Paired t-test (GM vs V2 Holdout): t={t_stat_hold:.3f}, p={p_val_hold:.2e}")

    full_report = {
        "dev": {"gm": dev_gm_summary, "v2": dev_v2_summary, "p_value": float(p_val_dev)},
        "holdout": {"gm": holdout_gm_summary, "v2": holdout_v2_summary, "p_value": float(p_val_hold)}
    }
    with open("scratch/large_scale_tournament_results.json", "w") as f:
        json.dump(full_report, f, indent=2)
    print("\nSaved full tournament results to scratch/large_scale_tournament_results.json")

if __name__ == '__main__':
    run_tournament()
