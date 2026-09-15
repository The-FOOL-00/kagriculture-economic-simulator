import copy
import json
import os
import sys
import math

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates"))

import kagsim
import router_parent as mod_r
import compiled_v54_plus_residual as v54

def benchmark_dairy_continuation():
    print("=" * 80)
    print("STEP 6: DISCOVERY EXPERIMENT: NEW DAIRY CONTINUATION VS DMITRII PLAN 0")
    print("Target World: SMOOTHIE_SHOP + ICE_CREAM_SHOP / ICE_CREAM_SHOP + SMOOTHIE_SHOP")
    print("=" * 80)
    
    # Load dairy tape
    dairy_tape = json.load(open("scratch/dairy_specialized_tape.json"))
    
    # Load dairy seeds
    seeds_data = json.load(open("scratch/shop_world_seeds.json"))
    dairy_seeds = seeds_data["SMOOTHIE_SHOP+ICE_CREAM_SHOP"] + seeds_data.get("ICE_CREAM_SHOP+SMOOTHIE_SHOP", [])
    
    n_seeds = min(50, len(dairy_seeds))
    test_seeds = dairy_seeds[:n_seeds]
    print(f"Running {n_seeds} paired seeds, both seats = {2 * n_seeds} competitive matches...")
    
    results_base = []
    results_candidate = []
    v54_base = []
    v54_cand = []
    
    # Candidate Policy that routes Dairy pairs to Plan 13
    class CandidateDairyPolicy(mod_r.Policy):
        def __init__(self, folder):
            super().__init__(folder)
            self.tapes.append(dairy_tape) # Plan 13
            
        def act(self, observation):
            step = int(observation["step"])
            player = int(observation["player"])
            state = self.players.get(player)
            if state is None or step <= state.last_step:
                state = self.players[player] = mod_r.DayState()
            state.last_step = step
            
            if step == mod_r.ROUTE_STEP:
                shops = observation["town"]["unlocked_shops"]
                pair = tuple(shops[:2])
                if pair in (("SMOOTHIE_SHOP", "ICE_CREAM_SHOP"), ("ICE_CREAM_SHOP", "SMOOTHIE_SHOP")):
                    state.plan = 13 # Candidate Dairy Continuation!
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

    for idx, s in enumerate(test_seeds):
        # 1. Baseline: Dmitrii Base vs V54
        # Seat 0
        pb0 = mod_r.Policy("extracted_agents/dmitrii_lb2800")
        g0 = kagsim.Game(s)
        while not g0.done: g0.step(pb0.act(g0.observe(0)), v54.agent(g0.observe(1)))
        results_base.append(g0.reward(0))
        v54_base.append(g0.reward(1))
        
        # Seat 1
        pb1 = mod_r.Policy("extracted_agents/dmitrii_lb2800")
        g1 = kagsim.Game(s)
        while not g1.done: g1.step(v54.agent(g1.observe(0)), pb1.act(g1.observe(1)))
        results_base.append(g1.reward(1))
        v54_base.append(g1.reward(0))
        
        # 2. Candidate: Candidate Policy vs V54
        # Seat 0
        pc0 = CandidateDairyPolicy("extracted_agents/dmitrii_lb2800")
        g2 = kagsim.Game(s)
        while not g2.done: g2.step(pc0.act(g2.observe(0)), v54.agent(g2.observe(1)))
        results_candidate.append(g2.reward(0))
        v54_cand.append(g2.reward(1))
        
        # Seat 1
        pc1 = CandidateDairyPolicy("extracted_agents/dmitrii_lb2800")
        g3 = kagsim.Game(s)
        while not g3.done: g3.step(v54.agent(g3.observe(0)), pc1.act(g3.observe(1)))
        results_candidate.append(g3.reward(1))
        v54_cand.append(g3.reward(0))

    n_matches = len(results_base)
    
    mean_base = sum(results_base) / n_matches
    mean_cand = sum(results_candidate) / n_matches
    delta = mean_cand - mean_base
    
    diffs = [c - b for c, b in zip(results_candidate, results_base)]
    diffs.sort()
    median_diff = diffs[n_matches // 2]
    
    # 95% CI on paired delta
    var_diff = sum((d - delta) ** 2 for d in diffs) / (n_matches - 1)
    std_diff = math.sqrt(var_diff)
    se_diff = std_diff / math.sqrt(n_matches)
    ci95_lower = delta - 1.96 * se_diff
    ci95_upper = delta + 1.96 * se_diff
    
    wins = sum(1 for c, b in zip(results_candidate, results_base) if c > b)
    ties = sum(1 for c, b in zip(results_candidate, results_base) if c == b)
    losses = sum(1 for c, b in zip(results_candidate, results_base) if c < b)
    
    # Candidate vs V54 win rate
    cand_wins_v54 = sum(1 for c, v in zip(results_candidate, v54_cand) if c > v)
    base_wins_v54 = sum(1 for b, v in zip(results_base, v54_base) if b > v)
    
    print(f"\nRESULTS OVER {n_matches} MATCHES ({n_seeds} SEEDS, BOTH SEATS):")
    print(f"  Dmitrii Base Mean Cash:     ${mean_base:,.2f}")
    print(f"  Candidate Dairy Mean Cash:  ${mean_cand:,.2f}")
    print(f"  Net Paired Delta:           ${delta:+,.2f}")
    print(f"  Median Delta:               ${median_diff:+,.2f}")
    print(f"  95% Confidence Interval:    [${ci95_lower:+,.2f}, ${ci95_upper:+,.2f}]")
    print(f"  Candidate vs Base Record:   {wins}W / {ties}T / {losses}L (Win Rate: {wins/n_matches*100:.1f}%)")
    print(f"  Candidate vs V54 Win Rate:  {cand_wins_v54}/{n_matches} ({cand_wins_v54/n_matches*100:.1f}%) vs Base {base_wins_v54}/{n_matches} ({base_wins_v54/n_matches*100:.1f}%)")
    print(f"  Worst Delta:                ${min(diffs):+,.2f}")
    print(f"  Best Delta:                 ${max(diffs):+,.2f}")
    
    # Tail probabilities
    p_neg_1k = sum(1 for d in diffs if d < -1000) / n_matches * 100
    p_pos_1k = sum(1 for d in diffs if d > 1000) / n_matches * 100
    p_pos_5k = sum(1 for d in diffs if d > 5000) / n_matches * 100
    print(f"  P(Delta < -$1,000):         {p_neg_1k:.1f}%")
    print(f"  P(Delta > +$1,000):         {p_pos_1k:.1f}%")
    print(f"  P(Delta > +$5,000):         {p_pos_5k:.1f}%")

if __name__ == "__main__":
    benchmark_dairy_continuation()
