"""Investigate the 'other_unattributed' revenue - trace large cash deltas step by step."""
import sys, os, importlib.util
sys.path.insert(0, 'external_repos/kaggriculture-cppsim')
sys.path.insert(0, 'candidates/closed_loop_architecture')
DMITRII_DIR = 'extracted_agents/dmitrii_lb2800'
sys.path.insert(0, DMITRII_DIR)
spec = importlib.util.spec_from_file_location('dmitrii_agent', os.path.join(DMITRII_DIR, 'main.py'))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
dmitrii_fn = mod.agent

import kagsim
from closed_loop_v2 import ClosedLoopAgentV2

seed = 50000
g = kagsim.Game(seed)
a = ClosedLoopAgentV2()
step = 0

print("=== TRACING LARGE CASH DELTAS (>500) ===")
print("Step | Day | CashBefore -> CashAfter | ShedBefore | ShedAfter | ShedDelta | Actions")

while not g.done:
    obs = g.observe(0)
    obs_dm = g.observe(1)
    act = a.act(obs)
    act_dm = dmitrii_fn(obs_dm)

    cash_before = float(obs['farms'][0].get('money', 0))
    shed_before = dict(obs['private']['shed'])
    seeds_before = dict(obs['private']['seeds'])
    prices = dict(obs['market']['prices'])
    inventories = obs['private'].get('inventories', [])
    
    g.step(act, act_dm)
    
    obs_after = g.observe(0)
    cash_after = float(obs_after['farms'][0].get('money', 0))
    shed_after = dict(obs_after['private']['shed'])
    seeds_after = dict(obs_after['private']['seeds'])
    inventories_after = obs_after['private'].get('inventories', [])
    
    cash_delta = cash_after - cash_before
    
    if abs(cash_delta) > 500:
        # Compute shed delta for all commodities
        all_comm = set(list(shed_before.keys()) + list(shed_after.keys()))
        shed_delta_str = ', '.join(
            f"{c}:{shed_after.get(c,0)-shed_before.get(c,0):+d}"
            for c in sorted(all_comm)
            if shed_after.get(c,0) != shed_before.get(c,0)
        )
        seed_delta_str = ', '.join(
            f"{c}:{seeds_after.get(c,0)-seeds_before.get(c,0):+d}"
            for c in sorted(set(list(seeds_before.keys()) + list(seeds_after.keys())))
            if seeds_after.get(c,0) != seeds_before.get(c,0)
        )
        
        mkt_str = '; '.join(str(o) for o in act.get('market', []) if o)
        
        # Compute what shed delta would explain
        explained_rev = 0
        for comm in all_comm:
            delta = shed_after.get(comm, 0) - shed_before.get(comm, 0)
            if delta < 0:  # sold
                explained_rev += abs(delta) * prices.get(comm, 0)
        
        # Inventory change
        inv_change = ''
        if inventories or inventories_after:
            inv_b = inventories[0] if inventories else {}
            inv_a = inventories_after[0] if inventories_after else {}
            all_inv = set(list(inv_b.keys()) + list(inv_a.keys()))
            inv_delta = {k: inv_a.get(k, 0) - inv_b.get(k, 0) for k in all_inv if inv_a.get(k,0) != inv_b.get(k,0)}
            if inv_delta:
                inv_change = f" | INV_DELTA:{inv_delta}"
        
        print(f"Step {step:3d} Day{step//24}: cash {cash_before:.0f} -> {cash_after:.0f} (delta={cash_delta:+.0f})")
        print(f"  Shed delta: {shed_delta_str if shed_delta_str else 'NONE'}")
        print(f"  Seed delta: {seed_delta_str if seed_delta_str else 'NONE'}")
        print(f"  Explained by shed: {explained_rev:.0f}  (residual: {cash_delta - explained_rev:+.0f})")
        print(f"  Market orders: {mkt_str[:120]}")
        print(f"  {inv_change}")
    
    step += 1
    if step > 300:
        break
