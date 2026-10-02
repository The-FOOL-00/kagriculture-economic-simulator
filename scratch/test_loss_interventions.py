import sys, os
sys.path.insert(0, os.path.abspath("."))
import json

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

# The 4 losses:
# L1: 250617 Seat 0
# L2: 250617 Seat 1
# L3: 250621 Seat 0
# L4: 250621 Seat 1

losses = [
    {"name": "L1", "seed": 250617, "seat": 0, "opp_seat": 1},
    {"name": "L2", "seed": 250617, "seat": 1, "opp_seat": 0},
    {"name": "L3", "seed": 250621, "seat": 0, "opp_seat": 1},
    {"name": "L4", "seed": 250621, "seat": 1, "opp_seat": 0},
]

def run_with_intervention(seed, seat, opp_seat, intervention_fn):
    sim = FastKagricultureSim(seed=seed)
    obs = sim.reset(seed=seed)
    
    for step in range(719):
        # Baseline action
        a49 = v49_mod.agent(obs[seat])
        a44 = v44_mod.agent(obs[opp_seat])
        
        # Apply intervention
        a49 = intervention_fn(step, obs[seat], a49)
        
        obs, _, done, _ = sim.step([a49, a44] if seat == 0 else [a44, a49])
        if done: break
        
    c49 = float(obs[seat]["farms"][seat]["money"])
    c44 = float(obs[opp_seat]["farms"][opp_seat]["money"])
    return c49, c44, c49 - c44

print("Testing Micro-Interventions on Four Fresh Losses...")

# Baseline verification
for l in losses:
    c49, c44, m = run_with_intervention(l["seed"], l["seat"], l["opp_seat"], lambda s, o, a: a)
    print(f"Baseline {l['name']} (Seed {l['seed']} Seat {l['seat']}): V49=${c49:.1f}, V44=${c44:.1f}, Margin=${m:+.1f}")

# Intervention 1: Step 0 Market: What if we don't do the -124 wheat churn at step 0?
def intv_step0_skip(step, obs, act):
    if step == 0:
        return {"farmer": act.get("farmer", ["PASS"]), "hands": [], "market": []}
    return act

print("\n--- Intervention 1: Skip Step 0 Market Churn ---")
for l in losses:
    c49, c44, m = run_with_intervention(l["seed"], l["seat"], l["opp_seat"], intv_step0_skip)
    print(f"Intv 1 on {l['name']}: Margin=${m:+.1f} (Win: {m > 0})")

# Intervention 2: Step 0 Market: Match V44's 25/25 churn
def intv_step0_v44_churn(step, obs, act):
    if step == 0:
        return {"farmer": act.get("farmer", ["PASS"]), "hands": [], "market": [['BUY_PRODUCT', 'WHEAT', 25], ['SELL', 'WHEAT', 25]]}
    return act

print("\n--- Intervention 2: Match V44's 25/25 Churn at Step 0 ---")
for l in losses:
    c49, c44, m = run_with_intervention(l["seed"], l["seat"], l["opp_seat"], intv_step0_v44_churn)
    print(f"Intv 2 on {l['name']}: Margin=${m:+.1f} (Win: {m > 0})")

# Intervention 3: Endgame Step 704: Preempt strawberry sale on 250617
def intv_endgame_strawberry(step, obs, act):
    if step == 704:
        # Check if we have strawberries in shed
        shed = obs.get("private", {}).get("shed", {}) or {}
        st = shed.get("STRAWBERRY", 0)
        if st > 0:
            mkt = list(act.get("market", []))
            mkt.append(["SELL", "STRAWBERRY", min(st, 2)])
            return {"farmer": act.get("farmer", ["PASS"]), "hands": act.get("hands", []), "market": mkt}
    return act

print("\n--- Intervention 3: Endgame Strawberry Sale at Step 704 ---")
for l in losses:
    c49, c44, m = run_with_intervention(l["seed"], l["seat"], l["opp_seat"], intv_endgame_strawberry)
    print(f"Intv 3 on {l['name']}: Margin=${m:+.1f} (Win: {m > 0})")
