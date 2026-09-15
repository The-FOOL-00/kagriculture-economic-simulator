import os
import sys

BASE_DIR = os.path.abspath(".")
sys.path.insert(0, ".")
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

import kagsim
import router_parent as mod_r
from closed_loop_v2 import ClosedLoopAgentV2
from closed_loop_v3 import ClosedLoopAgentV3

test_seeds = [50001, 50004, 50006, 50007, 50011, 50013, 50016, 50028, 50037, 50042]

print("="*80)
print("TESTING CLOSED-LOOP V3 vs DMITRII BASE & CLOSED-LOOP V2")
print("="*80)

v3_wins = 0
v3_losses = 0
v3_margins = []

for s in test_seeds:
    # Match Seat 0: V3 vs Dmitrii
    p_v3_0 = ClosedLoopAgentV3()
    p_dmi_1 = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
    g0 = kagsim.Game(s)
    while not g0.done:
        g0.step(p_v3_0.act(g0.observe(0)), p_dmi_1.act(g0.observe(1)))
    v3_s0 = g0.reward(0)
    dmi_s1 = g0.reward(1)
    m0 = v3_s0 - dmi_s1
    v3_margins.append(m0)
    if m0 > 0: v3_wins += 1
    elif m0 < 0: v3_losses += 1

    # Match Seat 1: Dmitrii vs V3
    p_dmi_0 = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
    p_v3_1 = ClosedLoopAgentV3()
    g1 = kagsim.Game(s)
    while not g1.done:
        g1.step(p_dmi_0.act(g1.observe(0)), p_v3_1.act(g1.observe(1)))
    dmi_s0 = g1.reward(0)
    v3_s1 = g1.reward(1)
    m1 = v3_s1 - dmi_s0
    v3_margins.append(m1)
    if m1 > 0: v3_wins += 1
    elif m1 < 0: v3_losses += 1

    # V2 vs Dmitrii for comparison
    p_v2_0 = ClosedLoopAgentV2()
    p_dmi_1_v2 = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
    gv2 = kagsim.Game(s)
    while not gv2.done:
        gv2.step(p_v2_0.act(gv2.observe(0)), p_dmi_1_v2.act(gv2.observe(1)))
    v2_s0 = gv2.reward(0)

    print(f"Seed {s:5d}: V3 S0 ${v3_s0:,.0f} vs Dmi S1 ${dmi_s1:,.0f} (Margin: {m0:+,.0f}) | V3 S1 ${v3_s1:,.0f} vs Dmi S0 ${dmi_s0:,.0f} (Margin: {m1:+,.0f}) | V2 S0: ${v2_s0:,.0f} (V3-V2: {v3_s0-v2_s0:+,.0f})")

print("-" * 80)
mean_m = sum(v3_margins) / len(v3_margins)
print(f"Total Matches: {len(v3_margins)} | Wins: {v3_wins} | Losses: {v3_losses} | Win Rate: {v3_wins/len(v3_margins)*100:.1f}% | Mean Margin: ${mean_m:+,.2f}")
