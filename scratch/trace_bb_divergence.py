import os
import sys
import importlib.util
import pandas as pd
import json

base_dir = r"c:\Users\Sundareswaran\Kagriculture"
sys.path.insert(0, os.path.join(base_dir, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(base_dir, "candidates", "closed_loop_architecture"))

import kagsim
from dev_004_joint_macro_scheduler import Dev004JointMacroScheduler, BASELINE_PATH

spec = importlib.util.spec_from_file_location("base_check", BASELINE_PATH)
base_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base_mod)

deltas = pd.read_csv('experiments/EXP-DEV-004/PAIRED_DELTAS.csv')
bb_nonzero_seeds = [246003, 246005, 246007, 246022, 246026, 246028, 246030, 246032, 246034, 246035, 246036, 246039, 246042, 246049]

results = []

for seed in bb_nonzero_seeds:
    row = deltas[deltas['seed'] == seed].iloc[0]
    
    # We will simulate Match 0: Candidate is Seat 0, Baseline is Seat 1
    # We will also run a counterfactual Baseline in Seat 0 to find the first step where Candidate(0) deviates from Baseline(0)
    g = kagsim.Game(seed)
    cand = Dev004JointMacroScheduler(seat=0, seed=seed)
    base_seat1 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base_seat1)
    base_seat0_cf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base_seat0_cf)
    
    first_div_step = None
    first_div_cand_act = None
    first_div_base_act = None
    first_econ_div_step = None
    first_econ_div_cash_diff = None
    
    step = 0
    while not g.done:
        o0 = g.observe(0)
        o1 = g.observe(1)
        
        a0_cand = cand.act(o0)
        a1_base = base_seat1.agent(o1)
        
        # What would baseline have done in seat 0 given the current observation o0?
        # Note: up until divergence, o0 is identical to baseline's o0.
        if first_div_step is None:
            a0_base = base_seat0_cf.agent(o0)
            if a0_cand != a0_base:
                first_div_step = step
                first_div_cand_act = a0_cand
                first_div_base_act = a0_base
        
        # Check cash difference between candidate seat 0 and baseline seat 1?
        # Or compare candidate seat 0 money against baseline seat 0 if run in self-play?
        # In Match 0, candidate is seat 0, baseline is seat 1.
        # Both seats have identical initial conditions, but let's check when seat 0 money != seat 1 money:
        m0 = o0['farms'][0]['money']
        m1 = o0['farms'][1]['money']
        if first_econ_div_step is None and step >= 72 and m0 != m1:
            first_econ_div_step = step
            first_econ_div_cash_diff = m0 - m1
            
        g.step(a0_cand, a1_base)
        step += 1
        
    cand_rew = float(g.reward(0))
    base_rew = float(g.reward(1))
    
    results.append({
        "seed": seed,
        "cand_rew": cand_rew,
        "base_rew": base_rew,
        "delta": cand_rew - base_rew,
        "paired_delta": row['paired_mean_delta'],
        "cand_selected_plan_step72": [e['selected_plan'] for e in cand.decision_events],
        "first_div_step": first_div_step,
        "first_div_cand_act": str(first_div_cand_act),
        "first_div_base_act": str(first_div_base_act),
        "first_econ_div_step": first_econ_div_step,
        "first_econ_div_cash_diff": first_econ_div_cash_diff
    })

df_res = pd.DataFrame(results)
print(df_res[['seed', 'cand_rew', 'base_rew', 'delta', 'paired_delta', 'first_div_step', 'first_econ_div_step']])
for r in results:
    print(f"\nSeed {r['seed']}: plans={r['cand_selected_plan_step72']}")
    print(f"  First div step: {r['first_div_step']}")
    print(f"  Cand act: {r['first_div_cand_act']}")
    print(f"  Base act: {r['first_div_base_act']}")
    print(f"  First econ div step: {r['first_econ_div_step']} (diff: {r['first_econ_div_cash_diff']})")
