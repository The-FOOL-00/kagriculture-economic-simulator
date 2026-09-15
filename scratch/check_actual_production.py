"""
scratch/check_actual_production.py
==================================
Inspects the actual physical units produced and cash realized by Tarzan vs V54++.
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

while not game.done:
    o0 = game.observe(0)
    o1 = game.observe(1)
    a0 = mod_tarzan.agent(o0)
    a1 = v54_plus_residual.agent(o1)
    game.step(a0, a1)

print(f"Final Cash -> Tarzan: ${game.reward(0):,.2f} | V54++: ${game.reward(1):,.2f}")
# In kagsim, we can check private shed, bank, etc.
obs0 = game.observe(0)
obs1 = game.observe(1)
print("Tarzan final shed:", obs0["private"]["shed"])
print("V54++ final shed :", obs1["private"]["shed"])
