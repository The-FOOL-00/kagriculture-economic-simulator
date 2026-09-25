# SPDX-License-Identifier: MIT
import os, sys
sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("extracted_agents/dmitrii_lb2800"))
from kaggle_environments import make
from scripts.v32_common import load_agent
import terminal_planner as dmit_planner

def test_a7_terminal_search(seed=249677):
    a7 = load_agent("E9_AST")
    dmitrii = load_agent("E8_DMITRII")
    env = make("kaggriculture", configuration={"seed": seed})
    
    # Run until step 712
    # We record A7 baseline actions for steps 712..718
    # To get A7's baseline remaining schedule:
    env.run([lambda o, c=None: a7.act(o, c), lambda o, c=None: dmitrii.act(o, c)])
    
    obs_712 = env.steps[712][0]["observation"]
    config = env.configuration
    
    # Extract A7's actual schedule from steps 712..718
    a7_remaining = [env.steps[s][0]["action"] for s in range(712, 719)]
    
    print("Testing Dmitrii plan_terminal on A7's step 712 state...")
    plan_dmit = dmit_planner.plan_terminal(obs_712, config, a7_remaining, max_simulations=128, passes=1, proposals_per_actor=8)
    print("Dmitrii planner result on A7:")
    print("  Accepted:", plan_dmit.get("accepted"))
    print("  Reason:", plan_dmit.get("reason"))
    print("  Simulations:", plan_dmit.get("simulations"))
    print("  Planning ms:", plan_dmit.get("planning_ms"))
    print("  Changes:", plan_dmit.get("changes"))
    cert = plan_dmit.get("certificate", {})
    print("  Sold unit delta:", cert.get("sold_unit_delta"))
    print("  Stock value gain:", cert.get("stock_value_gain_at_initial_prices"))

if __name__ == "__main__":
    test_a7_terminal_search(249677)
