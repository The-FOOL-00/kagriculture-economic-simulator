import sys, os
sys.path.insert(0, os.path.abspath("."))
import json
from collections import defaultdict
import numpy as np

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

critical_seeds = [250416, 250436, 250439]
cohort_seeds = [250400 + i for i in range(16)] # 16 test seeds

def run_simulation(seed, p0_fn, p1_fn):
    sim = FastKagricultureSim(seed=seed)
    obs = sim.reset()
    for step in range(719):
        a0 = p0_fn(obs[0], sim.configuration)
        a1 = p1_fn(obs[1], sim.configuration)
        obs, _, done, _ = sim.step([a0, a1])
        if done:
            break
    m0 = float(obs[0]["farms"][0]["money"])
    m1 = float(obs[0]["farms"][1]["money"])
    return m0, m1, m0 - m1

# Define continuation builders
def make_continuation_agent(branch_step, family, config_param=None):
    """
    Runs V49 exactly until branch_step.
    From branch_step onward, applies the specified continuation modification.
    """
    def _agent(obs, cfg=None):
        step = int(obs.get("step", 0))
        act = v49_mod.agent(obs, cfg)
        if step < branch_step:
            return act
        if not isinstance(act, dict):
            return act
            
        unlocked = obs.get("town", {}).get("unlocked_shops", [])
        has_milk_shop = any(s in ("PIZZA_SHOP", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP") for s in unlocked)
        has_wool_shop = any(s in ("TEXTILE_SHOP", "BOUTIQUE") for s in unlocked)
        
        farm = obs["farms"][obs.get("player", 0)]
        shed = farm.get("shed", {})
        shed_used = sum(shed.values())
        
        if family == "A_CONTROL":
            return act
            
        elif family == "B_DEMAND_SALE_TIMING":
            # If milk shop exists, delay selling milk unless price > threshold or shed is almost full (> 75)
            # Normal V49 sells milk as soon as it's in shed
            market_acts = act.get("market", [])
            new_market = []
            for m_op in market_acts:
                if len(m_op) >= 2 and m_op[0] == "SELL" and m_op[1] == "MILK":
                    if has_milk_shop and shed_used < 75:
                        # Check market price of milk
                        m_price = obs.get("market", {}).get("prices", {}).get("MILK", 100)
                        threshold = config_param if config_param else 120
                        if m_price < threshold:
                            continue # Hold milk for later
                new_market.append(m_op)
            return {
                "farmer": act.get("farmer", ["PASS"]),
                "hands": act.get("hands", []),
                "market": new_market
            }
            
        elif family == "C_PRODUCTION_EMPHASIS":
            # Attempt to buy additional cow at reveal step if milk shop present and cash >= 1000
            market_acts = list(act.get("market", []))
            if step == branch_step and has_milk_shop and farm.get("money", 0) >= 1200:
                # Add BUY_ANIMAL COW 1
                market_acts.append(["BUY_ANIMAL", "COW", 1])
            return {
                "farmer": act.get("farmer", ["PASS"]),
                "hands": act.get("hands", []),
                "market": market_acts
            }
            
        elif family == "D_INVENTORY_PROTECTION":
            # Keep a buffer of 3 milk in shed for shop consumption/price rebound
            market_acts = act.get("market", [])
            new_market = []
            for m_op in market_acts:
                if len(m_op) >= 3 and m_op[0] == "SELL" and m_op[1] == "MILK":
                    qty = int(m_op[2])
                    avail = shed.get("MILK", 0)
                    if has_milk_shop and avail > 0:
                        protected_qty = max(0, min(qty, avail - 3))
                        if protected_qty > 0:
                            new_market.append(["SELL", "MILK", protected_qty])
                        continue
                new_market.append(m_op)
            return {
                "farmer": act.get("farmer", ["PASS"]),
                "hands": act.get("hands", []),
                "market": new_market
            }
            
        elif family == "E_LATE_ROUTE_SUBSTITUTION":
            # At step 360+, if milk shop exists and milk price is high (>130),
            # prioritize collecting from cows over sheep if worker is near
            return act
            
        return act
        
    return _agent

print("Running V55 Counterfactual and Branch Matrix Analysis...")

# 1. Evaluate Branch Timing Matrix on Critical Seeds
branch_points = [215, 216, 217, 220, 240, 288]
branch_timing_results = []

for bp in branch_points:
    for s in critical_seeds:
        # Base
        m0_base, m1_base, marg_base = run_simulation(s, v49_mod.agent, v44_mod.agent)
        # Demand Sale Timing agent branching at bp
        agent_b = make_continuation_agent(bp, "B_DEMAND_SALE_TIMING", config_param=120)
        m0_b, m1_b, marg_b = run_simulation(s, agent_b, v44_mod.agent)
        
        branch_timing_results.append({
            "seed": s,
            "branch_step": bp,
            "family": "B_DEMAND_SALE_TIMING",
            "baseline_margin": marg_base,
            "candidate_margin": marg_b,
            "margin_delta": marg_b - marg_base
        })
        print(f"BranchStep {bp:3d} | Seed {s} | Base Margin = ${marg_base:>9.2f} | Cand = ${marg_b:>9.2f} | Delta = ${marg_b - marg_base:>+9.2f}")

with open("research/v55/counterfactuals/reveal_point_matrix.json", "w") as f:
    json.dump(branch_timing_results, f, indent=2)

# 2. Evaluate Continuation Families Matrix on Critical Seeds
continuation_families = [
    ("A_CONTROL", None),
    ("B_DEMAND_SALE_TIMING_120", ("B_DEMAND_SALE_TIMING", 120)),
    ("B_DEMAND_SALE_TIMING_140", ("B_DEMAND_SALE_TIMING", 140)),
    ("C_PRODUCTION_EMPHASIS", ("C_PRODUCTION_EMPHASIS", None)),
    ("D_INVENTORY_PROTECTION", ("D_INVENTORY_PROTECTION", None)),
]

continuation_results = []
for name, spec in continuation_families:
    fam = spec[0] if spec else "A_CONTROL"
    param = spec[1] if spec else None
    agent = make_continuation_agent(216, fam, param)
    
    for s in critical_seeds:
        m0_base, m1_base, marg_base = run_simulation(s, v49_mod.agent, v44_mod.agent)
        m0_c, m1_c, marg_c = run_simulation(s, agent, v44_mod.agent)
        continuation_results.append({
            "family_name": name,
            "family": fam,
            "param": param,
            "seed": s,
            "baseline_p0": m0_base,
            "baseline_p1": m1_base,
            "baseline_margin": marg_base,
            "candidate_p0": m0_c,
            "candidate_p1": m1_c,
            "candidate_margin": marg_c,
            "delta": marg_c - marg_base
        })
        print(f"Family: {name:<26} | Seed {s} | Delta: ${marg_c - marg_base:>+9.2f}")

with open("research/v55/counterfactuals/continuation_matrix.json", "w") as f:
    json.dump(continuation_results, f, indent=2)

print("\nMatrix runs complete. Saved reveal_point_matrix.json and continuation_matrix.json.")
