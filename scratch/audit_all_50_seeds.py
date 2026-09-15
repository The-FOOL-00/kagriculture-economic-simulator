import os
import sys
import json
from collections import Counter

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

import kagsim
from closed_loop_v2 import ClosedLoopAgentV2
from dev_001_dynamic_portfolio import Dev001DynamicPortfolioAgent

raw_path = "experiments/EXP-DEV-001/EXP-DEV-001_RAW_RESULTS.json"
with open(raw_path, "r") as f:
    raw = json.load(f)

v2_runs = raw["discovery_vs_v2"]

seed_modes = {}
seed_shops_72_144 = {}
seed_divergences = {}

for r in v2_runs:
    s = r["seed"]
    pm = r["paired_margin"]
    
    g = kagsim.Game(s)
    cand = Dev001DynamicPortfolioAgent()
    v2 = ClosedLoopAgentV2()
    
    # Observe up to step 145 to see mode selection
    shops = []
    div_count = 0
    
    while not g.done:
        step = g.observe(0)["step"]
        o0 = g.observe(0)
        o1 = g.observe(1)
        
        if step == 72:
            s72 = list(o0.get("town", {}).get("unlocked_shops", []))
        if step == 144:
            s144 = list(o0.get("town", {}).get("unlocked_shops", []))
            
        a0_cand = cand.act(o0)
        a0_v2 = v2.act(o0)
        if a0_cand != a0_v2:
            div_count += 1
            
        g.step(a0_cand, a0_cand) # step doesn't matter for twin test on identical obs
        
    mode = cand.mode_selected.get(0, "STRAWBERRY")
    seed_modes[s] = mode
    seed_shops_72_144[s] = (s72, s144)
    seed_divergences[s] = div_count

print("=== SUMMARY OF ALL 50 SEEDS ===")
mode_counts = Counter(seed_modes.values())
print("Mode counts across all 50 seeds:", mode_counts)

# Breakdown of the 42 ties:
print("\n=== BREAKDOWN OF THE 42 TIES ===")
ties_by_mode = {}
for r in v2_runs:
    s = r["seed"]
    if r["paired_margin"] == 0:
        m = seed_modes[s]
        ties_by_mode.setdefault(m, []).append(s)

for m, s_list in ties_by_mode.items():
    print(f"Mode {m}: {len(s_list)} seeds -> {s_list}")

# Breakdown of the 8 non-ties:
print("\n=== BREAKDOWN OF THE 8 NON-TIES ===")
for r in v2_runs:
    s = r["seed"]
    if r["paired_margin"] != 0:
        m = seed_modes[s]
        print(f"Seed {s}: Margin={r['paired_margin']}, Mode={m}, Shops72={seed_shops_72_144[s][0]}, Shops144={seed_shops_72_144[s][1]}, DivSteps={seed_divergences[s]}")
