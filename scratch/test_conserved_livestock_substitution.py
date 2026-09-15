"""
scratch/test_conserved_livestock_substitution.py
Causal test of Lynn Sakurai's Conserved Livestock Substitution:
In non-Yarn dairy worlds (Smoothie + Ice Cream), convert the 4 mid-game Sheep in Plan 0 into 4 COWS.
Measure on the exact same 40 seeds against compiled_v54_plus_residual.
"""
import copy
import importlib.util
import json
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))

import kagsim
import compiled_v54_plus_residual
from causal_test_shop_specialization import find_target_seeds, play_match

def create_dairy_substituted_tape():
    with open(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800", "actions.json")) as f:
        tapes = json.load(f)
        
    tape0 = copy.deepcopy(tapes[0])
    
    # In tape 0, replace mid-game SHEEP purchases and placements (after step 144) with COW
    for step in range(144, 719):
        act = tape0[step]
        # Market orders
        for order in act.get("market", []):
            if order and order[0] == "BUY_ANIMAL" and len(order) >= 2 and order[1] == "SHEEP":
                order[1] = "COW"
            elif order and order[0] == "SELL" and len(order) >= 2 and order[1] == "WOOL":
                order[1] = "MILK"
        # Worker actions
        workers = [act.get("farmer", ["PASS"])] + act.get("hands", [])
        for w in workers:
            if not w: continue
            if w[0] in ("PICKUP", "PLACE") and len(w) >= 2:
                if w[1] == "SHEEP": w[1] = "COW"
                elif w[1] == "WOOL": w[1] = "MILK"
                
    return tape0

def test_substitution():
    print("Testing Conserved Livestock Substitution on Smoothie + Ice Cream worlds...")
    seeds_pairs = find_target_seeds(target_pair=("SMOOTHIE_SHOP", "ICE_CREAM_SHOP"), max_seeds=40, start=60000)
    
    DMITRII_DIR = os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800")
    spec_d = importlib.util.spec_from_file_location("dmitrii_base", os.path.join(DMITRII_DIR, "main.py"))
    mod_d = importlib.util.module_from_spec(spec_d)
    spec_d.loader.exec_module(mod_d)
    baseline_agent = mod_d.agent
    
    # Build candidate with dairy tape
    dairy_tape0 = create_dairy_substituted_tape()
    spec_r = importlib.util.spec_from_file_location("router_mod", os.path.join(DMITRII_DIR, "router_parent.py"))
    mod_r = importlib.util.module_from_spec(spec_r)
    spec_r.loader.exec_module(mod_r)
    
    class DairyPolicy(mod_r.Policy):
        def __init__(self, folder):
            super().__init__(folder)
            # Add plan 13 as dairy specialized tape
            self.tapes.append(dairy_tape0)
            
        def act(self, observation):
            step, player = int(observation["step"]), int(observation["player"])
            state = self.players.get(player)
            if state is None or step <= state.last_step:
                state = self.players[player] = mod_r.DayState()
            state.last_step = step
            
            if step == mod_r.ROUTE_STEP:
                shops = observation["town"]["unlocked_shops"]
                pair = tuple(shops[:2])
                if pair in [("SMOOTHIE_SHOP", "ICE_CREAM_SHOP"), ("ICE_CREAM_SHOP", "SMOOTHIE_SHOP")]:
                    state.plan = 13 # Dairy-specialized Plan 13
                else:
                    state.plan = mod_r.SHOP_PLANS.get(pair, 0)
            if step == mod_r.FINAL_PLAN_STEP:
                state.plan = 2
                
            view = mod_r.FarmView(observation)
            tape = self.tapes[state.plan]
            action = copy.deepcopy(tape[step])
            mod_r.repair_weeds(action, view, state, step)
            mod_r.subtract_advanced_sales(action, state, step)
            mod_r.advance_sales(action, view, state, tape, step)
            action["market"] = action["market"][:mod_r.MAX_ORDERS]
            return mod_r.liquidate(view) if step == mod_r.LAST_STEP else action
            
    dairy_policy = DairyPolicy(DMITRII_DIR)
    candidate_agent = lambda obs, cfg=None: dairy_policy.act(obs)
    
    opp_agent = compiled_v54_plus_residual.agent
    
    # Run comparison
    print(f"Running 80 matches: Baseline Plan 0 vs Dairy-Substituted Plan 13...")
    base_scores, cand_scores, opp_base, opp_cand = [], [], [], []
    base_margins, cand_margins = [], []
    base_wins, cand_wins = 0, 0
    
    for s, pair in seeds_pairs:
        # Baseline
        r0_b, r1_b = play_match(baseline_agent, opp_agent, s)
        r1_b_sw, r0_b_sw = play_match(opp_agent, baseline_agent, s)
        base_scores.extend([r0_b, r0_b_sw])
        opp_base.extend([r1_b, r1_b_sw])
        base_margins.extend([r0_b - r1_b, r0_b_sw - r1_b_sw])
        if r0_b > r1_b: base_wins += 1
        if r0_b_sw > r1_b_sw: base_wins += 1
        
        # Candidate
        r0_c, r1_c = play_match(candidate_agent, opp_agent, s)
        r1_c_sw, r0_c_sw = play_match(opp_agent, candidate_agent, s)
        cand_scores.extend([r0_c, r0_c_sw])
        opp_cand.extend([r1_c, r1_c_sw])
        cand_margins.extend([r0_c - r1_c, r0_c_sw - r1_c_sw])
        if r0_c > r1_c: cand_wins += 1
        if r0_c_sw > r1_c_sw: cand_wins += 1
        
    n = len(base_margins)
    print("\n" + "="*80)
    print("CONSERVED LIVESTOCK SUBSTITUTION RESULTS")
    print("="*80)
    print(f"Baseline Plan 0 Mean Cash        : ${sum(base_scores)/n:10,.2f} | Margin: {sum(base_margins)/n:+10,.2f} | WR: {base_wins/n*100:.1f}%")
    print(f"Dairy-Substituted Plan 13 Mean   : ${sum(cand_scores)/n:10,.2f} | Margin: {sum(cand_margins)/n:+10,.2f} | WR: {cand_wins/n*100:.1f}%")
    print(f"Direct Causal Delta (Plan 13 - 0): {sum(cand_scores)/n - sum(base_scores)/n:+10,.2f}")
    print(f"Margin Delta                     : {sum(cand_margins)/n - sum(base_margins)/n:+10,.2f}")

if __name__ == "__main__":
    test_substitution()
