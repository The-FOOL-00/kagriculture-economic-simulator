import os
import sys
import importlib.util

def load_module(path):
    spec = importlib.util.spec_from_file_location("mod", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

from kaggle_environments import make

def test_step():
    cfg = {"episodeSteps": 720, "seed": 1000}
    env = make("kaggriculture", configuration=cfg, debug=True)
    env.reset()
    
    obs0 = env.steps[0][0].observation
    print("Obs keys:", list(obs0.keys()))
    
    gt = load_module("agents/ground_truth_control_current_engine.py")
    ab = load_module("generated_agents_1_32_7/apex_base.py")
    
    act_gt = gt.agent(obs0)
    print("GT Action:", act_gt)
    
    act_ab = ab.agent(obs0)
    print("AB Action:", act_ab)

if __name__ == "__main__":
    test_step()
