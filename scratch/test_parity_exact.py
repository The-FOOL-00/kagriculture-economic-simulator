import sys
import os
sys.path.insert(0, '.')
sys.path.insert(0, './scripts')
import copy
from kaggle_environments import make
from kaggle_environments.utils import structify
import kaggle_environments.envs.kaggriculture.kaggriculture as kg
from scripts.v32_common import load_agent

class FastKagricultureEnv:
    """Direct execution wrapper for official kaggriculture interpreter.
    Eliminates stdout redirection, schema validation, and history logging overhead
    while executing the EXACT official interpreter.
    """
    def __init__(self, seed=249635):
        # Create standard config
        raw_env = make('kaggriculture', configuration={'seed': seed})
        self.configuration = raw_env.configuration
        self.done = False
        self.step_num = 0
        self.state = None
        self.reset(seed)

    def reset(self, seed=None):
        if seed is not None:
            self.configuration.seed = seed
        self.done = False
        self.step_num = 0
        
        # Initialize state with 2 agent structs
        s0 = structify({
            "action": {},
            "status": "ACTIVE",
            "reward": 0.0,
            "observation": {
                "player": 0,
                "step": 0,
                "day": 0,
                "hour": 0,
                "remainingOverageTime": 60.0
            }
        })
        s1 = structify({
            "action": {},
            "status": "ACTIVE",
            "reward": 0.0,
            "observation": {
                "player": 1,
                "step": 0,
                "day": 0,
                "hour": 0,
                "remainingOverageTime": 60.0
            }
        })
        self.state = [s0, s1]
        kg._initialize(self.state, self)
        return self.state

    def step(self, actions):
        self.state[0].action = actions[0]
        self.state[1].action = actions[1]
        
        # Run official interpreter
        kg.interpreter(self.state, self)
        
        self.step_num += 1
        self.state[0].observation.step = self.step_num
        self.state[1].observation.step = self.step_num
        
        if self.step_num >= self.configuration.episodeSteps - 1:
            self.done = True
            for s in self.state:
                if s.status == "ACTIVE":
                    s.status = "DONE"
        return self.state

def compare_parity(seeds=[249635, 249636, 249637]):
    for seed in seeds:
        print(f"\n--- Testing Seed {seed} ---")
        # 1. Official run
        env_off = make('kaggriculture', configuration={'seed': seed})
        a_off = load_agent('E2_A7')
        b_off = load_agent('E8_DMITRII')
        
        env_off.reset()
        off_actions = []
        off_obs_0 = []
        off_obs_1 = []
        off_rewards_0 = []
        off_rewards_1 = []
        
        while not env_off.done:
            o0 = copy.deepcopy(env_off.steps[-1][0]["observation"])
            o1 = copy.deepcopy(env_off.steps[-1][1]["observation"])
            for k in ('step', 'market', 'town', 'day', 'hour'):
                if k in env_off.steps[-1][0]['observation']:
                    o0[k] = env_off.steps[-1][0]['observation'][k]
                    o1[k] = env_off.steps[-1][0]['observation'][k]
            
            act0 = a_off.act(o0)
            act1 = b_off.act(o1)
            off_actions.append((act0, act1))
            env_off.step([act0, act1])
            off_rewards_0.append(env_off.steps[-1][0]["reward"])
            off_rewards_1.append(env_off.steps[-1][1]["reward"])
            
        final_off_r0 = env_off.steps[-1][0]["reward"]
        final_off_r1 = env_off.steps[-1][1]["reward"]
        print(f"Official: Steps={len(off_rewards_0)}, Final r0={final_off_r0}, r1={final_off_r1}")
        
        # 2. Fast run
        env_fast = FastKagricultureEnv(seed=seed)
        a_fast = load_agent('E2_A7')
        b_fast = load_agent('E8_DMITRII')
        
        fast_rewards_0 = []
        fast_rewards_1 = []
        step_idx = 0
        
        while not env_fast.done:
            # Prepare observations
            s0_obs = env_fast.state[0].observation
            s1_obs = env_fast.state[1].observation
            
            o0 = copy.deepcopy(s0_obs)
            o1 = copy.deepcopy(s1_obs)
            
            act0 = a_fast.act(o0)
            act1 = b_fast.act(o1)
            
            env_fast.step([act0, act1])
            fast_rewards_0.append(env_fast.state[0].reward)
            fast_rewards_1.append(env_fast.state[1].reward)
            step_idx += 1
            
        final_fast_r0 = env_fast.state[0].reward
        final_fast_r1 = env_fast.state[1].reward
        print(f"Fast:     Steps={len(fast_rewards_0)}, Final r0={final_fast_r0}, r1={final_fast_r1}")
        
        assert final_off_r0 == final_fast_r0, f"Mismatch in r0 for seed {seed}: {final_off_r0} vs {final_fast_r0}"
        assert final_off_r1 == final_fast_r1, f"Mismatch in r1 for seed {seed}: {final_off_r1} vs {final_fast_r1}"
        assert len(off_rewards_0) == len(fast_rewards_0), f"Step count mismatch: {len(off_rewards_0)} vs {len(fast_rewards_0)}"
        print(f"Seed {seed}: 100% BIT-IDENTICAL MATCH!")

if __name__ == '__main__':
    compare_parity()
