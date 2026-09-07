import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
import json
import numpy as np
from concurrent.futures import ProcessPoolExecutor
from scipy import stats

OPPONENT_PATHS = [
    ("Live_Flooder", "opponents/live_flooder_v1.py"),
    ("Champion_Killer", "opponents/adversarial_champion_killer.py"),
    ("Market_Aggressor", "opponents/o9_market_aggressor.py"),
    ("Anti_Melon", "opponents/o10_anti_melon.py"),
    ("Top_Meta", "opponents/o12_top_meta.py"),
    ("Replay_Whyme", "opponents/replay_whyme_labs.py"),
    ("Replay_CropDusta", "opponents/replay_crop_dusta.py"),
    ("Starter", "starter")
]

DEV_SEEDS = list(range(10000, 10500))      # 500 seeds
HOLDOUT_SEEDS = list(range(20000, 20500))  # 500 seeds

def run_single_eval(agent_path, opp_path, seed, seat):
    if seat == 0:
        p0, p1 = agent_path, opp_path
    else:
        p0, p1 = opp_path, agent_path
        
    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.run([p0, p1])
    r0 = env.steps[-1][0]["reward"]
    r1 = env.steps[-1][1]["reward"]
    
    agent_reward = r0 if seat == 0 else r1
    opp_reward = r1 if seat == 0 else r0
    margin = agent_reward - opp_reward
    return agent_reward, opp_reward, margin

def phase16_worker(task):
    a_path, o_path, s, seat, o_name = task
    ar, or_, m = run_single_eval(a_path, o_path, s, seat)
    return o_name, ar, or_, m

def eval_tournament_split(split_name, seeds, agent_name, agent_path):
    print(f"\n--- Running Split: {split_name} (N={len(seeds)}) for {agent_name} ---")
    tasks = []
    n_opps = len(OPPONENT_PATHS)
    for i, seed in enumerate(seeds):
        opp_name, opp_path = OPPONENT_PATHS[i % n_opps]
        seat = i % 2
        tasks.append((agent_path, opp_path, seed, seat, opp_name))
        
    results_by_opp = {name: {"rewards": [], "margins": [], "wins": 0, "losses": 0, "ties": 0} for name, _ in OPPONENT_PATHS}
    all_rewards = []
    all_margins = []
    
    with ProcessPoolExecutor(max_workers=8) as executor:
        for o_name, ar, or_, m in executor.map(phase16_worker, tasks):
            results_by_opp[o_name]["rewards"].append(ar)
            results_by_opp[o_name]["margins"].append(m)
            if m > 0: results_by_opp[o_name]["wins"] += 1
            elif m < 0: results_by_opp[o_name]["losses"] += 1
            else: results_by_opp[o_name]["ties"] += 1
            all_rewards.append(ar)
            all_margins.append(m)
            
    total_wins = sum(d["wins"] for d in results_by_opp.values())
    total_losses = sum(d["losses"] for d in results_by_opp.values())
    total_ties = sum(d["ties"] for d in results_by_opp.values())
    n = len(all_rewards)
    
    mean_r = float(np.mean(all_rewards))
    median_r = float(np.median(all_rewards))
    std_r = float(np.std(all_rewards))
    mean_m = float(np.mean(all_margins))
    std_m = float(np.std(all_margins))
    ci95_m = [float(mean_m - 1.96 * std_m / np.sqrt(n)), float(mean_m + 1.96 * std_m / np.sqrt(n))]
    p5_r = float(np.percentile(all_rewards, 5))
    p10_r = float(np.percentile(all_rewards, 10))
    worst_r = float(np.min(all_rewards))
    
    summary = {
        "name": f"{agent_name} ({split_name} N={n})",
        "n": n,
        "W-L-T": f"{total_wins}-{total_losses}-{total_ties}",
        "win_rate": total_wins / n,
        "mean_reward": mean_r,
        "median_reward": median_r,
        "std_reward": std_r,
        "mean_margin": mean_m,
        "std_margin": std_m,
        "ci95_margin": ci95_m,
        "p5_reward": p5_r,
        "p10_reward": p10_r,
        "worst_reward": worst_r,
        "all_rewards": all_rewards,
        "all_margins": all_margins,
        "by_opponent": {}
    }
    
    for o_name, d in results_by_opp.items():
        summary["by_opponent"][o_name] = {
            "n": len(d["rewards"]),
            "W-L-T": f"{d['wins']}-{d['losses']}-{d['ties']}",
            "win_rate": d["wins"] / len(d["rewards"]),
            "mean_reward": float(np.mean(d["rewards"])),
            "mean_margin": float(np.mean(d["margins"]))
        }
        
    print(f"  {agent_name} {split_name}: W-L-T={summary['W-L-T']}, Mean=${mean_r:.2f}, Median=${median_r:.2f}, Margin=+${mean_m:.2f} [95% CI: ${ci95_m[0]:.2f}, ${ci95_m[1]:.2f}]")
    return summary

def run_phase16():
    print("================================================================================")
    print("PHASE 16: LARGE-SCALE 1,000-GAME TOURNAMENT (500 DEV + 500 HOLDOUT)")
    print("================================================================================")
    
    dev_ov = eval_tournament_split("Dev", DEV_SEEDS, "Adaptive Overlay", "candidates/candidate_v2_adaptive_overlay.py")
    dev_v2 = eval_tournament_split("Dev", DEV_SEEDS, "V2 Baseline", "candidates/slot2_aethel_refined_v2.py")
    
    holdout_ov = eval_tournament_split("Holdout", HOLDOUT_SEEDS, "Adaptive Overlay", "candidates/candidate_v2_adaptive_overlay.py")
    holdout_v2 = eval_tournament_split("Holdout", HOLDOUT_SEEDS, "V2 Baseline", "candidates/slot2_aethel_refined_v2.py")
    
    t_dev, p_dev = stats.ttest_rel(dev_ov["all_rewards"], dev_v2["all_rewards"])
    t_hold, p_hold = stats.ttest_rel(holdout_ov["all_rewards"], holdout_v2["all_rewards"])
    
    print(f"\nPaired t-test Dev    : t = {t_dev:.3f}, p = {p_dev:.4e}")
    print(f"Paired t-test Holdout: t = {t_hold:.3f}, p = {p_hold:.4e}")
    
    results = {
        "dev": {"overlay": dev_ov, "v2": dev_v2, "t_stat": float(t_dev), "p_value": float(p_dev)},
        "holdout": {"overlay": holdout_ov, "v2": holdout_v2, "t_stat": float(t_hold), "p_value": float(p_hold)}
    }
    
    with open('scratch/overlay_phase16_tournament_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    return results

if __name__ == '__main__':
    run_phase16()
