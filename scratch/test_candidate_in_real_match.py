# SPDX-License-Identifier: MIT
import os, sys
sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("extracted_agents/dmitrii_lb2800"))
from kaggle_environments import make
from scripts.v32_common import load_agent
import terminal_planner as dmit_planner

def run_experiment(seed=249677):
    # 1. Baseline Match
    a7_base = load_agent("E9_AST")
    dmit_base = load_agent("E8_DMITRII")
    env_base = make("kaggriculture", configuration={"seed": seed})
    env_base.run([lambda o, c=None: a7_base.act(o, c), lambda o, c=None: dmit_base.act(o, c)])
    
    a7_base_cash = env_base.steps[-1][0]["reward"]
    dmit_base_cash = env_base.steps[-1][1]["reward"]
    
    # Extract baseline remaining at 712
    obs_712 = env_base.steps[712][0]["observation"]
    config = env_base.configuration
    a7_remaining = [env_base.steps[s][0]["action"] for s in range(712, 719)]
    
    # Generate terminal plan
    plan = dmit_planner.plan_terminal(obs_712, config, a7_remaining, max_simulations=128)
    print("Plan accepted:", plan.get("accepted"), "Reason:", plan.get("reason"))
    cand_actions = plan.get("actions")
    
    # 2. Candidate Match: Exact A7 on steps 0..711; on steps 712..718 use cand_actions[step - 712]
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
    
    a7_cand_cash = env_cand.steps[-1][0]["reward"]
    dmit_cand_cash = env_cand.steps[-1][1]["reward"]
    
    print("\n" + "=" * 80)
    print(f"CLOSED-LOOP EVALUATION ON SEED {seed}:")
    print(f"BASELINE:  A7 Cash = ${a7_base_cash:,.2f} | Dmitrii Cash = ${dmit_base_cash:,.2f} | Margin = {a7_base_cash - dmit_base_cash:+,.2f}")
    print(f"CANDIDATE: A7 Cash = ${a7_cand_cash:,.2f} | Dmitrii Cash = ${dmit_cand_cash:,.2f} | Margin = {a7_cand_cash - dmit_cand_cash:+,.2f}")
    print(f"PAIRED DELTA vs A7: ${a7_cand_cash - a7_base_cash:+,.2f}")
    print("=" * 80)

if __name__ == "__main__":
    run_experiment(249677)
