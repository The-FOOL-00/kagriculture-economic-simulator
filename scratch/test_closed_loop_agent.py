import sys
import os
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates"))

import kagsim
import router_parent as mod_r
import compiled_v54_plus_residual as v54
from closed_loop_agent import ClosedLoopAgent

def test_single_seed(seed=50001):
    print("=" * 80)
    print(f"TESTING CLOSED-LOOP AGENT ON SEED {seed}")
    print("=" * 80)
    
    # 1. Closed-Loop Agent vs V54++
    g0 = kagsim.Game(seed)
    agent_cl = ClosedLoopAgent(switching_mode="MILESTONE_CONSERVATIVE")
    
    step_count = 0
    while not g0.done:
        obs0 = g0.observe(0)
        obs1 = g0.observe(1)
        act0 = agent_cl.act(obs0)
        act1 = v54.agent(obs1)
        g0.step(act0, act1)
        step_count += 1
        
    r_cl = g0.reward(0)
    r_v54 = g0.reward(1)
    
    # 2. Dmitrii Base vs V54++
    g1 = kagsim.Game(seed)
    p_dm = mod_r.Policy("extracted_agents/dmitrii_lb2800")
    while not g1.done:
        obs0 = g1.observe(0)
        obs1 = g1.observe(1)
        act0 = p_dm.act(obs0)
        act1 = v54.agent(obs1)
        g1.step(act0, act1)
        
    r_dm = g1.reward(0)
    
    print(f"Game completed: {step_count} steps.")
    print(f"  Closed-Loop Cash:   ${r_cl:,.2f}")
    print(f"  Dmitrii Base Cash:  ${r_dm:,.2f}")
    print(f"  V54++ Residual Cash:${r_v54:,.2f}")
    print(f"  CL vs Dmitrii Delta: ${r_cl - r_dm:+,.2f}")
    print(f"  CL Diagnostics: {agent_cl.diagnostics}")
    print(f"  Active Module: {agent_cl.active_module_id}")
    print(f"  Switches History: {agent_cl.switching_policy.switch_history}")

if __name__ == "__main__":
    for s in [50001, 50007, 50266, 50130]:
        test_single_seed(s)
