import sys
import os
sys.path.insert(0, os.path.abspath("."))
import copy
from kaggle_environments import make
import candidates.slot2_aethel_refined_v2 as v2
from scratch.v2_jit_melon_experiment import CANONICAL_JIT_TRACE

def make_handoff_agent(handoff_step):
    def agent(obs, config=None):
        step = obs.get("step")
        if step is None:
            step = int(obs.get("day", 0) * 24 + obs.get("hour", 0))
        else:
            step = int(step or 0)
            
        if step < handoff_step:
            if step >= 712:
                return v2._terminal_action(obs)
            return CANONICAL_JIT_TRACE[step]
        else:
            return v2.agent(obs, config)
    return agent

def robust(fn):
    def wrapped(obs, cfg=None):
        if obs.get("step") is None:
            obs["step"] = int(obs.get("day", 0) * 24 + obs.get("hour", 0))
        return fn(obs, cfg)
    return wrapped

test_steps = [24, 48, 72, 120, 240, 264, 265, 288, 336]
seed = 42

print(f"Testing handoff from H to V2 at various steps on seed {seed}...")
for hs in test_steps:
    agent_h = make_handoff_agent(hs)
    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env.run([robust(agent_h), robust(v2.agent)])
    
    r_cand = float(env.steps[-1][0]["reward"] or 0)
    r_v2 = float(env.steps[-1][1]["reward"] or 0)
    margin = r_cand - r_v2
    print(f"Handoff Step {hs:3d}: Candidate Reward = {r_cand:8.1f} | V2 Reward = {r_v2:8.1f} | Margin = {margin:+8.1f}")
