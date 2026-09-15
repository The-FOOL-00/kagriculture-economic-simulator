"""
PHASE 16 & 17: RIGOROUS 3-DATASET STATISTICAL TOURNAMENT VALIDATION
Evaluates:
1. ClosedLoopV2 vs Dmitrii
2. ClosedLoopV3 vs Dmitrii
3. ClosedLoopV3 vs ClosedLoopV2
Across three completely distinct datasets (Balanced Seats, CRN, Zero Leakage):
- Discovery: Seeds 50000 to 50049 (N=100 games)
- Qualification: Seeds 50050 to 50099 (N=100 games)
- Fresh Holdout: Seeds 50100 to 50149 (N=100 games)
Measures: Win Rate, Mean Cash, Paired Margin, 95% Confidence Interval, Worst Loss, Best Win, Catastrophic Rate.
"""
import os, sys, json, math
from typing import Dict, List, Any

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

import kagsim
import router_parent as mod_r
from closed_loop_v2 import ClosedLoopAgentV2
from closed_loop_v3 import ClosedLoopAgentV3

def ci95(data: List[float]) -> float:
    n = len(data)
    if n < 2: return 0.0
    mean = sum(data) / n
    var = sum((x - mean) ** 2 for x in data) / (n - 1)
    se = math.sqrt(var / n)
    return 1.96 * se

def evaluate_matchup(agent_cls_a, agent_cls_b, seeds: List[int], name_a: str, name_b: str) -> Dict[str, Any]:
    scores_a = []
    scores_b = []
    margins = []
    wins_a = 0
    catastrophes_a = 0
    
    for s in seeds:
        # Seat rotation 1: A as Seat 0, B as Seat 1
        g1 = kagsim.Game(s)
        pa1 = agent_cls_a()
        pb1 = agent_cls_b()
        while not g1.done:
            g1.step(pa1.act(g1.observe(0)), pb1.act(g1.observe(1)))
        ra1 = g1.reward(0); rb1 = g1.reward(1)
        scores_a.append(ra1); scores_b.append(rb1)
        margins.append(ra1 - rb1)
        if ra1 > rb1: wins_a += 1
        if ra1 < 60000: catastrophes_a += 1
        
        # Seat rotation 2: B as Seat 0, A as Seat 1
        g2 = kagsim.Game(s)
        pb2 = agent_cls_b()
        pa2 = agent_cls_a()
        while not g2.done:
            g2.step(pb2.act(g2.observe(0)), pa2.act(g2.observe(1)))
        rb2 = g2.reward(0); ra2 = g2.reward(1)
        scores_a.append(ra2); scores_b.append(rb2)
        margins.append(ra2 - rb2)
        if ra2 > rb2: wins_a += 1
        if ra2 < 60000: catastrophes_a += 1
        
    n = len(margins)
    mean_a = sum(scores_a) / n
    mean_b = sum(scores_b) / n
    margin = sum(margins) / n
    sorted_m = sorted(margins)
    median_m = sorted_m[n // 2]
    conf = ci95(margins)
    
    return {
        "matchup": f"{name_a} vs {name_b}",
        "n_games": n,
        "mean_a": round(mean_a, 2),
        "mean_b": round(mean_b, 2),
        "paired_margin": round(margin, 2),
        "ci95": round(conf, 2),
        "median_margin": round(median_m, 2),
        "win_rate": round(wins_a / n, 4),
        "worst_loss": round(min(margins), 2),
        "best_win": round(max(margins), 2),
        "catastrophic_rate": round(catastrophes_a / n, 4)
    }

def run_3dataset_tournament():
    datasets = {
        "Discovery (Seeds 50000-50049)": list(range(50000, 50050)),
        "Qualification (Seeds 50050-50099)": list(range(50050, 50100)),
        "Fresh Holdout (Seeds 50100-50149)": list(range(50100, 50150))
    }
    
    dmitrii_cls = lambda: mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
    
    all_results = {}
    for d_name, seeds in datasets.items():
        print("=" * 85, flush=True)
        print(f"RUNNING TOURNAMENT ON: {d_name} (N={len(seeds)*2} games, CRN)", flush=True)
        print("=" * 85, flush=True)
        
        # 1. ClosedLoopV2 vs Dmitrii
        print("1. Evaluating ClosedLoopV2 vs Dmitrii...", flush=True)
        res_v2_dmi = evaluate_matchup(ClosedLoopAgentV2, dmitrii_cls, seeds, "ClosedLoopV2", "Dmitrii")
        print(f"   -> Win Rate: {res_v2_dmi['win_rate']:.1%} | Margin: {res_v2_dmi['paired_margin']:+,.2f} +/- {res_v2_dmi['ci95']:.2f} | Worst: {res_v2_dmi['worst_loss']:+,.0f}", flush=True)
        
        # 2. ClosedLoopV3 vs Dmitrii
        print("2. Evaluating ClosedLoopV3 vs Dmitrii...", flush=True)
        res_v3_dmi = evaluate_matchup(ClosedLoopAgentV3, dmitrii_cls, seeds, "ClosedLoopV3", "Dmitrii")
        print(f"   -> Win Rate: {res_v3_dmi['win_rate']:.1%} | Margin: {res_v3_dmi['paired_margin']:+,.2f} +/- {res_v3_dmi['ci95']:.2f} | Worst: {res_v3_dmi['worst_loss']:+,.0f}", flush=True)
        
        # 3. ClosedLoopV3 vs ClosedLoopV2
        print("3. Evaluating ClosedLoopV3 vs ClosedLoopV2...", flush=True)
        res_v3_v2 = evaluate_matchup(ClosedLoopAgentV3, ClosedLoopAgentV2, seeds, "ClosedLoopV3", "ClosedLoopV2")
        print(f"   -> Win Rate: {res_v3_v2['win_rate']:.1%} | Margin: {res_v3_v2['paired_margin']:+,.2f} +/- {res_v3_v2['ci95']:.2f} | Worst: {res_v3_v2['worst_loss']:+,.0f}", flush=True)
        
        all_results[d_name] = [res_v2_dmi, res_v3_dmi, res_v3_v2]
        
    out_path = os.path.join(BASE_DIR, "scratch", "v3_three_dataset_validation.json")
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSaved all tournament results to {out_path}", flush=True)

if __name__ == "__main__":
    run_3dataset_tournament()
