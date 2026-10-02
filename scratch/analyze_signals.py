import sys, os
sys.path.insert(0, os.path.abspath("."))
import json
import numpy as np
from typing import Dict, Any, List

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

def extract_signals_at_step(obs: Dict[str, Any], prev_obs: Dict[str, Any], seat: int) -> Dict[str, Any]:
    opp = 1 - seat
    opp_farm = obs["farms"][opp]
    prev_opp_farm = prev_obs["farms"][opp] if prev_obs else opp_farm
    opp_tiles = opp_farm["tiles"]
    
    # O1: Opponent cow count
    o1_cows = sum(1 for r in opp_tiles for t in r if isinstance(t, dict) and t.get("animal") == "COW")
    
    # O2: Opponent pasture capacity (number of pastures)
    o2_pastures = sum(1 for r in opp_tiles for t in r if isinstance(t, dict) and t.get("kind") == "PASTURE")
    
    # O3: Opponent milk inventory (unharvested milk units sitting on cow tiles)
    o3_unharvested_milk = sum(t.get("yield_units", 0) for r in opp_tiles for t in r if isinstance(t, dict) and t.get("animal") == "COW")
    
    # O4: Opponent hired-hand count
    o4_hands = len(opp_farm.get("hands", []))
    
    # O5: Opponent cash trajectory (cash delta over last 24 steps if available)
    o5_cash = float(opp_farm.get("money", 0.0))
    o5_cash_delta = o5_cash - float(prev_opp_farm.get("money", 0.0))
    
    # O6: Opponent purchase actions legally inferred (new pastures or cows placed)
    prev_cows = sum(1 for r in prev_opp_farm["tiles"] for t in r if isinstance(t, dict) and t.get("animal") == "COW") if prev_obs else o1_cows
    o6_cow_purchases = max(0, o1_cows - prev_cows)
    
    # O7: Shared milk market inventory
    mkt = obs["market"]
    o7_milk_inv = mkt["inventory"]["MILK"]
    
    # O8: Shared milk price
    o8_milk_price = mkt["prices"]["MILK"]
    
    # O9: Recent milk sales inferred from public market changes (market inv increase not from us)
    # If prev_obs, delta = mkt['inventory']['MILK'] - prev_mkt['inventory']['MILK']
    if prev_obs:
        prev_mkt = prev_obs["market"]
        o9_inferred_sales = mkt["inventory"]["MILK"] - prev_mkt["inventory"]["MILK"]
    else:
        o9_inferred_sales = 0
        
    # O10: Composite public dairy score (normalized prototype)
    # w1 * cows + w2 * pastures + w3 * hands + w4 * (milk_price / 100)
    o10_composite = (o1_cows * 1.5) + (o2_pastures * 0.5) + (o4_hands * 0.2) + (o8_milk_price / 50.0)
    
    return {
        "O1_cows": o1_cows,
        "O2_pastures": o2_pastures,
        "O3_unharvested_milk": o3_unharvested_milk,
        "O4_hands": o4_hands,
        "O5_cash": o5_cash,
        "O5_cash_delta_recent": o5_cash_delta,
        "O6_cow_purchases": o6_cow_purchases,
        "O7_milk_inv": o7_milk_inv,
        "O8_milk_price": o8_milk_price,
        "O9_inferred_sales": o9_inferred_sales,
        "O10_composite_score": o10_composite
    }

def record_match_signals(seed: int, seat: int, world_type: str) -> Dict[str, Any]:
    sim = FastKagricultureSim(seed=seed)
    obs = sim.reset()
    prev_obs = None
    step_history = {}
    target_steps = [24, 48, 72, 96, 120, 144, 150]
    
    for step in range(151):
        if step in target_steps:
            step_history[f"step_{step}"] = extract_signals_at_step(obs[seat], prev_obs[seat] if prev_obs else None, seat)
        prev_obs = obs
        if seat == 0:
            a0 = v49_mod.agent(obs[0], sim.configuration)
            a1 = v44_mod.agent(obs[1], sim.configuration)
            actions = [a0, a1]
        else:
            a0 = v44_mod.agent(obs[0], sim.configuration)
            a1 = v49_mod.agent(obs[1], sim.configuration)
            actions = [a0, a1]
        obs, rewards, done, info = sim.step(actions)
        if done:
            break
            
    return {
        "seed": seed,
        "seat": seat,
        "world_type": world_type,
        "steps": step_history
    }

groups = {
    "DAIRY_COMMITMENT_LOSS": [
        (250436, 0), (250436, 1),
        (250439, 0), (250439, 1)
    ],
    "NON_DAIRY_LOSS": [
        (250416, 0), (250416, 1),
        (250428, 0), (250428, 1),
        (250433, 0), (250433, 1),
        (250497, 1)
    ],
    "NEUTRAL_COWSWAP": [
        (250400, 0), (250401, 0), (250402, 0), (250403, 0)
    ],
    "WINNING_COWSWAP": [
        (250413, 0), (250414, 0), (250415, 0), (250419, 0), (250425, 0)
    ]
}

all_signal_data = []

print("Extracting observable signals across all cohorts...")
for g_name, matches in groups.items():
    for seed, seat in matches:
        data = record_match_signals(seed, seat, g_name)
        all_signal_data.append(data)
        s150 = data["steps"]["step_150"]
        print(f"[{g_name:<21}] Seed {seed}:{seat} @ Step 150: Cows={s150['O1_cows']}, Pastures={s150['O2_pastures']}, Hands={s150['O4_hands']}, MilkP={s150['O8_milk_price']}, Score={s150['O10_composite_score']:.2f}")

os.makedirs("research/v54/cowswap", exist_ok=True)
with open("research/v54/cowswap/cowswap_observable_signal_analysis.json", "w") as f:
    json.dump(all_signal_data, f, indent=2)

print("Saved cowswap_observable_signal_analysis.json")
