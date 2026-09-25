import sys
import os
sys.path.insert(0, '.')
sys.path.insert(0, './scripts')
import copy
from kaggle_environments import make
import kaggle_environments.envs.kaggriculture.kaggriculture as kg
from scripts.v32_common import load_agent

def run_parity_check(seed=249635):
    # Run official kaggle_environments
    env_official = make('kaggriculture', configuration={'seed': seed})
    a = load_agent('E2_A7')
    b = load_agent('E0_V3')
    
    env_official.run([lambda o, c=None: a.act(o, c), lambda o, c=None: b.act(o, c)])
    
    official_steps = env_official.steps
    print(f"Official run finished. Total steps recorded: {len(official_steps)}")
    official_r0 = official_steps[-1][0]["reward"]
    official_r1 = official_steps[-1][1]["reward"]
    print(f"Official r0={official_r0}, r1={official_r1}")
    
    # Now run DirectEngine
    # Recreate the exact environment configuration from official
    cfg = env_official.configuration
    
    # We will reset agents fresh
    a_dir = load_agent('E2_A7')
    b_dir = load_agent('E0_V3')
    
    class StateWrapper:
        def __init__(self, raw_env):
            # kaggle_environments creates state list of AgentState objects
            pass

    # Let's inspect env_official._interpreter
    # In kaggle_environments, make('kaggriculture') uses kg.interpreter
    # Let's verify what env_official passes to interpreter
    return official_r0, official_r1

if __name__ == '__main__':
    run_parity_check()
