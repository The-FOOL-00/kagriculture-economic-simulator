import os
import sys
import json
import importlib.util

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("./external_repos/kaggriculture-cppsim"))

import kagsim
from candidates.closed_loop_architecture.dev_005_confirmed_shop_scheduler import Dev005ConfirmedShopScheduler

BASELINE_PATH = "candidates/compiled_v54_plus_residual.py"

def load_isolated_baseline(module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, BASELINE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

TARGET_SEEDS = [247000, 247012, 247017, 247033, 247039, 247025, 247034]

forensics = {}

for seed in TARGET_SEEDS:
    g = kagsim.Game(seed)
    cand = Dev005ConfirmedShopScheduler(seat=0, seed=seed)
    base = load_isolated_baseline(f"base_s{seed}_forensic")
    
    cand_sales = {"WOOL": 0, "MILK": 0, "STRAWBERRY": 0, "CARROT": 0, "WHEAT": 0, "MELON": 0}
    base_sales = {"WOOL": 0, "MILK": 0, "STRAWBERRY": 0, "CARROT": 0, "WHEAT": 0, "MELON": 0}
    
    step = 0
    while not g.done:
        o0 = g.observe(0)
        o1 = g.observe(1)
        a0 = cand.act(o0)
        a1 = base.agent(o1)
        
        # Track sales in actions
        for s in a0.get("sales", []):
            item = s.get("item")
            qty = s.get("quantity", 0)
            if item in cand_sales:
                cand_sales[item] += qty
        for s in a1.get("sales", []):
            item = s.get("item")
            qty = s.get("quantity", 0)
            if item in base_sales:
                base_sales[item] += qty
                
        g.step(a0, a1)
        step += 1
        
    rew0 = float(g.reward(0))
    rew1 = float(g.reward(1))
    delta = rew0 - rew1
    
    final_o0 = g.observe(0)
    final_o1 = g.observe(1)
    
    # Animals count
    cand_sheep = sum(1 for a in final_o0.get("animals", []) if a.get("type") == "SHEEP")
    cand_cows = sum(1 for a in final_o0.get("animals", []) if a.get("type") == "COW")
    base_sheep = sum(1 for a in final_o1.get("animals", []) if a.get("type") == "SHEEP")
    base_cows = sum(1 for a in final_o1.get("animals", []) if a.get("type") == "COW")
    
    forensics[seed] = {
        "seed": seed,
        "delta": delta,
        "cand_money": rew0,
        "base_money": rew1,
        "active_plan": cand.active_plan,
        "unlocked_shops": cand.decision_events[-1]["current_shops"] if cand.decision_events else "NONE",
        "decision_events": cand.decision_events,
        "cand_animals": {"SHEEP": cand_sheep, "COW": cand_cows},
        "base_animals": {"SHEEP": base_sheep, "COW": base_cows},
        "cand_sales": cand_sales,
        "base_sales": base_sales,
        "cand_terminal_inv": final_o0.get("inventory", {}),
        "base_terminal_inv": final_o1.get("inventory", {})
    }

with open("scratch/target_seeds_forensics.json", "w") as f:
    json.dump(forensics, f, indent=2)

print("Saved scratch/target_seeds_forensics.json")
for seed, d in forensics.items():
    print(f"\nSeed {seed} | Delta: {d['delta']:+.1f} | Plan: {d['active_plan']} | Shops: {d['unlocked_shops']}")
    print(f"  Cand Animals: {d['cand_animals']} vs Base Animals: {d['base_animals']}")
    print(f"  Cand Wool Sold: {d['cand_sales']['WOOL']} vs Base Wool Sold: {d['base_sales']['WOOL']}")
    print(f"  Cand Milk Sold: {d['cand_sales']['MILK']} vs Base Milk Sold: {d['base_sales']['MILK']}")
    print(f"  Cand Terminal Inv: {d['cand_terminal_inv']}")
    print(f"  Base Terminal Inv: {d['base_terminal_inv']}")
