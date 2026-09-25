# SPDX-License-Identifier: MIT
import os, sys
sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("extracted_agents/dmitrii_lb2800"))
from kaggle_environments import make
from scripts.v32_common import load_agent
import terminal_planner as dmit_planner

def analyze_regression(seed=249677):
    # 1. Run baseline
    a7_base = load_agent("E9_AST")
    dmit_base = load_agent("E8_DMITRII")
    env_base = make("kaggriculture", configuration={"seed": seed})
    env_base.run([lambda o, c=None: a7_base.act(o, c), lambda o, c=None: dmit_base.act(o, c)])
    
    obs_712 = env_base.steps[712][0]["observation"]
    config = env_base.configuration
    a7_remaining = [env_base.steps[s][0]["action"] for s in range(712, 719)]
    plan = dmit_planner.plan_terminal(obs_712, config, a7_remaining, max_simulations=128)
    cand_actions = plan.get("actions")
    
    # 2. Run candidate
    class CandidateAgent:
        def __init__(self, plan_actions):
            self.base_agent = load_agent("E9_AST")
            self.plan_actions = plan_actions
            
        def act(self, obs, cfg=None):
            step = obs.get("step", 0)
            if step < 712:
                return self.base_agent.act(obs, cfg)
            elif 712 <= step <= 718:
                offset = step - 712
                if self.plan_actions and offset < len(self.plan_actions):
                    return self.plan_actions[offset]
            return self.base_agent.act(obs, cfg)

    cand_agent = CandidateAgent(cand_actions)
    dmit_cand = load_agent("E8_DMITRII")
    env_cand = make("kaggriculture", configuration={"seed": seed})
    env_cand.run([lambda o, c=None: cand_agent.act(o, c), lambda o, c=None: dmit_cand.act(o, c)])
    
    print(f"{'Step':4s} | {'Base Money':10s} | {'Cand Money':10s} | {'Diff(Cand - Base)':18s} | {'Base Sells':20s} | {'Cand Sells':20s}")
    print("-" * 90)
    for s in range(712, 720):
        m_base = env_base.steps[s][0]["observation"]["farms"][0]["money"]
        m_cand = env_cand.steps[s][0]["observation"]["farms"][0]["money"]
        diff = m_cand - m_base
        
        act_base = env_base.steps[s][0].get("action") or {}
        act_cand = env_cand.steps[s][0].get("action") or {}
        mkt_base = act_base.get("market", [])
        mkt_cand = act_cand.get("market", [])
        
        print(f"{s:4d} | {m_base:10.1f} | {m_cand:10.1f} | {diff:+18.1f} | {str(mkt_base)[:20]:20s} | {str(mkt_cand)[:20]:20s}")
        
    # Check shed and carried at 718 and 719
    priv_base_718 = env_base.steps[718][0]["observation"]["private"]
    priv_cand_718 = env_cand.steps[718][0]["observation"]["private"]
    priv_base_719 = env_base.steps[719][0]["observation"]["private"]
    priv_cand_719 = env_cand.steps[719][0]["observation"]["private"]
    
    print("\n--- Step 718 Shed / Carried ---")
    print("Base Shed 718:", priv_base_718["shed"])
    print("Cand Shed 718:", priv_cand_718["shed"])
    print("Base Carried 718:", [dict(inv) for inv in priv_base_718["inventories"] if any(v > 0 for v in inv.values())])
    print("Cand Carried 718:", [dict(inv) for inv in priv_cand_718["inventories"] if any(v > 0 for v in inv.values())])
    
    print("\n--- Step 719 Shed / Carried ---")
    print("Base Shed 719:", priv_base_719["shed"])
    print("Cand Shed 719:", priv_cand_719["shed"])
    print("Base Carried 719:", [dict(inv) for inv in priv_base_719["inventories"] if any(v > 0 for v in inv.values())])
    print("Cand Carried 719:", [dict(inv) for inv in priv_cand_719["inventories"] if any(v > 0 for v in inv.values())])

    # Check what was executed at step 718 in market
    print("\n--- Market Orders at Step 718 ---")
    print("Base Action 718 Market:", env_base.steps[718][0]["action"].get("market"))
    print("Cand Action 718 Market:", env_cand.steps[718][0]["action"].get("market"))

if __name__ == "__main__":
    analyze_regression(249677)
