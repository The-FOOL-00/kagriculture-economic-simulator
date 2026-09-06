"""
scratch/run_overlay_benchmark.py
Comprehensive Tournament Benchmark of Guarded V2 vs Frozen V2, Aethel V1, and Live Flooder.
Evaluates 200 Dev matches, 200 Holdout matches, and 200 Opponent matches (600 total matches).
"""

import sys
sys.path.insert(0, ".")
import math
import json
import time
from multiprocessing import Pool, cpu_count
import kaggle_environments
import candidates.slot2_aethel_refined_v2 as v2
import agents.candidate_a_aethel_v1 as v1
import scratch.v2_safety_overlay as overlay

def flooder_agent(obs, config=None):
    step = int(obs.get("step", 0) or 0)
    farms = obs.get("farms", [{}, {}])
    p = int(obs.get("player", 0) or 0)
    my_farm = farms[p] if len(farms) > p else {}
    money = float(my_farm.get("money", 0) or 0)
    orders = []
    if step == 0:
        orders = [["BUY_SEED", "WHEAT", 100], ["BUY_PRODUCT", "FERTILIZER", 10], ["HIRE"]]
    elif step % 24 == 0 and money >= 250:
        orders = [["BUY_SEED", "WHEAT", 10], ["HIRE"]]
    return {"farmer": ["PASS"], "hands": [["PASS"] for _ in my_farm.get("hands", [])], "market": orders}

def simulate_match(args):
    seed, p0_type, p1_type = args
    env = kaggle_environments.make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env.reset()
    
    agent_map = {
        "guarded": overlay.V2SafetyOverlayAgent(),
        "v2": v2.agent,
        "v1": v1.agent,
        "flooder": flooder_agent
    }
    
    a0 = agent_map[p0_type]
    a1 = agent_map[p1_type]
    
    for step in range(719):
        obs0 = env.state[0].observation
        obs1 = env.state[1].observation
        act0 = a0(obs0)
        act1 = a1(obs1)
        env.step([act0, act1])
        
    r0 = float(env.steps[-1][0]["reward"])
    r1 = float(env.steps[-1][1]["reward"])
    return r0, r1


def run_suite(name, match_args, cand_is_p0_list):
    n = len(match_args)
    with Pool(processes=min(cpu_count(), 8)) as pool:
        results = pool.map(simulate_match, match_args)
        
    cand_scores = []
    opp_scores = []
    margins = []
    wins = 0.0
    
    for idx, (r0, r1) in enumerate(results):
        is_p0 = cand_is_p0_list[idx]
        c_score = r0 if is_p0 else r1
        o_score = r1 if is_p0 else r0
        margin = c_score - o_score
        cand_scores.append(c_score)
        opp_scores.append(o_score)
        margins.append(margin)
        if margin > 0: wins += 1.0
        elif margin == 0: wins += 0.5
        
    mean_cand = sum(cand_scores) / n
    mean_opp = sum(opp_scores) / n
    mean_margin = sum(margins) / n
    win_rate = (wins / n) * 100.0
    
    variance = sum((m - mean_margin) ** 2 for m in margins) / max(1, n - 1)
    std_margin = math.sqrt(variance)
    ci_95 = 1.96 * std_margin / math.sqrt(n)
    
    t_stat = mean_margin / (std_margin / math.sqrt(n)) if std_margin > 0 else 0
    p_val = math.erfc(abs(t_stat) / math.sqrt(2))
    
    # Statistical quantiles
    sorted_margins = sorted(margins)
    p5 = sorted_margins[int(0.05 * n)]
    median_margin = sorted_margins[int(0.50 * n)]
    worst_loss = sorted_margins[0]
    catastrophic_rate = sum(1 for m in margins if m < -50000) / n * 100.0
    
    print(f"\n{name} (N={n}):")
    print(f"  Guarded Score:   ${mean_cand:,.1f} | Opponent Score: ${mean_opp:,.1f}")
    print(f"  Mean Margin:     ${mean_margin:+,.1f} +/- ${ci_95:,.1f} (95% CI)")
    print(f"  Median Margin:   ${median_margin:+,.1f} | 5th Percentile: ${p5:+,.1f}")
    print(f"  Worst Loss:      ${worst_loss:+,.1f} | Catastrophic Rate: {catastrophic_rate:.1f}%")
    print(f"  Win Rate:        {win_rate:.1f}% | p-val = {p_val:.2e}")
    
    return {
        "n": n, "mean_cand": mean_cand, "mean_opp": mean_opp,
        "mean_margin": mean_margin, "median_margin": median_margin,
        "p5": p5, "worst_loss": worst_loss, "catastrophic_rate": catastrophic_rate,
        "win_rate": win_rate, "ci_95": ci_95, "p_val": p_val
    }


def main():
    print("=" * 85)
    print("V2 SAFETY OVERLAY TOURNAMENT BENCHMARK (DEV + HOLDOUT + OPPONENTS)")
    print("=" * 85)
    
    # 1. Dev Set vs Frozen V2 (100 seeds x 2 seats = 200 matches)
    dev_seeds = [10000 + i * 37 for i in range(100)]
    dev_args = []
    dev_cand_p0 = []
    for s in dev_seeds:
        dev_args.append((s, "guarded", "v2"))
        dev_cand_p0.append(True)
        dev_args.append((s, "v2", "guarded"))
        dev_cand_p0.append(False)
        
    dev_res = run_suite("1. Dev Suite vs Frozen V2", dev_args, dev_cand_p0)
    
    # 2. Frozen Holdout vs Frozen V2 (100 unseen seeds x 2 seats = 200 matches)
    holdout_seeds = [77000 + i * 43 for i in range(100)]
    holdout_args = []
    holdout_cand_p0 = []
    for s in holdout_seeds:
        holdout_args.append((s, "guarded", "v2"))
        holdout_cand_p0.append(True)
        holdout_args.append((s, "v2", "guarded"))
        holdout_cand_p0.append(False)
        
    holdout_res = run_suite("2. Frozen Holdout vs Frozen V2", holdout_args, holdout_cand_p0)
    
    # 3. Opponent Suite vs Aethel V1 (50 seeds x 2 seats = 100 matches)
    v1_seeds = [50000 + i * 31 for i in range(50)]
    v1_args = []
    v1_cand_p0 = []
    for s in v1_seeds:
        v1_args.append((s, "guarded", "v1"))
        v1_cand_p0.append(True)
        v1_args.append((s, "v1", "guarded"))
        v1_cand_p0.append(False)
        
    v1_res = run_suite("3. Opponent Suite vs Aethel V1", v1_args, v1_cand_p0)
    
    # 4. Opponent Suite vs Live Flooder (50 seeds x 2 seats = 100 matches)
    flood_seeds = [90000 + i * 19 for i in range(50)]
    flood_args = []
    flood_cand_p0 = []
    for s in flood_seeds:
        flood_args.append((s, "guarded", "flooder"))
        flood_cand_p0.append(True)
        flood_args.append((s, "flooder", "guarded"))
        flood_cand_p0.append(False)
        
    flood_res = run_suite("4. Opponent Suite vs Live Flooder", flood_args, flood_cand_p0)
    
    summary = {
        "dev_vs_v2": dev_res,
        "holdout_vs_v2": holdout_res,
        "opp_vs_v1": v1_res,
        "opp_vs_flooder": flood_res
    }
    
    with open("scratch/overlay_benchmark_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
        
    print("\nBenchmark successfully completed and saved to scratch/overlay_benchmark_summary.json.")


if __name__ == "__main__":
    main()
