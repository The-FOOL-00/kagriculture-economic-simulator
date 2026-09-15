import os, sys, importlib.util
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

pe = pd.read_csv('experiments/EXP-DEV-004/PLAN_EVENTS.csv')
pe['match'] = [0 if i % 8 < 4 else 1 for i in range(len(pe))]
deltas = pd.read_csv('experiments/EXP-DEV-004/PAIRED_DELTAS.csv')

losses = deltas[deltas['outcome'] == 'LOSS'].sort_values('seed')

loss_table = []

for _, row in losses.iterrows():
    s = int(row['seed'])
    sub_pe = pe[(pe['seed'] == s) & (pe['match'] == 0)]
    
    # Trace match 0
    g = kagsim.Game(s)
    cand = Dev004JointMacroScheduler(seat=0, seed=s)
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)
    
    cand_purchases_pre_rev = []
    first_div_step = None
    step_rev = None
    post_rev_plan = None
    first_econ_div_after_rev = None
    
    step = 0
    while not g.done:
        o0 = g.observe(0)
        o1 = g.observe(1)
        a0 = cand.act(o0)
        a1 = base.agent(o1)
        
        # Check plan history
        # Has reversal occurred?
        rev_now = False
        if len(cand.decision_events) >= 2:
            prev_e = cand.decision_events[-2]
            curr_e = cand.decision_events[-1]
            if prev_e['selected_plan'] != 'BASELINE_BACKBONE' and curr_e['selected_plan'] == 'BASELINE_BACKBONE':
                if step_rev is None and step >= curr_e['step']:
                    step_rev = curr_e['step']
                    post_rev_plan = curr_e['selected_plan']
        
        if step_rev is None:
            for m in a0.get('market', []):
                if m[0].startswith('BUY'):
                    cand_purchases_pre_rev.append((step, m))
        else:
            m0 = o0['farms'][0]['money']
            m1 = o0['farms'][1]['money']
            if first_econ_div_after_rev is None and step > step_rev and m0 != m1:
                first_econ_div_after_rev = (step, m0 - m1)
                
        g.step(a0, a1)
        step += 1
        
    cand_rew = float(g.reward(0))
    base_rew = float(g.reward(1))
    
    # Initial plan
    plans = sub_pe['selected_plan'].tolist()
    steps = sub_pe['step'].tolist()
    
    # First activation step
    first_act_step = None
    first_act_plan = None
    for st, pl in zip(steps, plans):
        if pl != 'BASELINE_BACKBONE':
            first_act_step = st
            first_act_plan = pl
            break
            
    reversal_occurred = step_rev is not None
    
    # Asset cost and exposure estimation
    # For seeds reversing at 144: between 72 and 144, candidate bought wheat seed, strawberry seed, fertilizer, wheat product
    # Strawberry seed cost = 100 per seed.
    asset_desc = []
    asset_cost = 0.0
    for st, p in cand_purchases_pre_rev:
        if p[0] == 'BUY_SEED' and p[1] == 'STRAWBERRY':
            qty = int(p[2])
            cost = qty * 100.0
            asset_cost += cost
            asset_desc.append(f"STRAWBERRY_SEEDx{qty}@{st}")
        elif p[0] == 'BUY_ANIMAL':
            qty = int(p[2])
            unit_c = 400.0 if p[1] == 'COW' else 250.0
            cost = qty * unit_c
            asset_cost += cost
            asset_desc.append(f"{p[1]}x{qty}@{st}")
            
    if not asset_desc:
        asset_desc_str = "NONE"
    else:
        asset_desc_str = ";".join(asset_desc)
        
    entry = {
        "seed": s,
        "baseline_reward": row['match0_base_p1'],
        "candidate_reward": row['match0_cand_p0'],
        "delta": row['match0_delta'],
        "paired_delta": row['paired_mean_delta'],
        "initial_candidate_plan": "BASELINE_BACKBONE",
        "first_activation_step": first_act_step if first_act_step is not None else "NONE",
        "first_activation_plan": first_act_plan if first_act_plan is not None else "NONE",
        "reversal_occurred": reversal_occurred,
        "reversal_step": step_rev if step_rev is not None else "NONE",
        "post_reversal_plan": post_rev_plan if post_rev_plan is not None else "NONE",
        "commitment_event": f"Route specialization execution at Step {first_act_step}" if first_act_step else "NONE",
        "asset_purchased": asset_desc_str,
        "asset_cost": asset_cost,
        "estimated_sunk_exposure": asset_cost,
        "first_econ_div_after_reversal": f"Step {first_econ_div_after_rev[0]} (Diff {first_econ_div_after_rev[1]:.1f})" if first_econ_div_after_rev else "NONE",
        "final_plan": plans[-1],
        "final_delta": row['paired_mean_delta']
    }
    loss_table.append(entry)

df_losses = pd.DataFrame(loss_table)
print(df_losses.to_string())
with open('scratch/loss_table.json', 'w') as f:
    json.dump(loss_table, f, indent=2)
