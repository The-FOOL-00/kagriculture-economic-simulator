# SPDX-License-Identifier: MIT
import os, sys, copy
sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("extracted_agents/dmitrii_lb2800"))
from kaggle_environments import make
from scripts.v32_common import load_agent
import terminal_planner as dmit_planner

def test_a7_schedule_prediction(seed=249677):
    a7 = load_agent("E9_AST")
    dmit = load_agent("E8_DMITRII")
    env = make("kaggriculture", configuration={"seed": seed})
    env.run([lambda o, c=None: a7.act(o, c), lambda o, c=None: dmit.act(o, c)])
    
    ground_truth_actions = [env.steps[s][0]["action"] for s in range(712, 719)]
    
    a7_fresh = load_agent("E9_AST")
    for s in range(712):
        obs = env.steps[s][0]["observation"]
        act = a7_fresh.act(obs)
        
    obs_712 = env.steps[712][0]["observation"]
    config = env.configuration
    seat = int(obs_712.get("player", 0))
    
    a7_clone = copy.deepcopy(a7_fresh)
    
    predicted_actions = []
    projected = copy.deepcopy(obs_712)
    for step in range(712, 719):
        projected["step"] = step
        projected["day"] = step // 24
        projected["hour"] = step % 24
        act = a7_clone.act(projected)
        predicted_actions.append(copy.deepcopy(act))
        
        # Transition shadow state
        run = dmit_planner.simulate(projected, config, [act])
        projected["farms"][seat] = run["farm"]
        projected["private"] = run["private"]
        
    matches = 0
    for idx, (gt, pr) in enumerate(zip(ground_truth_actions, predicted_actions)):
        eq = (gt == pr)
        if eq:
            matches += 1
        print(f"Step {712+idx}: Match={eq}")
        if not eq:
            print("  GT:", gt)
            print("  PR:", pr)
            
    print(f"Total matched with simulated shadow transition: {matches} / 7")

if __name__ == "__main__":
    test_a7_schedule_prediction(249677)
