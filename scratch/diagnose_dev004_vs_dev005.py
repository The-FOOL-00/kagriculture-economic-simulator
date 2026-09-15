import os
import sys
import json
import csv
import importlib.util
import numpy as np

# Add project root
sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("./external_repos/kaggriculture-cppsim"))

import kagsim
from candidates.closed_loop_architecture.dev_004_joint_macro_scheduler import Dev004JointMacroScheduler

BASELINE_PATH = "candidates/compiled_v54_plus_residual.py"

def load_isolated_baseline(module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, BASELINE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

SEEDS = list(range(247000, 247050))

print(f"Running DEV-004 on {len(SEEDS)} seeds for diagnostic comparison...")

dev004_results = {}

for i, seed in enumerate(SEEDS):
    # Match 0: DEV-004 as p0, Baseline as p1
    g0 = kagsim.Game(seed)
    cand0 = Dev004JointMacroScheduler(seat=0, seed=seed)
    base1 = load_isolated_baseline(f"base_s{seed}_m0")
    while not g0.done:
        o0 = g0.observe(0)
        o1 = g0.observe(1)
        a0 = cand0.act(o0)
        a1 = base1.agent(o1)
        g0.step(a0, a1)
    p0_cand0 = float(g0.reward(0))
    p1_base0 = float(g0.reward(1))
    d0 = p0_cand0 - p1_base0

    # Match 1: Baseline as p0, DEV-004 as p1
    g1 = kagsim.Game(seed)
    base0 = load_isolated_baseline(f"base_s{seed}_m1")
    cand1 = Dev004JointMacroScheduler(seat=1, seed=seed)
    while not g1.done:
        o0 = g1.observe(0)
        o1 = g1.observe(1)
        a0 = base0.agent(o0)
        a1 = cand1.act(o1)
        g1.step(a0, a1)
    p0_base1 = float(g1.reward(0))
    p1_cand1 = float(g1.reward(1))
    d1 = p1_cand1 - p0_base1

    mean_d = 0.5 * (d0 + d1)
    dev004_results[seed] = {
        "dev004_p0": p0_cand0,
        "base_p1": p1_base0,
        "dev004_p1": p1_cand1,
        "base_p0": p0_base1,
        "delta0": d0,
        "delta1": d1,
        "mean_delta": mean_d,
        "cand0_plan": cand0.active_plan,
        "activated": cand0.active_plan != "BASELINE_BACKBONE" or cand1.active_plan != "BASELINE_BACKBONE"
    }
    if (i + 1) % 10 == 0:
        print(f"  Processed {i+1}/{len(SEEDS)} seeds...")

# Save DEV-004 raw results
with open("scratch/dev004_raw_results.json", "w") as f:
    json.dump(dev004_results, f, indent=2)

# Load DEV-005 results
with open("experiments/EXP-DEV-005/RAW_RESULTS.json", "r") as f:
    dev005_data = json.load(f)
dev005_by_seed = {d["seed"]: d for d in dev005_data}

# Compare
comparison = []
d004_deltas = []
d005_deltas = []
diff_deltas = [] # DEV-005 - DEV-004

for s in SEEDS:
    d4 = dev004_results[s]["mean_delta"]
    d5 = dev005_by_seed[s]["paired_mean_delta"]
    d004_deltas.append(d4)
    d005_deltas.append(d5)
    diff = d5 - d4
    diff_deltas.append(diff)
    comparison.append({
        "seed": s,
        "dev004_delta": d4,
        "dev005_delta": d5,
        "dev005_minus_dev004": diff,
        "dev004_plan": dev004_results[s]["cand0_plan"],
        "dev005_plan": dev005_by_seed[s]["cand0_plan"],
        "dev004_act": dev004_results[s]["activated"],
        "dev005_act": dev005_by_seed[s]["activated"]
    })

d004_arr = np.array(d004_deltas)
d005_arr = np.array(d005_deltas)
diff_arr = np.array(diff_deltas)

print("\n" + "="*80)
print("DIAGNOSTIC COMPARISON: DEV-004 vs DEV-005 (Seeds 247000-247049)")
print("="*80)
print(f"DEV-004 Mean Delta: {np.mean(d004_arr):+.2f} | Wins: {np.sum(d004_arr > 0)} | Losses: {np.sum(d004_arr < 0)} | Ties: {np.sum(d004_arr == 0)}")
print(f"DEV-005 Mean Delta: {np.mean(d005_arr):+.2f} | Wins: {np.sum(d005_arr > 0)} | Losses: {np.sum(d005_arr < 0)} | Ties: {np.sum(d005_arr == 0)}")
print(f"DEV-005 - DEV-004 Mean: {np.mean(diff_arr):+.2f}")
print(f"Seeds where DEV-005 > DEV-004: {np.sum(diff_arr > 0)}")
print(f"Seeds where DEV-005 < DEV-004: {np.sum(diff_arr < 0)}")
print(f"Seeds where DEV-005 == DEV-004: {np.sum(diff_arr == 0)}")

divergent_seeds = [c for c in comparison if c["dev005_minus_dev004"] != 0]
print(f"\nTotal Divergent Seeds: {len(divergent_seeds)}")
for c in divergent_seeds:
    print(f"  Seed {c['seed']}: DEV-004={c['dev004_delta']:+.1f} ({c['dev004_plan']}), DEV-005={c['dev005_delta']:+.1f} ({c['dev005_plan']}) -> Diff: {c['dev005_minus_dev004']:+.1f}")

# Save comparison json
with open("scratch/dev004_vs_dev005_comparison.json", "w") as f:
    json.dump({
        "dev004_mean": float(np.mean(d004_arr)),
        "dev005_mean": float(np.mean(d005_arr)),
        "diff_mean": float(np.mean(diff_arr)),
        "divergent_seeds": divergent_seeds,
        "all_seeds": comparison
    }, f, indent=2)
print("Saved scratch/dev004_vs_dev005_comparison.json")
