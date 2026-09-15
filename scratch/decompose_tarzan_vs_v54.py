"""
scratch/decompose_tarzan_vs_v54.py
==================================
Deep economic decomposition of Tarzan vs V54++ head-to-head match on Seed 47.
Tracks cash, shed inventory, production, sales, and worker actions.
"""
import importlib.util
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates"))

import kagsim
import v54_plus_residual

TARZAN_DIR = os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800")
sys.path.insert(0, TARZAN_DIR)

spec_tarzan = importlib.util.spec_from_file_location("tarzan_agent", os.path.join(TARZAN_DIR, "main.py"))
mod_tarzan = importlib.util.module_from_spec(spec_tarzan)
spec_tarzan.loader.exec_module(mod_tarzan)

seed = 47
game = kagsim.Game(seed)

checkpoints = [0, 72, 144, 216, 288, 360, 432, 504, 576, 648, 718]

# Track metrics
t_cash, v_cash = {}, {}
t_sales, v_sales = {}, {}
t_ferts, v_ferts = 0, 0

print("=" * 75)
print(f"ECONOMIC DECOMPOSITION: TARZAN (Seat 0) vs V54++ RESIDUAL (Seat 1) on Seed {seed}")
print("=" * 75)

for step in range(719):
    o0 = game.observe(0)
    o1 = game.observe(1)
    
    if step in checkpoints:
        m0 = o0["farms"][0]["money"]
        m1 = o1["farms"][1]["money"]
        h0 = len(o0["farms"][0]["hands"])
        h1 = len(o1["farms"][1]["hands"])
        t_cash[step] = m0
        v_cash[step] = m1
        print(f"Step {step:3d} (Day {step//24:2d}) | Tarzan: ${m0:9,.0f} ({h0:2d}h) | V54++: ${m1:9,.0f} ({h1:2d}h) | Delta: {m0 - m1:+9,.0f}")
        
    a0 = mod_tarzan.agent(o0)
    a1 = v54_plus_residual.agent(o1)
    
    # Count fertilize
    for cmd in ([a0.get("farmer")] + a0.get("hands", [])):
        if cmd and cmd[0] == "FERTILIZE": t_ferts += 1
    for cmd in ([a1.get("farmer")] + a1.get("hands", [])):
        if cmd and cmd[0] == "FERTILIZE": v_ferts += 1
        
    # Count sales
    for order in a0.get("market", []):
        if order and order[0] == "SELL":
            t_sales[order[1]] = t_sales.get(order[1], 0) + order[2]
    for order in a1.get("market", []):
        if order and order[0] == "SELL":
            v_sales[order[1]] = v_sales.get(order[1], 0) + order[2]
            
    game.step(a0, a1)

print("-" * 75)
print(f"Final Rewards -> Tarzan: ${game.reward(0):,.2f} | V54++: ${game.reward(1):,.2f} | Net Margin: {game.reward(0) - game.reward(1):+,.2f}")
print(f"Total FERTILIZE Actions -> Tarzan: {t_ferts} | V54++: {v_ferts}")
print("\n--- Realized Units Sold by Commodity ---")
products = sorted(set(list(t_sales.keys()) + list(v_sales.keys())))
print(f"{'Product':<12} | {'Tarzan Sold':<12} | {'V54++ Sold':<12} | {'Delta':<10}")
print("-" * 52)
for p in products:
    ts = t_sales.get(p, 0)
    vs = v_sales.get(p, 0)
    print(f"{p:<12} | {ts:<12d} | {vs:<12d} | {ts - vs:+10d}")
print("=" * 75)
