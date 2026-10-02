import sys, os
sys.path.insert(0, os.path.abspath("."))
import json
import numpy as np
from typing import Dict, Any, List

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v48_challenger.main as v48_mod
import candidates.v44_economic_portfolio.main as v44_mod

PROTECTED_HOLDOUTS = [(214200, 214249), (340090, 340199), (249695, 249734)]
NEAR_TIE_SEEDS = [250700 + i for i in range(128)]

for s in NEAR_TIE_SEEDS:
    for start, end in PROTECTED_HOLDOUTS:
        assert not (start <= s <= end), f"CRITICAL: Protected holdout seed {s} accessed!"

def extract_opp_dairy_state(obs: Dict[str, Any], seat: int) -> Dict[str, Any]:
    opp = 1 - seat
    farm = obs["farms"][opp]
    tiles = farm["tiles"]
    cows = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "COW")
    pastures = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("kind") == "PASTURE")
    hands = len(farm.get("hands", []))
    mkt = obs["market"]
    milk_p = mkt["prices"]["MILK"]
    egg_p = mkt["prices"]["EGG"]
    score = (cows * 1.5) + (pastures * 0.5) + (hands * 0.2) + (milk_p / 50.0)
    return {
        "cows": cows,
        "pastures": pastures,
        "hands": hands,
        "milk_price": milk_p,
        "egg_price": egg_p,
        "dairy_score": score
    }

def run_match(seed: int, seat: int, opp_name: str) -> Dict[str, Any]:
    sim = FastKagricultureSim(seed=seed)
    obs = sim.reset()
    opp_mod = v48_mod if opp_name == "V48" else v44_mod
    
    opp_state_step150 = {}
    v49_cs_decision = ""
    
    for step in range(720):
        if step == 150:
            opp_state_step150 = extract_opp_dairy_state(obs[seat], seat)
            
        if seat == 0:
            a0 = v49_mod.agent(obs[0], sim.configuration)
            a1 = opp_mod.agent(obs[1], sim.configuration)
            actions = [a0, a1]
        else:
            a0 = opp_mod.agent(obs[0], sim.configuration)
            a1 = v49_mod.agent(obs[1], sim.configuration)
            actions = [a0, a1]
            
        if step == 150:
            v49_cs_decision = v49_mod._CS_REPORT.get("cs_decision", "")
            
        obs, rewards, done, info = sim.step(actions)
        if done:
            break
            
    v49_cash = float(obs[seat]["farms"][seat]["money"])
    opp_cash = float(obs[seat]["farms"][1 - seat]["money"])
    margin = v49_cash - opp_cash
    
    return {
        "seed": seed,
        "seat": seat,
        "opponent": opp_name,
        "v49_cash": v49_cash,
        "opp_cash": opp_cash,
        "margin": margin,
        "abs_margin": abs(margin),
        "won": margin > 0,
        "is_near_tie": abs(margin) <= 500.0,
        "v49_cs_decision": v49_cs_decision,
        "opp_step150": opp_state_step150
    }

print("Searching near-ties across 256 paired legs (128 vs V48, 128 vs V44)...")
all_matches = []
near_ties = []

for s in NEAR_TIE_SEEDS:
    for seat in [0, 1]:
        # Test vs V48
        r_v48 = run_match(s, seat, "V48")
        all_matches.append(r_v48)
        if r_v48["is_near_tie"]:
            near_ties.append(r_v48)
            print(f"NEAR-TIE vs V48 | Seed {s}:{seat} Margin=${r_v48['margin']:>7.2f} OppCows={r_v48['opp_step150']['cows']} Score={r_v48['opp_step150']['dairy_score']:.2f} Won={r_v48['won']}")

for s in NEAR_TIE_SEEDS[:64]: # 128 legs vs V44
    for seat in [0, 1]:
        r_v44 = run_match(s, seat, "V44")
        all_matches.append(r_v44)
        if r_v44["is_near_tie"]:
            near_ties.append(r_v44)
            print(f"NEAR-TIE vs V44 | Seed {s}:{seat} Margin=${r_v44['margin']:>7.2f} OppCows={r_v44['opp_step150']['cows']} Score={r_v44['opp_step150']['dairy_score']:.2f} Won={r_v44['won']}")

print(f"\nTotal matches evaluated: {len(all_matches)}")
print(f"Total near-ties found (abs(margin) <= $500): {len(near_ties)}")

if near_ties:
    won_ties = [m for m in near_ties if m["won"]]
    lost_ties = [m for m in near_ties if not m["won"]]
    print(f"Near-ties won by V49: {len(won_ties)}, lost by V49: {len(lost_ties)}")
    
    mean_score_won = np.mean([m["opp_step150"]["dairy_score"] for m in won_ties]) if won_ties else 0
    mean_score_lost = np.mean([m["opp_step150"]["dairy_score"] for m in lost_ties]) if lost_ties else 0
    print(f"Mean Opponent Dairy Score in Near-Ties Won: {mean_score_won:.3f}")
    print(f"Mean Opponent Dairy Score in Near-Ties Lost: {mean_score_lost:.3f}")
    print(f"Separation delta: {mean_score_lost - mean_score_won:.3f}")

with open("research/v54/cowswap/near_tie_analysis.json", "w") as f:
    json.dump({
        "total_matches": len(all_matches),
        "near_ties_count": len(near_ties),
        "near_ties": near_ties
    }, f, indent=2)

print("Saved near_tie_analysis.json")
