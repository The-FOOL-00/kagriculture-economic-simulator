import sys, os
sys.path.insert(0, os.path.abspath("."))
import json
import numpy as np
from collections import defaultdict

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

# Groups against V44 (Seat 0):
# Group C (Losses): 250617 (-$862), 250621 (-$82)
# Group B (Near Wins <= $500): 250616 (+$384), 250631 (+$305)
# Group A (Comfortable Wins): 250600 (+$1,336), 250607 (+$8,961), 250618 (+$2,788), 250620 (+$5,526), 250622 (+$11,411)

groups = {
    "Losses (Group C)": [250617, 250621],
    "Near Wins (Group B)": [250616, 250631],
    "Comfortable Wins (Group A)": [250600, 250607, 250618, 250620, 250622]
}

check_steps = [150, 216, 360, 504, 600, 648, 690]

features = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

print("Extracting trajectory features for Group A, B, C against V44...")

for grp_name, seeds in groups.items():
    for s in seeds:
        sim = FastKagricultureSim(seed=s)
        obs = sim.reset(seed=s)
        for step in range(719):
            if step in check_steps:
                f0 = obs[0]["farms"][0]
                f1 = obs[1]["farms"][1]
                c0 = float(f0["money"])
                c1 = float(f1["money"])
                rel_cash = c0 - c1
                
                # Public visible opponent features
                opp_cows = sum(1 for row in f1["tiles"] for t in row if isinstance(t, dict) and t.get("animal") == "COW")
                opp_sheep = sum(1 for row in f1["tiles"] for t in row if isinstance(t, dict) and t.get("animal") == "SHEEP")
                opp_geese = sum(1 for row in f1["tiles"] for t in row if isinstance(t, dict) and t.get("animal") == "GOOSE")
                
                my_cows = sum(1 for row in f0["tiles"] for t in row if isinstance(t, dict) and t.get("animal") == "COW")
                my_sheep = sum(1 for row in f0["tiles"] for t in row if isinstance(t, dict) and t.get("animal") == "SHEEP")
                
                # Market prices
                mkt_prices = obs[0]["market"]["prices"]
                milk_price = mkt_prices.get("MILK", 100)
                wool_price = mkt_prices.get("WOOL", 150)
                
                features[grp_name][step]["rel_cash"].append(rel_cash)
                features[grp_name][step]["milk_price"].append(milk_price)
                features[grp_name][step]["wool_price"].append(wool_price)
                features[grp_name][step]["opp_cows"].append(opp_cows)
                features[grp_name][step]["my_cows"].append(my_cows)
                
            a0 = v49_mod.agent(obs[0])
            a1 = v44_mod.agent(obs[1])
            obs, _, done, _ = sim.step([a0, a1])

print("\n--- TRAJECTORY FEATURE SEPARATION SUMMARY ---")
for step in check_steps:
    print(f"\n================ STEP {step} ================")
    for feat in ("rel_cash", "milk_price", "wool_price", "opp_cows"):
        vals_c = features["Losses (Group C)"][step][feat]
        vals_b = features["Near Wins (Group B)"][step][feat]
        vals_a = features["Comfortable Wins (Group A)"][step][feat]
        print(f"  Feature {feat:<12}:")
        print(f"    Losses (C)      : {vals_c} -> mean = {np.mean(vals_c):.1f}")
        print(f"    Near Wins (B)   : {vals_b} -> mean = {np.mean(vals_b):.1f}")
        print(f"    Comfortable (A) : {vals_a} -> mean = {np.mean(vals_a):.1f}")

summary_payload = {
    "groups": {k: v for k, v in groups.items()},
    "features": {g: {step: {f: vals for f, vals in fdict.items()} for step, fdict in sdict.items()} for g, sdict in features.items()}
}

with open("research/v56/analysis/DIVERGENCE_SIGNALS.json", "w") as f:
    json.dump(summary_payload, f, indent=2)

print("\nSaved research/v56/analysis/DIVERGENCE_SIGNALS.json!")
