import os
import sys
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))

import kagsim
from closed_loop_v2 import ClosedLoopAgentV2
from dev_001_dynamic_portfolio import Dev001DynamicPortfolioAgent

def analyze_seed(seed: int, label: str):
    print(f"\n==========================================")
    print(f"ANALYSIS OF SEED {seed} ({label})")
    print(f"==========================================")
    
    # Run Match 0: Cand (Seat 0) vs V2 (Seat 1)
    g0 = kagsim.Game(seed)
    cand0 = Dev001DynamicPortfolioAgent()
    v2_1 = ClosedLoopAgentV2()
    
    first_divergence_0 = None
    divergence_count_0 = 0
    divergences_0 = []
    
    shops_unlocked = {}
    
    step = 0
    while not g0.done:
        o0 = g0.observe(0)
        o1 = g0.observe(1)
        
        # Track shops
        unlocked = o0.get("town", {}).get("unlocked_shops", [])
        if step in [72, 144, 216, 288, 360, 432, 504, 576]:
            shops_unlocked[step] = list(unlocked)
        
        a0 = cand0.act(o0)
        a1 = v2_1.act(o1)
        
        # Now let's compare what V2 would have done if in Seat 0!
        # Create a twin V2 in Seat 0 with identical history?
        # Actually, let's see if cand0 differs from V2 acting on o0:
        v2_twin = ClosedLoopAgentV2()
        # Note: v2 is mostly state-free or has internal history?
        # Let's check if ClosedLoopAgentV2 has internal state.
        
        g0.step(a0, a1)
        step += 1

    cand_rew0 = g0.reward(0)
    v2_rew1 = g0.reward(1)
    
    print(f"Match 0: Cand(Seat 0) = {cand_rew0}, V2(Seat 1) = {v2_rew1}, Margin = {cand_rew0 - v2_rew1}")
    print(f"Shops unlocked on seed {seed}: {shops_unlocked}")
    print(f"Candidate mode at end: {cand0.mode_selected}")
    print(f"Candidate crops substituted: {cand0.crops_substituted}")

    # Now let's run baseline self-play: V2 (Seat 0) vs V2 (Seat 1)
    gv2 = kagsim.Game(seed)
    v2_0_base = ClosedLoopAgentV2()
    v2_1_base = ClosedLoopAgentV2()
    
    # Step-by-step compare cand0 actions with v2_0_base actions if given identical observations
    g_comp = kagsim.Game(seed)
    cand_comp = Dev001DynamicPortfolioAgent()
    v2_comp = ClosedLoopAgentV2()
    
    first_div = None
    all_divs = []
    
    s = 0
    while not g_comp.done:
        obs0 = g_comp.observe(0)
        obs1 = g_comp.observe(1)
        
        # What would cand do on obs0?
        act_cand = cand_comp.act(obs0)
        # What would v2 do on obs0?
        act_v2 = v2_comp.act(obs0)
        
        if act_cand != act_v2 and first_div is None:
            first_div = (s, act_cand, act_v2, obs0.get("town", {}).get("unlocked_shops", []))
            all_divs.append((s, act_cand, act_v2))
        elif act_cand != act_v2:
            all_divs.append((s, act_cand, act_v2))
            
        # Step with act_cand to see trajectory of cand
        # For opponent, let's give v2_1 action
        # Wait, in the actual match0, opponent was v2_1!
        # So g_comp will follow exact cand vs v2_1 match!
        act_opp = v2_1_base.act(obs1)
        g_comp.step(act_cand, act_opp)
        s += 1

    print(f"\nComparing Cand actions directly to V2 actions on identical states in Match 0:")
    if first_div is None:
        print("NO ACTION DIVERGENCES AT ALL! Cand was 100% identical to V2!")
    else:
        print(f"Total steps where Cand differed from V2: {len(all_divs)}")
        print(f"FIRST DIVERGENCE at Step {first_div[0]} (Day {first_div[0]//24}):")
        print(f"  Cand action: {first_div[1]}")
        print(f"  V2   action: {first_div[2]}")
        print(f"  Unlocked shops then: {first_div[3]}")
        if len(all_divs) > 1:
            print(f"First 5 divergences:")
            for d in all_divs[:5]:
                print(f"  Step {d[0]}: Cand={d[1]} | V2={d[2]}")

if __name__ == "__main__":
    analyze_seed(50018, "Worst Loss: -$2388")
    analyze_seed(50004, "Best Win: +$15264")
    analyze_seed(50001, "Win: +$192")
    analyze_seed(50017, "Small Loss: -$11")
    analyze_seed(50000, "Tie: $0")
    analyze_seed(50002, "Tie: $0")
