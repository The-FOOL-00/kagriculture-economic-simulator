"""
PHASE 14: ADVERSARIAL REVELATIONS STRESS TEST
Compares:
- ClosedLoopV2
- Naive Specialist (TomatoSpecialistV1)
- ClosedLoopV3 (Information-Aware Controller)
Across key adversarial and pure seeds:
1. Seed 50082: Day 6 = Farmers Market + Pizza (Adversarial Strawberry demand)
2. Seed 50097: Day 6 = Pet Cafe + Pizza, Day 9 = Ice Cream (Adversarial Strawberry demand)
3. Seed 50042: Pure Pizza + Bakery world
4. Seed 50083: Pure Pizza + Bakery world
"""
import os, sys, json
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))
sys.path.insert(0, os.path.join(BASE_DIR, "scratch"))

import kagsim
import router_parent as mod_r
from closed_loop_v2 import ClosedLoopAgentV2
from closed_loop_v3 import ClosedLoopAgentV3
from test_tomato_with_sales import TomatoSpecialistV1

def evaluate_seed(agent_cls, name, seed):
    margins = []
    scores = []
    for seat in [0, 1]:
        g = kagsim.Game(seed)
        ag = agent_cls()
        dmi = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
        if seat == 0:
            while not g.done: g.step(ag.act(g.observe(0)), dmi.act(g.observe(1)))
            r_ag = g.reward(0); r_dmi = g.reward(1)
        else:
            while not g.done: g.step(dmi.act(g.observe(0)), ag.act(g.observe(1)))
            r_ag = g.reward(1); r_dmi = g.reward(0)
        margins.append(r_ag - r_dmi)
        scores.append(r_ag)
    return sum(margins) / len(margins), sum(scores) / len(scores)

def run_adversarial_test():
    test_seeds = [
        (50082, "Adversarial: Day 6 Farmers Market + Pizza"),
        (50097, "Adversarial: Day 9 Ice Cream unlock"),
        (50042, "Pure Pizza: Pizza + Bakery world"),
        (50083, "Pure Pizza: Double Pizza + Bakery world"),
    ]
    
    print("=" * 85)
    print("PHASE 14: ADVERSARIAL REVELATIONS & CRITICAL BENCHMARK")
    print("=" * 85)
    print(f"{'Seed / Archetype':<42} | {'V2 Margin':<12} | {'Naive Spec':<12} | {'V3 Margin':<12} | {'V3 Cash'}")
    print("-" * 85)
    
    for s, desc in test_seeds:
        v2_m, v2_c = evaluate_seed(ClosedLoopAgentV2, "V2", s)
        naive_m, naive_c = evaluate_seed(TomatoSpecialistV1, "Naive", s)
        v3_m, v3_c = evaluate_seed(ClosedLoopAgentV3, "V3", s)
        print(f"Seed {s}: {desc:<34} | {v2_m:+<12,.0f} | {naive_m:+<12,.0f} | {v3_m:+<12,.0f} | ${v3_c:,.0f}")

if __name__ == "__main__":
    run_adversarial_test()
