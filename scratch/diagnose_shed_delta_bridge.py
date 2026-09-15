"""
CORRECT BRIDGE APPROACH: Track cash changes directly.
The cash DELTA per step IS the revenue - costs. No need to reconstruct from sell orders.
Instead, track WHAT caused each cash delta (sell vs buy) using the action context.
"""
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

# Strategy: track shed changes to attribute revenue
# Revenue from commodity X = delta_shed[X] * price[X] when delta_shed[X] < 0 (shed decreases)
# Cost from BUY_SEED/BUY_ANIMAL/BUY_LAND/HIRE = explicit orders with prices

# Also: read cash deltas directly  
print("=== CASH DELTA APPROACH ===")
print("Track: cash_after - cash_before per step, correlated with shed changes and buy orders")
print()

step = 0
prev_cash = None
prev_shed = None

revenue_by_commodity = {}  # commodity -> total revenue
costs = {'seeds': 0, 'animals': 0, 'land': 0, 'labor': 0, 'feed': 0, 'other': 0}

total_cash_delta = 0.0

while not g.done:
    obs = g.observe(0)
    obs_dm = g.observe(1)
    act = a.act(obs)
    act_dm = dmitrii_fn(obs_dm)
    
    cash_before = float(obs['farms'][0].get('money', 0))
    shed_before = dict(obs['private']['shed'])
    prices = dict(obs['market']['prices'])
    
    g.step(act, act_dm)
    
    obs_after = g.observe(0)
    cash_after = float(obs_after['farms'][0].get('money', 0))
    shed_after = dict(obs_after['private']['shed'])
    
    cash_delta = cash_after - cash_before
    
    if abs(cash_delta) > 0.1:
        # Compute shed changes
        shed_delta = {k: shed_after.get(k, 0) - shed_before.get(k, 0) for k in set(list(shed_before.keys()) + list(shed_after.keys()))}
        
        # Revenue: commodities whose shed DECREASED (sold)
        step_rev = {}
        for comm, delta in shed_delta.items():
            if delta < 0:
                # Shed decreased -> likely sold
                step_rev[comm] = abs(delta) * prices.get(comm, 0)
                revenue_by_commodity[comm] = revenue_by_commodity.get(comm, 0) + step_rev[comm]
        
        # Cost from explicit buy orders in the action BEFORE this step
        # (already computed from obs at this step)
        step_buy_cost = 0
        for order in act.get('market', []):
            if not order: continue
            op = order[0]
            if op == 'BUY_SEED':
                crop = order[1]
                qty = order[2] if len(order) > 2 else 1
                # Actual cost = qty actually received (check seed delta)
                # Seeds are in obs['private']['seeds']
                seed_qty_before = obs['private']['seeds'].get(crop, 0)
                seed_qty_after = obs_after['private']['seeds'].get(crop, 0)
                actual_qty = max(0, seed_qty_after - seed_qty_before)
                cost = actual_qty * prices.get(crop, 0)
                costs['seeds'] += cost
                step_buy_cost += cost
            elif op == 'BUY_ANIMAL':
                animal = order[1]
                qty = order[2] if len(order) > 2 else 1
                cost = qty * prices.get(animal, 0)
                costs['animals'] += cost
                step_buy_cost += cost
            elif op == 'BUY_LAND':
                costs['land'] += 4000
                step_buy_cost += 4000
            elif op == 'HIRE':
                # Actual hire cost = check farm.hands count change
                hands_before = len(obs['farms'][0].get('hands', []))
                hands_after = len(obs_after['farms'][0].get('hands', []))
                new_hands = max(0, hands_after - hands_before)
                # HIRE cost is approx hires_today * daily_wage
                hires_today = obs['farms'][0].get('hires_today', 0)
                # Just use cash_delta minus revenue as proxy for now
            elif op == 'BUY_FEED':
                qty = order[1] if len(order) > 1 else 1
                cost = qty * prices.get('WHEAT', 25)
                costs['feed'] += cost
                step_buy_cost += cost
    
    step += 1

final_obs = g.observe(0)
final_cash = float(final_obs['farms'][0].get('money', 0))
sim_reward = float(g.reward(0))

print(f"Simulator reward:           {sim_reward:.0f}")
print(f"Start cash:                 3000")
print(f"Net income (sim):           {sim_reward - 3000:.0f}")
print()
print(f"Revenue reconstructed via shed deltas:")
total_rev = 0
for comm, rev in sorted(revenue_by_commodity.items(), key=lambda x: -x[1]):
    print(f"  {comm:15s}: {rev:>10.0f}")
    total_rev += rev
print(f"  {'TOTAL':15s}: {total_rev:>10.0f}")
print()
print(f"Costs reconstructed:")
for cat, cost in costs.items():
    print(f"  {cat:15s}: {cost:>10.0f}")
total_costs = sum(costs.values())
print(f"  {'TOTAL':15s}: {total_costs:>10.0f}")
print()
reconstructed = 3000 + total_rev - total_costs
print(f"Reconstructed final cash:   {reconstructed:.0f}")
print(f"Actual final cash:          {final_cash:.0f}")
print(f"Bridge error:               {reconstructed - final_cash:.0f}")
