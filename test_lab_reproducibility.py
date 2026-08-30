import sys, os
project_root = r"c:\Users\Sundareswaran\Kagriculture"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import time
import numpy as np
from kaggle_environments import make
import importlib.util

# Load synthetic suite safely via importlib
synth_path = os.path.join(project_root, "agents", "synthetic_suite.py")
synth_spec = importlib.util.spec_from_file_location("synthetic_suite", synth_path)
synth_mod = importlib.util.module_from_spec(synth_spec)
synth_spec.loader.exec_module(synth_mod)

melon_burst_agent = synth_mod.melon_burst_agent
strawberry_rush_agent = synth_mod.strawberry_rush_agent
crop_efficient_agent = synth_mod.crop_efficient_agent
land_expansion_agent = synth_mod.land_expansion_agent
balanced_agent = synth_mod.balanced_agent

# Load previous scratch strategy lab to inspect and test
prev_scratch = r"C:\Users\Sundareswaran\.gemini\antigravity-ide\brain\1a3b82a1-c6f0-4548-874b-0e3add7eb4e8\scratch\strategies_lab.py"
spec = importlib.util.spec_from_file_location("strat_lab", prev_scratch)
strat_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(strat_mod)
StrategyFactory = strat_mod.StrategyFactory

titan_path = os.path.join(project_root, "main.py")

STRATEGIES = {
    "Titan_Production": titan_path,
    "Pure_Crop_0Animals": StrategyFactory.create_agent("PURE_CROP", target_cows=0, target_sheep=0, target_melons=20),
    "Pure_Livestock_8C4S": StrategyFactory.create_agent("PURE_LIVESTOCK", target_cows=8, target_sheep=4, target_melons=0),
    "Hybrid_8C4S_20Melon": StrategyFactory.create_agent("HYBRID", target_cows=8, target_sheep=4, target_melons=20),
    "Hybrid_6C3S_10Melon": StrategyFactory.create_agent("HYBRID", target_cows=6, target_sheep=3, target_melons=10),
    "Hybrid_6C3S_20Melon": StrategyFactory.create_agent("HYBRID", target_cows=6, target_sheep=3, target_melons=20),
    "Hybrid_6C3S_30Melon": StrategyFactory.create_agent("HYBRID", target_cows=6, target_sheep=3, target_melons=30),
    "Hybrid_4C2S_20Melon": StrategyFactory.create_agent("HYBRID", target_cows=4, target_sheep=2, target_melons=20),
}

def run_match(a0, a1, seed, swapped=False):
    cfg = {"episodeSteps": 720, "seed": seed}
    env = make("kaggriculture", configuration=cfg, debug=False)
    env.run([a0, a1])
    s = env.steps[-1]
    r0 = float(s[0].reward if s[0].reward is not None else 0.0)
    r1 = float(s[1].reward if s[1].reward is not None else 0.0)
    if swapped:
        return r1, r0
    return r0, r1

def evaluate_h2h(name0, a0, name1, a1, seeds=[1001, 1002, 1003, 1004, 1005]):
    scores0 = []
    scores1 = []
    w0, w1, ties = 0, 0, 0

    for s in seeds:
        # P0 vs P1
        r0, r1 = run_match(a0, a1, s, swapped=False)
        scores0.append(r0)
        scores1.append(r1)
        if r0 > r1: w0 += 1
        elif r1 > r0: w1 += 1
        else: ties += 1

        # P1 vs P0 (swapped)
        r0_sw, r1_sw = run_match(a1, a0, s, swapped=True)
        scores0.append(r0_sw)
        scores1.append(r1_sw)
        if r0_sw > r1_sw: w0 += 1
        elif r1_sw > r0_sw: w1 += 1
        else: ties += 1

    total = len(scores0)
    print(f"Matchup: {name0:20s} vs {name1:20s} ({total} games, seeds {seeds[0]}..{seeds[-1]})")
    print(f"  {name0} Win Rate: {w0/total*100:5.1f}% ({w0}W - {w1}L - {ties}T)")
    print(f"  {name0} Mean Cash: ${np.mean(scores0):8,.2f} | {name1} Mean Cash: ${np.mean(scores1):8,.2f}")
    print(f"  Margin: {np.mean(scores0) - np.mean(scores1):+8,.2f}\n")
    return {
        "cand": name0, "opp": name1, "games": total, "w": w0, "l": w1,
        "mean0": np.mean(scores0), "mean1": np.mean(scores1),
        "margin": np.mean(scores0) - np.mean(scores1)
    }

if __name__ == "__main__":
    print("=" * 80)
    print("PART 1 & 2: INDEPENDENT REPRODUCIBILITY BENCHMARK")
    print("=" * 80)

    # 1. Test Peer Head-to-Head
    h2h_results = []
    seeds = [10001, 10002, 10003, 10004, 10005] # 10 games per pair
    
    cand = "Hybrid_6C3S_10Melon"
    cand_agent = STRATEGIES[cand]

    for opp in ["Titan_Production", "Pure_Livestock_8C4S", "Hybrid_8C4S_20Melon", "Pure_Crop_0Animals"]:
        res = evaluate_h2h(cand, cand_agent, opp, STRATEGIES[opp], seeds=seeds)
        h2h_results.append(res)

    # 2. Benchmark against synthetic pool
    print("=" * 80)
    print("BENCHMARK ACROSS SYNTHETIC OPPONENT SUITE")
    print("=" * 80)
    synths = {
        "Melon_Burst": melon_burst_agent,
        "Crop_Efficient": crop_efficient_agent,
        "Balanced": balanced_agent,
    }
    for s_name in ["Titan_Production", "Pure_Crop_0Animals", "Pure_Livestock_8C4S", "Hybrid_8C4S_20Melon", "Hybrid_6C3S_10Melon"]:
        agent = STRATEGIES[s_name]
        print(f"\nEvaluating: {s_name}")
        scores = []
        for syn_name, syn_agent in synths.items():
            for s in [20001, 20002]:
                r0, r1 = run_match(agent, syn_agent, s, swapped=False)
                scores.append(r0)
                r0_sw, r1_sw = run_match(syn_agent, agent, s, swapped=True)
                scores.append(r0_sw)
        print(f"  --> Average Cash vs Pool ({len(scores)} games): ${np.mean(scores):8,.2f} (Median: ${np.median(scores):8,.2f})")
