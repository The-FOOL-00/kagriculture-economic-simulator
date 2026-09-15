"""Check exact sell order quantities submitted by V2."""
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

# Print every sell order in first 30 steps and last 10 steps
print("=== V2 SELL ORDERS (steps 0-50) ===")
for _ in range(51):
    obs = g.observe(0)
    obs_dm = g.observe(1)
    act = a.act(obs)
    act_dm = dmitrii_fn(obs_dm)
    
    for order in act.get('market', []):
        if order and order[0] == 'SELL':
            shed = obs['private']['shed']
            comm = order[1]
            qty = order[2] if len(order) > 2 else '?'
            price = obs['market']['prices'].get(comm, '?')
            shed_qty = shed.get(comm, 0)
            print(f"  step {step:3d} day={step//24} hr={step%24}: SELL {comm} qty={qty} price={price} shed={shed_qty}")
    
    g.step(act, act_dm)
    step += 1

# Check how many sell orders per step on average
print("\n=== Rerun from scratch: count sell orders ===")
g2 = kagsim.Game(seed)
a2 = ClosedLoopAgentV2()
step = 0
total_sells = 0
steps_with_sell = 0
max_qty_per_sell = 0
while not g2.done:
    obs = g2.observe(0)
    obs_dm = g2.observe(1)
    act = a2.act(obs)
    act_dm = dmitrii_fn(obs_dm)
    
    step_sells = [o for o in act.get('market', []) if o and o[0] == 'SELL']
    if step_sells:
        steps_with_sell += 1
        for s in step_sells:
            qty = s[2] if len(s) > 2 else 1
            total_sells += qty
            if qty > max_qty_per_sell:
                max_qty_per_sell = qty
    
    g2.step(act, act_dm)
    step += 1

print(f"Total steps: {step}")
print(f"Steps with sell: {steps_with_sell}")
print(f"Total sell quantity accumulated: {total_sells}")
print(f"Max qty in single SELL order: {max_qty_per_sell}")
print(f"Avg qty per sell step: {total_sells/steps_with_sell:.1f}" if steps_with_sell else "N/A")

# Key insight: what is the simulator's actual cash flow?
# Cash goes from 3000 to 93010 = +90010 net
# That means actual net income = 90010
# Our claimed sell revenue is 8M -> something is very wrong with qty tracking
print()
print(f"Net actual income: {93010-3000}")
print("This vs claimed sell rev of 8M means sells are being COUNTED not EXECUTED")
print("I.e., the SELL orders submitted to the market are not actually filling that much")
print("The market likely has a limited sell queue or the sells are on the action tape repeatedly")
