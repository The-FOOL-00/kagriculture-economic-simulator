"""
scratch/inspect_strawberry_divergence.py
========================================
Inspect transactions on Days 13-18 (Steps 312 to 432) for Tarzan vs V54++.
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

for step in range(433):
    o0 = game.observe(0)
    o1 = game.observe(1)
    a0 = mod_tarzan.agent(o0)
    a1 = v54_plus_residual.agent(o1)
    
    m0_before = o0["farms"][0]["money"]
    m1_before = o1["farms"][1]["money"]
    
    game.step(a0, a1)
    
    o0_after = game.observe(0)
    o1_after = game.observe(1)
    m0_after = o0_after["farms"][0]["money"]
    m1_after = o1_after["farms"][1]["money"]
    
    # Check if sales happened
    if 336 <= step <= 432:
        d0 = m0_after - m0_before
        d1 = m1_after - m1_before
        if d0 > 0 or d1 > 0:
            day = step // 24
            hour = step % 24
            print(f"Step {step:3d} (Day {day:2d} h{hour:02d}) -> Tarzan rev: +${d0:6,.0f} (market={a0.get('market')}) | V54++ rev: +${d1:6,.0f} (market={a1.get('market')})")
