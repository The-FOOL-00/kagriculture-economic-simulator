import os
import sys
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

import kagsim
import router_parent as mod_r
from closed_loop_v2 import ClosedLoopAgentV2
from specialized_branch_agent import DemandSpecializedAgent

g_v2 = kagsim.Game(50007)
p_v2 = ClosedLoopAgentV2()
p_dmi = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))

v2_sales = {}
while not g_v2.done:
    s = g_v2.observe(0)["step"]
    a0 = p_v2.act(g_v2.observe(0))
    a1 = p_dmi.act(g_v2.observe(1))
    for m in a0.get("market", []):
        if m and m[0] == "SELL":
            v2_sales[m[1]] = v2_sales.get(m[1], 0) + m[2]
    g_v2.step(a0, a1)

g_sp = kagsim.Game(50007)
p_sp = DemandSpecializedAgent(enable_pizza_specialist=True)
p_dmi2 = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))

sp_sales = {}
while not g_sp.done:
    s = g_sp.observe(0)["step"]
    a0 = p_sp.act(g_sp.observe(0))
    a1 = p_dmi2.act(g_sp.observe(1))
    for m in a0.get("market", []):
        if m and m[0] == "SELL":
            sp_sales[m[1]] = sp_sales.get(m[1], 0) + m[2]
    g_sp.step(a0, a1)

print(f"Seed 50007 Results:")
print(f"V2 Cash: ${g_v2.reward(0):,.0f} | Sales breakdown: {v2_sales}")
print(f"Spec Cash: ${g_sp.reward(0):,.0f} | Sales breakdown: {sp_sales}")
print(f"Discarded V2: {g_v2.observe(0)['farms'][0].get('discarded')}")
print(f"Discarded Spec: {g_sp.observe(0)['farms'][0].get('discarded')}")
