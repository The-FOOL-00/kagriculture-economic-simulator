import os
import sys
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

import kagsim
from closed_loop_v2 import ClosedLoopAgentV2
from dev_001_dynamic_portfolio import Dev001DynamicPortfolioAgent

def inspect_match(seed):
    # Match 0
    g = kagsim.Game(seed)
    cand = Dev001DynamicPortfolioAgent()
    v2 = ClosedLoopAgentV2()
    
    while not g.done:
        o0 = g.observe(0)
        o1 = g.observe(1)
        a0 = cand.act(o0)
        a1 = v2.act(o1)
        g.step(a0, a1)
        
    print(f"=== SEED {seed} TERMINAL STATE (Match 0: Cand Seat 0 vs V2 Seat 1) ===")
    print(f"Cand Cash: {g.reward(0)}")
    print(f"V2   Cash: {g.reward(1)}")
    print(f"Cand Animals: {cand.animals_purchased if hasattr(cand, 'animals_purchased') else 'N/A'}")
    
    # Check end observation of both players
    obs0 = g.observe(0)
    obs1 = g.observe(1)
    print("Cand Shed:", obs0.get("shed", {}))
    print("V2   Shed:", obs1.get("shed", {}))
    print("Cand Farm animals:", obs0.get("farm", {}).get("animals", []))
    print("V2   Farm animals:", obs1.get("farm", {}).get("animals", []))
    print("Cand Workers (Hands):", len(obs0.get("farm", {}).get("hands", [])))
    print("V2   Workers (Hands):", len(obs1.get("farm", {}).get("hands", [])))

if __name__ == "__main__":
    inspect_match(50018)
    print("\n" + "="*50 + "\n")
    inspect_match(50004)
