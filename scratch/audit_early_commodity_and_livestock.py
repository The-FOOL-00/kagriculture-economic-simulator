import os
import sys
import copy
import json
import csv
from collections import defaultdict
import importlib.util
from kaggle_environments import make

CANDIDATE_PATHS = {
    "V66": "external_repos/kaggriculture-v66-agent/main.py",
    "V54++": "candidates/v54_plus_shop.py",
}

_LOADED_AGENTS = {}

def get_agent_fn(name):
    if name not in _LOADED_AGENTS:
        path = os.path.abspath(CANDIDATE_PATHS[name])
        d = os.path.dirname(path)
        if d not in sys.path:
            sys.path.insert(0, d)
        spec = importlib.util.spec_from_file_location(name.replace("+", "p") + "_eval", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _LOADED_AGENTS[name] = getattr(mod, "agent", getattr(mod, "kaggle_agent", None))
    return _LOADED_AGENTS[name]

fn_v54 = get_agent_fn("V54++")
fn_v66 = get_agent_fn("V66")

seeds_to_test = [1542, 1609, 1773, 1871, 1948, 1949, 1969]

results = []

for seed in seeds_to_test:
    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env.reset()
    
    # Per-player metrics for Steps 0-143
    stats = [{
        "strawberry_plants": 0,
        "strawberry_harvests": 0,
        "strawberry_sales": 0,
        "strawberry_sale_steps": [],
        "strawberry_revenue": 0.0,
        "wheat_sales": 0,
        "wool_sales": 0,
        "milk_sales": 0,
        "fert_buys": 0,
        "cow_buys": 0,
        "cow_steps": [],
        "sheep_buys": 0,
        "sheep_steps": [],
        "feed_actions": 0,
        "care_actions": 0,
        "water_actions": 0,
        "move_actions": 0,
        "productive_actions": 0,
        "animal_starvations": 0,
        "cash_step72": 0.0,
        "cash_step144": 0.0,
        "strawberry_prices": []
    } for _ in range(2)]
    
    for s in range(144):
        o0, o1 = env.state[0].observation, env.state[1].observation
        o0["step"], o1["step"] = s, s
        
        act0 = fn_v54(o0, env.configuration)
        act1 = fn_v66(o1, env.configuration)
        
        # Track market orders
        for p, act in enumerate([act0, act1]):
            for ord in (act.get("market") or []):
                if len(ord) >= 3:
                    cmd, item, qty = ord[0], ord[1], int(ord[2])
                    if cmd == "SELL":
                        if item == "STRAWBERRY":
                            stats[p]["strawberry_sales"] += qty
                            stats[p]["strawberry_sale_steps"].append(s)
                            # get price from market
                            mkt = env.state[p].observation.get("market", {})
                            price = mkt.get(item, {}).get("price", 0.0)
                            stats[p]["strawberry_revenue"] += qty * price
                            stats[p]["strawberry_prices"].append(price)
                        elif item == "WHEAT":
                            stats[p]["wheat_sales"] += qty
                        elif item == "WOOL":
                            stats[p]["wool_sales"] += qty
                        elif item == "MILK":
                            stats[p]["milk_sales"] += qty
                    elif cmd == "BUY":
                        if item == "FERTILIZER":
                            stats[p]["fert_buys"] += qty
                        elif item == "COW":
                            stats[p]["cow_buys"] += qty
                            stats[p]["cow_steps"].append(s)
                        elif item == "SHEEP":
                            stats[p]["sheep_buys"] += qty
                            stats[p]["sheep_steps"].append(s)
            
            # Track farmer actions
            f_act = act.get("farmer", ["PASS"])
            if f_act[0] in ["NORTH", "SOUTH", "EAST", "WEST"]:
                stats[p]["move_actions"] += 1
            elif f_act[0] in ["PLANT", "HARVEST", "WATER", "CARE", "FEED", "BUY", "SELL"]:
                stats[p]["productive_actions"] += 1
            if f_act[0] == "CARE":
                stats[p]["care_actions"] += 1
            elif f_act[0] == "FEED":
                stats[p]["feed_actions"] += 1
            elif f_act[0] == "WATER":
                stats[p]["water_actions"] += 1
            elif f_act[0] == "PLANT" and len(f_act) > 1 and f_act[1] == "STRAWBERRY":
                stats[p]["strawberry_plants"] += 1
            elif f_act[0] == "HARVEST":
                # check if strawberry
                pass

        env.step([act0, act1])
        
        if s == 71:
            stats[0]["cash_step72"] = env.state[0].observation["farms"][0]["money"]
            stats[1]["cash_step72"] = env.state[1].observation["farms"][1]["money"]
        if s == 143:
            stats[0]["cash_step144"] = env.state[0].observation["farms"][0]["money"]
            stats[1]["cash_step144"] = env.state[1].observation["farms"][1]["money"]

    results.append({
        "seed": seed,
        "v54": stats[0],
        "v66": stats[1]
    })

print(json.dumps(results, indent=2))
with open("research/early_accounting_7seeds.json", "w") as f:
    json.dump(results, f, indent=2)
