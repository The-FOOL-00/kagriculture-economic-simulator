"""
scratch/causal_test_shop_specialization.py
Phase 7: Controlled Causal Test of Shop Specialization.
Finds seeds where non-Yarn shop pairs with high absorption occur:
Specifically: SMOOTHIE_SHOP, ICE_CREAM_SHOP, FARMERS_MARKET, PIZZA_SHOP.
Compares:
1. Baseline Dmitrii-LB2800 (which falls back to Plan 0)
2. Candidate A: Route to Plan 6 (Ice Cream specialization)
3. Candidate B: Route to Plan 8 (Smoothie specialization)
4. Candidate C: Route to Plan 11 (Smoothie specialization)
Against compiled_v54_plus_residual on identical seeds, both seats.
"""
import copy
from concurrent.futures import ProcessPoolExecutor, as_completed
import importlib.util
import json
import math
import os
import sys
import time

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))

import kagsim
import compiled_v54_plus_residual
from router_parent import SHOP_PLANS

def get_shops_for_seed(seed):
    game = kagsim.Game(seed)
    idle = {"farmer": ["PASS"], "hands": [], "market": []}
    for _ in range(145):
        game.step(idle, idle)
    obs = game.observe(0)
    unlocked = obs["town"]["unlocked_shops"]
    s0 = unlocked[0] if len(unlocked) > 0 else "NONE"
    s1 = unlocked[1] if len(unlocked) > 1 else "NONE"
    return (s0, s1)

def find_target_seeds(target_pair=("SMOOTHIE_SHOP", "ICE_CREAM_SHOP"), max_seeds=50, start=60000):
    found = []
    curr = start
    while len(found) < max_seeds and curr < start + 5000:
        pair = get_shops_for_seed(curr)
        if pair == target_pair or pair == (target_pair[1], target_pair[0]):
            found.append((curr, pair))
        curr += 1
    return found

def make_agent_with_custom_route(assigned_plan):
    import copy, json
    from pathlib import Path
    DMITRII_DIR = os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800")
    
    spec = importlib.util.spec_from_file_location("custom_dmitrii", os.path.join(DMITRII_DIR, "router_parent.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    
    class CustomPolicy(mod.Policy):
        def act(self, observation):
            step, player = int(observation["step"]), int(observation["player"])
            state = self.players.get(player)
            if state is None or step <= state.last_step:
                state = self.players[player] = mod.DayState()
            state.last_step = step
            
            if step == mod.ROUTE_STEP:
                shops = observation["town"]["unlocked_shops"]
                pair = tuple(shops[:2])
                if pair in [("SMOOTHIE_SHOP", "ICE_CREAM_SHOP"), ("ICE_CREAM_SHOP", "SMOOTHIE_SHOP")]:
                    state.plan = assigned_plan
                else:
                    state.plan = mod.SHOP_PLANS.get(pair, 0)
            if step == mod.FINAL_PLAN_STEP:
                state.plan = 2
                
            view = mod.FarmView(observation)
            tape = self.tapes[state.plan]
            action = copy.deepcopy(tape[step])
            mod.repair_weeds(action, view, state, step)
            mod.subtract_advanced_sales(action, state, step)
            mod.advance_sales(action, view, state, tape, step)
            action["market"] = action["market"][:mod.MAX_ORDERS]
            return mod.liquidate(view) if step == mod.LAST_STEP else action
            
    policy = CustomPolicy(DMITRII_DIR)
    return lambda obs, cfg=None: policy.act(obs)

def play_match(fn0, fn1, seed):
    game = kagsim.Game(seed)
    while not game.done:
        o0 = game.observe(0)
        o1 = game.observe(1)
        a0 = fn0(o0)
        a1 = fn1(o1)
        game.step(a0, a1)
    return float(game.reward(0)), float(game.reward(1))

def test_pair_candidate():
    print("Finding seeds with SMOOTHIE_SHOP + ICE_CREAM_SHOP (or vice versa)...")
    seeds_pairs = find_target_seeds(target_pair=("SMOOTHIE_SHOP", "ICE_CREAM_SHOP"), max_seeds=40, start=60000)
    print(f"Found {len(seeds_pairs)} target seeds.")
    
    # Load baseline Dmitrii
    DMITRII_DIR = os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800")
    spec_d = importlib.util.spec_from_file_location("dmitrii_base", os.path.join(DMITRII_DIR, "main.py"))
    mod_d = importlib.util.module_from_spec(spec_d)
    spec_d.loader.exec_module(mod_d)
    baseline_agent = mod_d.agent
    
    # Create candidates:
    cand_plan8 = make_agent_with_custom_route(assigned_plan=8) # Smoothie-specialized tape
    cand_plan6 = make_agent_with_custom_route(assigned_plan=6) # IceCream-specialized tape
    cand_plan11 = make_agent_with_custom_route(assigned_plan=11) # Smoothie-specialized tape 11
    
    opp_agent = compiled_v54_plus_residual.agent
    
    print("\n" + "="*85)
    print("CONTROLLED CAUSAL EXPERIMENT: SMOOTHIE_SHOP + ICE_CREAM_SHOP WORLDS")
    print(f"Matches: {len(seeds_pairs)} seeds x 2 seats = {len(seeds_pairs)*2} matches per policy")
    print("="*85)
    
    policies = [
        ("Baseline Plan 0 (Generic Fallback)", baseline_agent),
        ("Candidate Plan 8 (Smoothie Route)", cand_plan8),
        ("Candidate Plan 6 (Ice Cream Route)", cand_plan6),
        ("Candidate Plan 11 (Smoothie Route 11)", cand_plan11),
    ]
    
    summary = {}
    
    for pol_name, pol_agent in policies:
        scores_d = []
        scores_o = []
        margins = []
        wins = 0
        
        for s, pair in seeds_pairs:
            # Seat 0
            r0, r1 = play_match(pol_agent, opp_agent, s)
            m0 = r0 - r1
            scores_d.append(r0)
            scores_o.append(r1)
            margins.append(m0)
            if m0 > 0: wins += 1
            
            # Seat 1
            r1, r0 = play_match(opp_agent, pol_agent, s)
            m1 = r0 - r1
            scores_d.append(r0)
            scores_o.append(r1)
            margins.append(m1)
            if m1 > 0: wins += 1
            
        n = len(margins)
        mean_d = sum(scores_d)/n
        mean_o = sum(scores_o)/n
        mean_m = sum(margins)/n
        wr = wins/n
        
        print(f"\nPolicy: {pol_name}")
        print(f"  Mean Cash   : ${mean_d:10,.2f}")
        print(f"  Opp Mean    : ${mean_o:10,.2f}")
        print(f"  Paired Margin: {mean_m:+10,.2f}")
        print(f"  Win Rate    : {wr*100:6.2f}% ({wins}/{n})")
        
        summary[pol_name] = {
            "mean_cash": mean_d,
            "opp_cash": mean_o,
            "margin": mean_m,
            "win_rate": wr
        }
        
    out_file = os.path.join(BASE_DIR, "results", "causal_smoothie_icecream_experiment.json")
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSaved experiment results to {out_file}")

if __name__ == "__main__":
    test_pair_candidate()
