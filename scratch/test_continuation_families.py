import sys, os
sys.path.insert(0, os.path.abspath("."))
import json
import copy
from typing import Dict, Any, List

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

def run_continuation_experiment(seed: int, seat: int, variant_name: str) -> Dict[str, Any]:
    sim = FastKagricultureSim(seed=seed)
    obs = sim.reset()
    opp_seat = 1 - seat
    
    held_milk = 0
    blocked_count = 0
    
    for step in range(719):
        # Default V49 action
        if seat == 0:
            a0 = v49_mod.agent(obs[0], sim.configuration)
            a1 = v44_mod.agent(obs[1], sim.configuration)
        else:
            a0 = v44_mod.agent(obs[0], sim.configuration)
            a1 = v49_mod.agent(obs[1], sim.configuration)
            
        act = a0 if seat == 0 else a1
        mkt = act.get("market", [])
        
        shops = list(obs[seat]["town"]["unlocked_shops"])
        has_milk_shop = any(s in ("PIZZA_SHOP", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP") for s in shops)
        has_yarn_store = "YARN_STORE" in shops
        has_pet_cafe = "PET_CAFE" in shops
        
        # Apply Continuation Variants (only active from Step 216 onward)
        if step >= 216 and isinstance(act, dict):
            new_mkt = []
            
            if variant_name == "B1_HOLD_MILK_UNTIL_650":
                # If milk shop exists, hold midgame milk sales until step 650 (liquidation)
                for o in mkt:
                    if len(o) >= 3 and o[0] == "SELL" and o[1] == "MILK" and step < 650:
                        if has_milk_shop:
                            continue # suppress midgame milk sell
                    new_mkt.append(o)
                act["market"] = new_mkt
                
            elif variant_name == "B2_HOLD_MILK_PRICE_THRESHOLD":
                # Sell milk only if price >= 140 or step >= 690
                p_milk = obs[seat]["market"]["prices"]["MILK"]
                for o in mkt:
                    if len(o) >= 3 and o[0] == "SELL" and o[1] == "MILK":
                        if p_milk < 140 and step < 690:
                            continue
                    new_mkt.append(o)
                act["market"] = new_mkt
                
            elif variant_name == "B3_DUMP_MILK_PREEMPTIVE":
                # If milk shop opened at step 216, aggressively sell milk immediately to capture shop price before opponent
                shed = (obs[seat].get("private") or {}).get("shed", {})
                m_qty = shed.get("MILK", 0)
                if has_milk_shop and m_qty > 0 and step in (216, 240, 264, 288):
                    already = any(o[0] == "SELL" and o[1] == "MILK" for o in mkt)
                    if not already and len(mkt) < 10:
                        mkt.append(["SELL", "MILK", m_qty])
                act["market"] = mkt
                
            elif variant_name == "B4_HOLD_WOOL_FOR_YARN":
                # If yarn store open, sell wool; otherwise hold wool until step 690
                for o in mkt:
                    if len(o) >= 3 and o[0] == "SELL" and o[1] == "WOOL":
                        if not has_yarn_store and step < 690:
                            continue
                    new_mkt.append(o)
                act["market"] = new_mkt
                
            elif variant_name == "B5_STAGGERED_PREEMPT_DUOPOLY":
                # Pre-empt opponent staggered liquidation at step 691-692 (before V44 sells at 693)
                shed = (obs[seat].get("private") or {}).get("shed", {})
                if step in (691, 692):
                    for item in ("STRAWBERRY", "MILK", "WOOL", "MELON"):
                        q = shed.get(item, 0)
                        if q >= 2 and len(mkt) < 10:
                            mkt.append(["SELL", item, max(1, q // 2)])
                act["market"] = mkt
                
        # Execute step
        actions = [act, a1] if seat == 0 else [a0, act]
        obs, rewards, done, info = sim.step(actions)
        if done:
            break
            
    v49_cash = float(obs[seat]["farms"][seat]["money"])
    opp_cash = float(obs[seat]["farms"][opp_seat]["money"])
    margin = v49_cash - opp_cash
    
    return {
        "seed": seed,
        "seat": seat,
        "variant": variant_name,
        "v49_cash": v49_cash,
        "opp_cash": opp_cash,
        "margin": margin,
        "won": margin > 0
    }

SEEDS = [250416, 250436, 250439]
VARIANTS = [
    "CONTROL_V49",
    "B1_HOLD_MILK_UNTIL_650",
    "B2_HOLD_MILK_PRICE_THRESHOLD",
    "B3_DUMP_MILK_PREEMPTIVE",
    "B4_HOLD_WOOL_FOR_YARN",
    "B5_STAGGERED_PREEMPT_DUOPOLY"
]

results = []

print("Running continuation family experiments on critical seeds...")
for s in SEEDS:
    print(f"\n=== SEED {s} ===")
    ctrl = run_continuation_experiment(s, 0, "CONTROL_V49")
    print(f"CONTROL V49: Margin = ${ctrl['margin']:>9.2f} (Won={ctrl['won']})")
    for v in VARIANTS[1:]:
        res = run_continuation_experiment(s, 0, v)
        delta = res["margin"] - ctrl["margin"]
        print(f"Variant {v:<30}: Margin = ${res['margin']:>9.2f} | Delta = ${delta:>+9.2f} | Won={res['won']}")
        results.append(res)

os.makedirs("research/v55/counterfactuals", exist_ok=True)
with open("research/v55/counterfactuals/critical_seed_counterfactuals.json", "w") as f:
    json.dump(results, f, indent=2)

print("\nSaved research/v55/counterfactuals/critical_seed_counterfactuals.json")
