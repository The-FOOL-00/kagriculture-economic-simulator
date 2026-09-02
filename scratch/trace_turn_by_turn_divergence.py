# SPDX-License-Identifier: MIT
"""
Turn-by-turn trace comparison between Hydra V1 and Aethel (Closer Cleo)
"""

import os
import sys
import json
import copy
import importlib.util
from kaggle_environments import make

def load_agent(filepath):
    spec = importlib.util.spec_from_file_location("agent_mod", filepath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def run_step_by_step_trace(seed=1):
    hydra = load_agent(os.path.abspath("agents/hydra_prime.py"))
    cleo = load_agent(os.path.abspath("replays/raw/reference_agents/closer_cleo.py"))
    
    env = make("kaggriculture", configuration={"seed": seed})
    
    # We will run env manually turn by turn
    obs_list = env.reset(num_agents=2)
    
    divergences = []
    
    # Track states
    for step in range(720):
        obs0 = copy.deepcopy(env.state[0].observation)
        obs1 = copy.deepcopy(env.state[1].observation)
        
        # Hydra as Player 0, Cleo as Player 1
        act0 = hydra.agent(obs0)
        act1 = cleo.agent(obs1)
        
        # Also let's check what Cleo would do if Cleo was in Player 0's shoes
        cleo_act_as_p0 = cleo.agent(obs0)
        
        # Check if Hydra action as P0 differs from Cleo action as P0
        if act0 != cleo_act_as_p0:
            div_info = {
                "step": step,
                "hour": step % 24,
                "day": step // 24,
                "hydra_act": act0,
                "cleo_act": cleo_act_as_p0,
                "p0_money": obs0.get("farms", [{}])[0].get("money", 0),
                "p1_money": obs0.get("farms", [{}])[1].get("money", 0),
                "p0_shed": dict((obs0.get("private") or {}).get("shed", {})),
                "market_prices": dict((obs0.get("market") or {}).get("prices", {})),
                "market_inv": dict((obs0.get("market") or {}).get("inventory", {}))
            }
            divergences.append(div_info)
            if len(divergences) <= 10 or step in (4, 24, 48, 72, 96, 680, 712, 716, 717):
                print(f"\n--- DIVERGENCE AT STEP {step:3d} (Day {step//24}, Hour {step%24}) ---")
                print(f"Hydra Action : {act0}")
                print(f"Cleo Action  : {cleo_act_as_p0}")
                print(f"P0 Money: {div_info['p0_money']:.1f} | P1 Money: {div_info['p1_money']:.1f}")
                print(f"P0 Shed: {div_info['p0_shed']}")
        
        # Step env with act0, act1
        env.step([act0, act1])
        
        if env.done:
            break
            
    final_reward0 = env.state[0].reward
    final_reward1 = env.state[1].reward
    print(f"\n=== MATCH END (Seed {seed}) ===")
    print(f"Total Divergences: {len(divergences)} / 720 steps")
    print(f"Hydra Reward (P0): {final_reward0}")
    print(f"Cleo  Reward (P1): {final_reward1}")
    print(f"Margin (P0 - P1): {final_reward0 - final_reward1:+.1f}")
    
    return divergences

if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    run_step_by_step_trace(seed)
