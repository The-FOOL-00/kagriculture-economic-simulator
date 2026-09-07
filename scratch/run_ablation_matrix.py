import sys, os
sys.path.insert(0, os.path.abspath('.'))
import copy
import json
import kaggle_environments
import numpy as np

import candidates.slot2_aethel_refined_v2 as v2_mod
from candidates.candidate_cl_aethel_prime import agent as prime_agent

SEEDS = [42, 100, 2024]

def eval_agent(agent_fn, seeds=SEEDS, opp_name="starter"):
    scores = []
    opp_scores = []
    for s in seeds:
        env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": s})
        opp_fn = kaggle_environments.environments['kaggriculture']['agents'][opp_name]
        env.run([agent_fn, opp_fn])
        scores.append(env.steps[-1][0]['reward'])
        opp_scores.append(env.steps[-1][1]['reward'])
    return float(np.mean(scores)), float(np.std(scores)), scores

# --- ABLATIONS ON V2 ---

# Baseline V2
def run_v2_baseline():
    return v2_mod.agent

# Ablation V2-A: No Market Controller (Raw Trace)
def make_v2_no_market_controller():
    def agent(obs, config=None):
        step = min(int(obs.get("step", 0) or 0), len(v2_mod._TRACE) - 1)
        if step >= v2_mod._TERMINAL_START_STEP:
            return v2_mod._terminal_action(obs)
        return copy.deepcopy(v2_mod._TRACE[step])
    return agent

# Ablation V2-B: Reduced Hiring (Cap hiring to 4 hands max)
def make_v2_reduced_hiring():
    def agent(obs, config=None):
        act = v2_mod.agent(obs, config)
        step = int(obs.get("step", 0) or 0)
        # Suppress HIRE orders beyond 4 hands
        farm = (obs.get("farms") or [{}])[0]
        hands_count = len(farm.get("hands", []))
        hires_today = int(farm.get("hires_today", 0) or 0)
        if "market" in act:
            filtered_m = []
            for o in act["market"]:
                if isinstance(o, list) and o and o[0] == "HIRE":
                    if hands_count + hires_today >= 4:
                        continue
                filtered_m.append(o)
            act["market"] = filtered_m
        return act
    return agent

# Ablation V2-C: No Terminal Liquidation Net (Steps 712-720 keep running trace or pass)
def make_v2_no_terminal():
    def agent(obs, config=None):
        step = min(int(obs.get("step", 0) or 0), len(v2_mod._TRACE) - 1)
        # Disable terminal liquidation
        action = copy.deepcopy(v2_mod._TRACE[step])
        return action
    return agent

# Ablation V2-D: Premature Melon Harvest (Harvest melons on Day 10 at yield=1 instead of yield=6)
# (In trace, melon harvest is step 249-264; if yield was 1, reward is much lower)

# --- ABLATIONS ON PRIME ---

# Baseline Prime
def run_prime_baseline():
    return prime_agent

# Ablation Prime-A: Scaled Hiring (Prime hires up to 6 on D0, 8 on D4, 12 on D10)
from candidates.candidate_cl_aethel_prime import CLAethelPrime, _fib

class PrimeWithV2Hiring(CLAethelPrime):
    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)
        # Replace hiring logic with aggressive hiring
        # Target hands: Day 0: 5, Day 1-3: 4, Day 4-6: 6, Day 7-9: 8, Day 10+: 12
        if day == 0: target = 5
        elif day < 4: target = 4
        elif day < 7: target = 6
        elif day < 10: target = 8
        else: target = 12
        
        # Strip existing HIRE orders from orders
        orders = [o for o in orders if not (isinstance(o, list) and o and o[0] == "HIRE")]
        cur_h = hired
        budget = money
        while cur_h < target and len(orders) < 10:
            cost = _fib(cur_h)
            if budget >= cost:
                orders.append(["HIRE"])
                budget -= cost
                cur_h += 1
            else:
                break
        return orders[:10]

# Ablation Prime-B: Guarded Melon Harvest (Wait until yield == 6)
class PrimeGuardedHarvest(CLAethelPrime):
    def _dispatch_workers(self, all_workers, all_invs, tiles, shed, seeds, quads, day, hour, scan_res):
        # Override local-first harvest: DO NOT harvest melon if yield < 6 and day < 28!
        actions = [None] * len(all_workers)
        claimed_tiles = set()
        ns = self._nearest_shed(all_workers[0], tiles) if hasattr(self, '_nearest_shed') else (4, 4)
        target_pasture_slots = scan_res.get("target_pasture_slots", set())
        
        # We run the standard logic but skip melon harvest if yield < 6
        # Let's inspect how CLAethelPrime dispatches
        return super()._dispatch_workers(all_workers, all_invs, tiles, shed, seeds, quads, day, hour, scan_res)

def run_all_ablations():
    print("="*80)
    print("PHASE 4 & 5: CONTROLLED ABLATIONS BENCHMARK (SEEDS 42, 100, 2024)")
    print("="*80)
    
    results = {}
    
    # 1. V2 Baseline
    m, s, raw = eval_agent(v2_mod.agent)
    results["V2_Baseline"] = {"mean": m, "std": s, "raw": raw}
    print(f"V2 Baseline:               ${m:>9,.1f} +/- {s:>7,.1f}")
    
    # 2. V2 No Market Controller
    m, s, raw = eval_agent(make_v2_no_market_controller())
    delta = m - results["V2_Baseline"]["mean"]
    results["V2_No_Market_Ctrl"] = {"mean": m, "std": s, "delta": delta}
    print(f"V2 No Market Controller:   ${m:>9,.1f} (Delta: ${delta:>+8,.1f}, {delta/results['V2_Baseline']['mean']*100:>+5.1f}%)")
    
    # 3. V2 Reduced Hiring (Cap 4)
    m, s, raw = eval_agent(make_v2_reduced_hiring())
    delta = m - results["V2_Baseline"]["mean"]
    results["V2_Cap_4_Hands"] = {"mean": m, "std": s, "delta": delta}
    print(f"V2 Cap 4 Hands:            ${m:>9,.1f} (Delta: ${delta:>+8,.1f}, {delta/results['V2_Baseline']['mean']*100:>+5.1f}%)")
    
    # 4. V2 No Terminal Action
    m, s, raw = eval_agent(make_v2_no_terminal())
    delta = m - results["V2_Baseline"]["mean"]
    results["V2_No_Terminal"] = {"mean": m, "std": s, "delta": delta}
    print(f"V2 No Terminal Net:        ${m:>9,.1f} (Delta: ${delta:>+8,.1f}, {delta/results['V2_Baseline']['mean']*100:>+5.1f}%)")
    
    # 5. Prime Baseline
    m, s, raw = eval_agent(prime_agent)
    results["Prime_Baseline"] = {"mean": m, "std": s, "raw": raw}
    print(f"\nPrime Baseline:            ${m:>9,.1f} +/- {s:>7,.1f}")
    
    # 6. Prime with Scaled Hiring
    p_hiring = PrimeWithV2Hiring()
    def p_hiring_agent(obs, cfg=None): return p_hiring(obs, cfg)
    m, s, raw = eval_agent(p_hiring_agent)
    delta = m - results["Prime_Baseline"]["mean"]
    results["Prime_Scaled_Hiring"] = {"mean": m, "std": s, "delta": delta}
    print(f"Prime + Scaled Hiring:     ${m:>9,.1f} (Delta: ${delta:>+8,.1f}, {delta/results['Prime_Baseline']['mean']*100:>+5.1f}%)")

    with open("scratch/ablation_study_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nSaved ablation results to scratch/ablation_study_results.json")

if __name__ == '__main__':
    run_all_ablations()
