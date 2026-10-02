import sys, os
sys.path.insert(0, os.path.abspath("."))
import json
from typing import Dict, Any, Tuple

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod
from scratch.analyze_signals import extract_signals_at_step

TARGET_MATCHES = [
    {"loss_id": "L07", "seed": 250436, "seat": 0, "type": "RESCUE_TARGET"},
    {"loss_id": "L08", "seed": 250436, "seat": 1, "type": "RESCUE_TARGET"},
    {"loss_id": "L09", "seed": 250439, "seat": 0, "type": "RESCUE_TARGET"},
    {"loss_id": "L10", "seed": 250439, "seat": 1, "type": "RESCUE_TARGET"},
    {"loss_id": "L01", "seed": 250416, "seat": 0, "type": "NEGATIVE_CONTROL"},
    {"loss_id": "L02", "seed": 250416, "seat": 1, "type": "NEGATIVE_CONTROL"},
]

def evaluate_cowswap_gate(policy: str, obs: Dict[str, Any], seat: int) -> Tuple[bool, float, Dict[str, Any]]:
    """Evaluates whether policy suppresses COWSWAP at Step 150 using ONLY legal public state."""
    if policy == "C0":
        return False, 0.0, {}
    if policy == "C_off":
        return True, 0.0, {}
        
    opp_seat = 1 - seat
    opp_farm = obs["farms"][opp_seat]
    v49_farm = obs["farms"][seat]
    
    # Observable features
    opp_cows = sum(1 for r in opp_farm["tiles"] for t in r if isinstance(t, dict) and t.get("animal") == "COW")
    opp_pastures = sum(1 for r in opp_farm["tiles"] for t in r if isinstance(t, dict) and t.get("kind") == "PASTURE")
    opp_hands = len(opp_farm.get("hands", []))
    
    mkt = obs["market"]
    prices = mkt["prices"]
    milk_p = prices.get("MILK", 160)
    egg_p = prices.get("EGG", 50)
    
    shops = list((obs.get("town") or {}).get("unlocked_shops") or [])
    has_egg_shop = any(s in ("BAKERY", "BRUNCH_SPOT") for s in shops)
    has_milk_shop = any(s in ("PIZZA_SHOP", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP") for s in shops)
    
    # Dairy Score
    dairy_score = (opp_cows * 1.5) + (opp_pastures * 0.5) + (opp_hands * 0.2) + (milk_p / 50.0)
    
    suppress = False
    details = {
        "opp_cows": opp_cows,
        "opp_pastures": opp_pastures,
        "opp_hands": opp_hands,
        "milk_price": milk_p,
        "egg_price": egg_p,
        "dairy_score": dairy_score,
        "has_egg_shop": has_egg_shop,
        "has_milk_shop": has_milk_shop
    }
    
    if policy == "C1":
        # Suppress if opponent cows >= 4
        suppress = (opp_cows >= 4)
    elif policy == "C2":
        # Suppress if opponent pastures >= 6
        suppress = (opp_pastures >= 6)
    elif policy == "C3":
        # Suppress if composite dairy score >= 14.0
        suppress = (dairy_score >= 14.0)
    elif policy == "C4":
        # Suppress if dairy score >= 14.0 and COWSWAP would materially reduce V49 milk supply
        # V49 plans to swap 3 cows to geese
        suppress = (dairy_score >= 14.0 and opp_cows >= 4)
    elif policy == "C5":
        # Relative-economic gate:
        # Isolated egg advantage estimated ~ $1,500
        # Opponent deprivation benefit: opp_cows * (milk_p - 110) * 15 (estimated future yield)
        estimated_deprivation = opp_cows * max(0, milk_p - 110) * 12.0
        estimated_egg_gain = 1500.0
        suppress = (estimated_deprivation > estimated_egg_gain)
        details["estimated_deprivation"] = estimated_deprivation
    elif policy == "C6":
        # Full relative market gate:
        # Opponent dairy commitment high (cows >= 4), milk price high (>= 180),
        # no milk shop open to absorb flood, so our milk will depress price significantly
        suppress = (opp_cows >= 4 and milk_p >= 180 and not has_milk_shop)
        
    return suppress, dairy_score, details

def run_match_with_policy(spec: Dict[str, Any], policy: str) -> Dict[str, Any]:
    seed = spec["seed"]
    seat = spec["seat"]
    opp_seat = 1 - seat
    
    sim = FastKagricultureSim(seed=seed)
    obs = sim.reset()
    
    step_150_action = None
    step_150_suppress = False
    step_150_dairy_score = 0.0
    gate_details = {}
    
    milk_prices_timeline = []
    
    v49_milk_produced = 0
    v49_eggs_produced = 0
    opp_milk_produced = 0
    
    for step in range(720):
        if step % 24 == 0:
            milk_prices_timeline.append(obs[seat]["market"]["prices"]["MILK"])
            
        if step == 150:
            suppress, score, details = evaluate_cowswap_gate(policy, obs[seat], seat)
            step_150_suppress = suppress
            step_150_dairy_score = score
            gate_details = details
            
            orig_options = v49_mod._CS_OPTIONS
            if suppress:
                v49_mod._CS_OPTIONS = ()
            else:
                v49_mod._CS_OPTIONS = ('GOOSE',)
                
        # Agent calls
        if seat == 0:
            a0 = v49_mod.agent(obs[0], sim.configuration)
            a1 = v44_mod.agent(obs[1], sim.configuration)
            actions = [a0, a1]
        else:
            a0 = v44_mod.agent(obs[0], sim.configuration)
            a1 = v49_mod.agent(obs[1], sim.configuration)
            actions = [a0, a1]
            
        if step == 150:
            step_150_action = actions[seat]
            v49_mod._CS_OPTIONS = ('GOOSE',) # reset
            
        # Track production yields directly from farm tiles
        v49_farm = obs[seat]["farms"][seat]
        opp_farm = obs[seat]["farms"][opp_seat]
        for r in v49_farm["tiles"]:
            for t in r:
                if isinstance(t, dict):
                    if t.get("animal") == "COW" and t.get("yield_units", 0) > 0:
                        v49_milk_produced += t["yield_units"]
                    elif t.get("animal") == "GOOSE" and t.get("yield_units", 0) > 0:
                        v49_eggs_produced += t["yield_units"]
        for r in opp_farm["tiles"]:
            for t in r:
                if isinstance(t, dict):
                    if t.get("animal") == "COW" and t.get("yield_units", 0) > 0:
                        opp_milk_produced += t["yield_units"]
                        
        obs, rewards, done, info = sim.step(actions)
        if done:
            break
            
    v49_cash = float(obs[seat]["farms"][seat]["money"])
    opp_cash = float(obs[seat]["farms"][opp_seat]["money"])
    margin = v49_cash - opp_cash
    won = margin > 0
    
    # Check rescue status
    baseline_nominal = spec.get("nominal_loss", -1400.0)
    rescued = (won and baseline_nominal < 0)
    
    return {
        "loss_id": spec["loss_id"],
        "seed": seed,
        "seat": seat,
        "type": spec["type"],
        "policy": policy,
        "step_150_suppressed": step_150_suppress,
        "dairy_score": step_150_dairy_score,
        "terminal_v49_cash": v49_cash,
        "terminal_opp_cash": opp_cash,
        "terminal_margin": margin,
        "won": won,
        "rescued": rescued,
        "milk_prices_timeline": milk_prices_timeline,
        "gate_details": gate_details
    }

POLICIES = ["C0", "C1", "C2", "C3", "C4", "C5", "C6", "C_off"]
all_results = []

print("Running counterfactual evaluations across policies C0..C6, C_off...")
for m in TARGET_MATCHES:
    print(f"\n--- MATCH {m['loss_id']} (Seed {m['seed']} Seat {m['seat']} - {m['type']}) ---")
    for pol in POLICIES:
        res = run_match_with_policy(m, pol)
        all_results.append(res)
        print(f"Policy {pol:<5}: Suppress={str(res['step_150_suppressed']):<5} Margin=${res['terminal_margin']:>9.2f} (Won={res['won']}, Rescued={res['rescued']})")

os.makedirs("research/v54/cowswap", exist_ok=True)
with open("research/v54/cowswap/cowswap_loss_counterfactuals.json", "w") as f:
    json.dump(all_results, f, indent=2)

print("\nSaved cowswap_loss_counterfactuals.json")
