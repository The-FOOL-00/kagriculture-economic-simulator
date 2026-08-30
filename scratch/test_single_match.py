import os
import sys
from kaggle_environments import make

def test():
    cfg = {"episodeSteps": 720, "seed": 1000}
    env = make("kaggriculture", configuration=cfg, debug=True)
    
    agent0 = "generated_agents_1_32_7/apex_base.py"
    agent1 = "agents/ground_truth_control_current_engine.py"
    
    env.run([agent0, agent1])
    print("Steps:", len(env.steps))
    print("Agent0 cash:", env.steps[-1][0].observation["farms"][0]["money"])
    print("Agent1 cash:", env.steps[-1][1].observation["farms"][1]["money"])
    print("Agent0 shed:", env.steps[-1][0].observation["private"]["shed"])
    print("Agent0 tiles with pastures:", sum(1 for row in env.steps[-1][0].observation["farms"][0]["tiles"] for t in row if isinstance(t, dict) and t.get("kind") == "PASTURE"))

if __name__ == "__main__":
    test()
