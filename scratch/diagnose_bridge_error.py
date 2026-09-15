"""Diagnose bridge accounting error."""
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

# Track cash changes vs claimed revenue
sells = []
total_sell_rev = 0.0
total_buy_cost = 0.0

# Run and record every sell action and its cash impact
all_cash = []  # cash BEFORE each step
all_cash_after = []  # cash AFTER each step

while not g.done:
    obs = g.observe(0)
    obs_dm = g.observe(1)
    act = a.act(obs)
    act_dm = dmitrii_fn(obs_dm)

    cash_before = float(obs['farms'][0].get('money', 0))
    prices = obs['market']['prices']
    
    step_sell_rev = 0.0
    step_buy_cost = 0.0
    for order in act.get('market', []):
        if not order: continue
        op = order[0]
        if op == 'SELL':
            comm = order[1]
            qty = order[2] if len(order) > 2 else 1
            price = prices.get(comm, 0)
            rev = qty * price
            step_sell_rev += rev
            sells.append((step, comm, qty, price, rev))
        elif op == 'BUY_SEED':
            crop = order[1]
            qty = order[2] if len(order) > 2 else 1
            price = prices.get(crop, 0)
            step_buy_cost += qty * price
        elif op == 'HIRE':
            step_buy_cost += 600  # approx
        elif op == 'BUY_LAND':
            step_buy_cost += 4000
        elif op == 'BUY_ANIMAL':
            animal = order[1]
            price = prices.get(animal, 0)
            step_buy_cost += price
        elif op == 'BUY_FEED':
            qty = order[1] if len(order) > 1 else 1
            step_buy_cost += qty * prices.get('WHEAT', 25)

    total_sell_rev += step_sell_rev
    total_buy_cost += step_buy_cost

    g.step(act, act_dm)
    obs_after = g.observe(0)
    cash_after = float(obs_after['farms'][0].get('money', 0))
    
    all_cash.append(cash_before)
    all_cash_after.append(cash_after)
    step += 1

final_cash = all_cash_after[-1]
sim_reward = float(g.reward(0))
start_cash = all_cash[0]

print(f"Start cash:          {start_cash:.0f}")
print(f"Final cash (obs):    {final_cash:.0f}")
print(f"Simulator reward:    {sim_reward:.0f}")
print(f"Total sell revenue:  {total_sell_rev:.0f}")
print(f"Total buy cost:      {total_buy_cost:.0f}")
print(f"Reconstructed:       {start_cash + total_sell_rev - total_buy_cost:.0f}")
print(f"Bridge error:        {start_cash + total_sell_rev - total_buy_cost - final_cash:.0f}")
print()
print(f"Total steps: {step}")
print(f"Total sell events: {len(sells)}")

# Check: does V2 sell same commodity many times?
from collections import Counter
sell_counts = Counter()
for s in sells:
    sell_counts[s[1]] += s[2]
print("Total units sold by commodity:", dict(sell_counts))

# Check first 5 cash deltas > 500
large_deltas = [(i, all_cash_after[i] - all_cash[i], all_cash[i], all_cash_after[i]) 
                for i in range(len(all_cash)) 
                if abs(all_cash_after[i] - all_cash[i]) > 200]
print()
print("Large cash deltas (>200):")
for i, delta, before, after in large_deltas[:20]:
    print(f"  step {i:3d} day={i//24}: {before:.0f} -> {after:.0f}  delta={delta:+.0f}")
