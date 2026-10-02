import sys, os
sys.path.insert(0, '.')
import copy
import json

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
from research.v57.canonical_transform import (
    get_transformations_for_step,
    verify_structural_invariants,
    evaluate_transformation
)

# Step 1: Capture V49 baseline market orders at steps of interest
def get_v49_market_orders_by_step(seed, seat=0):
    sim = FastKagricultureSim(seed=seed)
    obs = sim.reset(seed=seed)
    mkt_by_step = {}
    for step in range(719):
        a = v49_mod.agent(obs[seat])
        if isinstance(a, dict) and a.get('market'):
            mkt_by_step[step] = a['market']
        # step with dummy/pass
        obs, _, done, _ = sim.step([a, {}] if seat == 0 else [{}, a])
        if done: break
    return mkt_by_step

orders_250621 = get_v49_market_orders_by_step(250621)
orders_250617 = get_v49_market_orders_by_step(250617)

print("Orders at target steps for Seed 250621:")
for s in [693, 694, 696, 697, 698, 718]:
    if s in orders_250621:
        print(f"  Step {s} (len={len(orders_250621[s])}): {orders_250621[s]}")

print("\nOrders at target steps for Seed 250617:")
for s in [693, 694, 696, 697, 698, 718]:
    if s in orders_250617:
        print(f"  Step {s} (len={len(orders_250617[s])}): {orders_250617[s]}")
