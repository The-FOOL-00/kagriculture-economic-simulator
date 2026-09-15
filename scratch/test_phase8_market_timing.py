"""
PHASE 8: CAUSAL RESOLUTION OF MARKET TIMING CONTRADICTION.
Tests selling specialized tomato harvest on:
- 4k (step % 4 == 0)
- 4k+1 (step % 4 == 1)
- 4k+2 (step % 4 == 2)
- 4k+3 (step % 4 == 3)
Under:
1. IDLE opponent
2. Dmitrii opponent
3. ORiginators replay actions (Seed 50266, Pizza+Pizza)
"""
import os
import sys
import json
import copy

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

import kagsim
import router_parent as mod_r
from closed_loop_v2 import ClosedLoopAgentV2

# Load ORiginators replay actions
with open("replays/live_tournament/episode_107543042.json") as f:
    ep_orig = json.load(f)

class ReplayAgent:
    def __init__(self, ep, seat):
        self.steps = [s[seat].get("action", {}) for s in ep["steps"]]
    def act(self, obs):
        step = int(obs["step"])
        if step < len(self.steps) and self.steps[step]:
            return self.steps[step]
        return {"farmer": ["PASS"], "hands": [], "market": []}

def simulate_market_timing(timing_mod: int, opp_type: str, seed: int = 50266):
    # Simulate a tomato selling scenario
    g = kagsim.Game(seed)
    # P0 is a specialized agent that produces tomatoes and sells on step % 4 == timing_mod
    # We load ORiginators' tape as P0 or modify ClosedLoopV2
    # Let's use ORiginators' physical route for P0, but modulate the SELL step timing!
    orig_actions = [copy.deepcopy(s[1].get("action", {})) for s in ep_orig["steps"]]
    
    # Modify sell orders in orig_actions according to timing_mod
    pending_tomato_sales = 0
    modified_actions = []
    for step in range(len(orig_actions)):
        act = copy.deepcopy(orig_actions[step])
        # Strip existing tomato sales and queue them
        new_market = []
        for m in act.get("market", []):
            if m and m[0] == "SELL" and len(m) > 1 and m[1] == "TOMATO":
                pending_tomato_sales += m[2]
            else:
                new_market.append(m)
        
        # If this step matches timing_mod and we have pending sales
        if step % 4 == timing_mod and pending_tomato_sales > 0 and step >= 500:
            batch = min(pending_tomato_sales, 20)
            new_market.append(["SELL", "TOMATO", batch])
            pending_tomato_sales -= batch
            
        act["market"] = new_market
        modified_actions.append(act)
    
    # Now set opponent
    if opp_type == "IDLE":
        p1 = None
    elif opp_type == "DMITRII":
        p1 = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
    elif opp_type == "ORIGINATORS":
        p1 = ReplayAgent(ep_orig, 1)
        
    step = 0
    while not g.done:
        a0 = modified_actions[step] if step < len(modified_actions) else {"farmer": ["PASS"], "hands": [], "market": []}
        if opp_type == "IDLE":
            a1 = {"farmer": ["PASS"], "hands": [], "market": []}
        elif opp_type == "DMITRII":
            a1 = p1.act(g.observe(1))
        else:
            a1 = p1.act(g.observe(1))
        g.step(a0, a1)
        step += 1
        
    return g.reward(0), g.reward(1)

def run_phase8_experiments():
    print("=" * 70)
    print("PHASE 8: MARKET TIMING COUNTERFACTUAL EXPERIMENT")
    print("=" * 70)
    
    results = {}
    for opp in ["IDLE", "DMITRII"]:
        print(f"\n--- OPPONENT: {opp} ---")
        results[opp] = {}
        for mod in [0, 1, 2, 3]:
            # Average across 5 Pizza seeds: 50007, 50012, 50030, 50037, 50266
            seeds = [50007, 50012, 50030, 50037, 50266]
            scores_p0 = []
            scores_p1 = []
            for s in seeds:
                r0, r1 = simulate_market_timing(mod, opp, seed=s)
                scores_p0.append(r0)
                scores_p1.append(r1)
            mean_p0 = sum(scores_p0) / len(scores_p0)
            mean_p1 = sum(scores_p1) / len(scores_p1)
            margin = mean_p0 - mean_p1
            results[opp][f"4k+{mod}"] = (mean_p0, margin)
            print(f"Timing 4k+{mod} (step%4=={mod}): P0 Cash = ${mean_p0:,.0f} | Margin vs {opp} = ${margin:+,.0f}")

if __name__ == "__main__":
    run_phase8_experiments()
