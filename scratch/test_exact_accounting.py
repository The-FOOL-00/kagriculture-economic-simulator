import sys
import os
import json
from collections import defaultdict
import numpy as np
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))

import candidates.candidate_cl_fert_gated as m1_module
from scratch.run_wheat_quota_sweep_50seeds import ParameterizedQuotaAgent
from scratch.run_pasture_causal_ablations_50seeds import MechanismAAgent

def audit_seed_exact_ledger(seed, agent_fn):
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    steps = env.run([agent_fn, "starter"])
    
    p = 0
    start_money = steps[0][p]["observation"]["farms"][p]["money"]
    
    # Track every credit and debit by comparing money between step start and end,
    # or by tracking the exact step-to-step farm money delta.
    revenue_by_item = defaultdict(float)
    seed_exp_by_crop = defaultdict(float)
    feed_exp = 0.0
    animal_exp_by_species = defaultdict(float)
    hire_exp = 0.0
    land_exp = 0.0
    
    for s_idx in range(1, len(steps)):
        prev_obs = steps[s_idx - 1][p]["observation"]
        curr_obs = steps[s_idx][p]["observation"]
        
        prev_farm = prev_obs["farms"][p]
        curr_farm = curr_obs["farms"][p]
        
        prev_priv = prev_obs.get("private") or {}
        curr_priv = curr_obs.get("private") or {}
        
        m_before = prev_farm["money"]
        m_after = curr_farm["money"]
        delta_m = m_after - m_before
        
        # We can extract exact transactions by looking at action and state changes
        act = steps[s_idx][p].get("action") or {}
        
        # Check hires: cost is mult * _fib(n_already_today)
        # Hires today count:
        hires_before = prev_farm.get("hires_today", 0)
        hires_after = curr_farm.get("hires_today", 0)
        # However, at end of day (step % 24 == 0), hires_today resets.
        # But hands count increases!
        # More directly: in step actions:
        # If action has "hire": wait, hire is a market order? Let's check how hire is invoked.
        pass

    # Let's inspect how kaggriculture applies actions and where money changes!
    return steps[-1][p]["reward"]

if __name__ == "__main__":
    print("Testing exact accounting ledger...")
