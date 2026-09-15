import os
import sys
import json
import csv
import numpy as np

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("./external_repos/kaggriculture-cppsim"))

import kagsim
from candidates.closed_loop_architecture.dev_005_confirmed_shop_scheduler import Dev005ConfirmedShopScheduler, PRODUCT_SHOPS

SEEDS = list(range(247000, 247050))

# Metrics to collect:
# - terminal dead inventory (items that cannot be sold at current shops or farm market)
# - worker under-service (unharvested mature crops at end)
# - liquidity failures (cash < 0 or bankruptcy)
# - market mismatch count (inventory produced that had no matching commercial shop)
# - asset mismatch count (specialized livestock bought without matching commercial shop)

audit_results = {}

for seed in SEEDS:
    # We inspect Match 0 of DEV-005
    g = kagsim.Game(seed)
    cand = Dev005ConfirmedShopScheduler(seat=0, seed=seed)
    
    # Run simulation
    while not g.done:
        o0 = g.observe(0)
        o1 = g.observe(1)
        a0 = cand.act(o0)
        # Dummy opponent
        a1 = {"player": 1, "worker_moves": [], "builds": [], "purchases": [], "sales": []}
        # But wait, to match baseline opponent we can just load baseline or check game state
        g.step(a0, a1)
        
    final_obs = g.observe(0)
    unlocked_shops = set(cand.unlocked_shops)
    
    # Inventory
    inventory = final_obs.get("inventory", {}) or {}
    total_inv_units = sum(inventory.values())
    
    # Market mismatch: units in inventory whose primary specialized shop is not in unlocked_shops
    # (e.g. WOOL without YARN_STORE)
    wool_units = inventory.get("WOOL", 0)
    wool_mismatch = wool_units if "YARN_STORE" not in unlocked_shops else 0
    
    # Animal count
    sheep_count = 0
    cow_count = 0
    for a in final_obs.get("animals", []):
        if a.get("type") == "SHEEP":
            sheep_count += 1
        elif a.get("type") == "COW":
            cow_count += 1
            
    # Asset mismatch: sheep > 5 without YARN_STORE
    sheep_mismatch = max(0, sheep_count - 5) if "YARN_STORE" not in unlocked_shops else 0
    
    # Unharvested mature tiles at step 720
    unharvested_mature = 0
    for tile in final_obs.get("map", []):
        if tile.get("crop_type") and tile.get("crop_growth", 0) >= 1.0:
            unharvested_mature += 1
            
    # Liquidity check
    min_cash = min([ev.get("liquidity", 1000) for ev in cand.decision_events] or [final_obs.get("money", 0)])
    liquidity_failure = (final_obs.get("money", 0) < 0) or (min_cash < 0)
    
    audit_results[seed] = {
        "seed": seed,
        "active_plan": cand.active_plan,
        "unlocked_shops": list(unlocked_shops),
        "terminal_money": final_obs.get("money", 0),
        "total_inv_units": total_inv_units,
        "wool_units": wool_units,
        "wool_mismatch": wool_mismatch,
        "sheep_count": sheep_count,
        "sheep_mismatch": sheep_mismatch,
        "unharvested_mature_tiles": unharvested_mature,
        "liquidity_failure": liquidity_failure,
        "min_cash": min_cash
    }

with open("scratch/dev005_telemetry_audit.json", "w") as f:
    json.dump(audit_results, f, indent=2)

print("Completed telemetry audit for 50 seeds.")
total_wool_mismatch = sum(v["wool_mismatch"] for v in audit_results.values())
total_sheep_mismatch = sum(v["sheep_mismatch"] for v in audit_results.values())
total_unharvested = sum(v["unharvested_mature_tiles"] for v in audit_results.values())
total_liq_failures = sum(1 for v in audit_results.values() if v["liquidity_failure"])

print(f"Total Wool Market Mismatch Units: {total_wool_mismatch}")
print(f"Total Sheep Asset Mismatch: {total_sheep_mismatch}")
print(f"Total Unharvested Mature Tiles: {total_unharvested}")
print(f"Total Liquidity Failures: {total_liq_failures}")
