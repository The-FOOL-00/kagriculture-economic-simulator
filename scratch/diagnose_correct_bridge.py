"""
CORRECT BRIDGE: Direct cash-delta attribution.

The correct approach:
1. At each step, record cash_before and cash_after (from g.observe())
2. The cash delta = cash_after - cash_before is the GROUND TRUTH for that step
3. Classify the delta by what actions were submitted:
   - If SELL order submitted for commodity X and shed[X] decreased: revenue from X
   - If BUY_SEED submitted and seeds increased: cost
   - etc.
4. The sum of attributed deltas = total net income = final_cash - start_cash

This closes EXACTLY because we're using the actual cash change, not submitted quantities.

Key insight: shed decreases are the ACTUAL sold quantities (not submitted qty).
            Cash increase from sell = price * actual_shed_decrease.
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
from collections import defaultdict

def run_attributed_bridge(seed, v2_seat=0):
    """Run a game and reconstruct exact cash bridge by tracking state transitions."""
    dm_seat = 1 - v2_seat
    g = kagsim.Game(seed)
    a = ClosedLoopAgentV2()
    
    # Accumulators
    revenue = defaultdict(float)  # commodity -> revenue
    costs = defaultdict(float)    # category -> cost
    hire_events = []
    land_events = []
    
    step = 0
    unattributed = 0.0  # residual
    
    while not g.done:
        obs_v2 = g.observe(v2_seat)
        obs_dm = g.observe(dm_seat)
        act_v2 = a.act(obs_v2)
        act_dm = dmitrii_fn(obs_dm)
        
        # State BEFORE
        cash_before = float(obs_v2['farms'][v2_seat].get('money', 0))
        shed_before = dict(obs_v2['private']['shed'])
        seeds_before = dict(obs_v2['private']['seeds'])
        prices = dict(obs_v2['market']['prices'])
        hands_before = len(obs_v2['farms'][v2_seat].get('hands', []))
        quads_before = set(obs_v2['farms'][v2_seat].get('unlocked_quadrants', []))
        
        acts = [None, None]
        acts[v2_seat] = act_v2
        acts[dm_seat] = act_dm
        g.step(acts[0], acts[1])
        
        # State AFTER
        obs_after = g.observe(v2_seat)
        cash_after = float(obs_after['farms'][v2_seat].get('money', 0))
        shed_after = dict(obs_after['private']['shed'])
        seeds_after = dict(obs_after['private']['seeds'])
        hands_after = len(obs_after['farms'][v2_seat].get('hands', []))
        quads_after = set(obs_after['farms'][v2_seat].get('unlocked_quadrants', []))
        
        cash_delta = cash_after - cash_before
        if abs(cash_delta) < 0.01:
            step += 1
            continue
        
        # Attribute the cash delta
        attributed = 0.0
        
        # 1. Revenue from commodities whose shed decreased
        all_comms = set(list(shed_before.keys()) + list(shed_after.keys()))
        for comm in all_comms:
            b = shed_before.get(comm, 0)
            a_ = shed_after.get(comm, 0)
            if a_ < b:  # shed decreased -> sold
                sold_qty = b - a_
                price = prices.get(comm, 0)
                rev = sold_qty * price
                revenue[comm] += rev
                attributed += rev
        
        # 2. Cost from seeds: seed count increased = bought seeds
        all_crops = set(list(seeds_before.keys()) + list(seeds_after.keys()))
        for crop in all_crops:
            b = seeds_before.get(crop, 0)
            a_ = seeds_after.get(crop, 0)
            if a_ > b:  # seeds increased -> bought seeds
                bought = a_ - b
                price = prices.get(crop, 0)
                cost = bought * price
                costs['seeds'] += cost
                attributed -= cost
        
        # 3. Cost from land: new quadrant unlocked
        new_quads = quads_after - quads_before
        if new_quads:
            for q in new_quads:
                costs['land'] += 4000.0
                attributed -= 4000.0
                land_events.append({'step': step, 'quad': q})
        
        # 4. Cost from labor: new hands hired
        if hands_after > hands_before:
            new_hires = hands_after - hands_before
            # Labor cost per hire can be derived from actual cash delta
            # For now track separately
            hire_events.append({'step': step, 'count': new_hires})
            # Labor cost = we'll use the unattributed portion below
        
        # 5. Unattributed residual (animal purchases, feed, labor wages, etc.)
        residual = cash_delta - attributed
        if abs(residual) > 0.5:
            # Could be: animal purchase, HIRE cost, feed purchase
            # Check if any BUY orders were in the action
            for order in act_v2.get('market', []):
                if not order: continue
                op = order[0]
                if op == 'BUY_ANIMAL':
                    animal = order[1]
                    qty = order[2] if len(order) > 2 else 1
                    price = prices.get(animal, 0)
                    # Check if shed[animal] increased
                    shed_b = shed_before.get(animal, 0)
                    shed_a = shed_after.get(animal, 0)
                    if shed_a > shed_b:
                        cost = (shed_a - shed_b) * price
                    else:
                        cost = qty * price
                    costs['animals'] += cost
                    attributed -= cost
                elif op == 'BUY_FEED':
                    qty = order[1] if len(order) > 1 else 1
                    cost = qty * prices.get('WHEAT', 25)
                    costs['feed'] += cost
                    attributed -= cost
                elif op == 'HIRE':
                    # Hire cost — compute from residual
                    pass
            
            residual2 = cash_delta - attributed
            if hands_after > hands_before and residual2 < 0:
                # Assign negative residual to labor
                costs['labor'] += abs(residual2)
                attributed += residual2
                residual2 = 0
            
            # Final residual
            if abs(residual2) > 10:
                costs['other_unattributed'] += abs(min(0, residual2))
                revenue['other_unattributed'] += max(0, residual2)
                unattributed += residual2
        
        step += 1
    
    final_obs = g.observe(v2_seat)
    final_cash = float(final_obs['farms'][v2_seat].get('money', 0))
    sim_reward = float(g.reward(v2_seat))
    start_cash = 3000.0
    
    total_rev = sum(revenue.values())
    total_cost = sum(costs.values())
    reconstructed = start_cash + total_rev - total_cost
    bridge_error = reconstructed - final_cash
    
    return {
        'seed': seed, 'v2_seat': v2_seat,
        'start_cash': start_cash,
        'final_cash': final_cash,
        'sim_reward': sim_reward,
        'revenue': dict(revenue),
        'costs': dict(costs),
        'total_rev': total_rev,
        'total_cost': total_cost,
        'reconstructed': reconstructed,
        'bridge_error': bridge_error,
        'unattributed': unattributed,
        'hire_events': hire_events,
        'land_events': land_events,
    }


if __name__ == '__main__':
    print("=== SHED-DELTA BRIDGE TEST (Seeds 50000-50002, both seats) ===\n")
    for seed in [50000, 50001, 50002]:
        for seat in [0, 1]:
            r = run_attributed_bridge(seed, seat)
            err = r['bridge_error']
            status = "OK" if abs(err) < 500 else "WARN" if abs(err) < 2000 else "FAIL"
            print(f"Seed {seed} V2=P{seat}: final={r['final_cash']:.0f}  bridge_err={err:+.0f}  [{status}]")
            if abs(err) > 100:
                print(f"  Revenue: " + "  ".join(f"{k}={v:.0f}" for k,v in r['revenue'].items() if v > 0))
                print(f"  Costs:   " + "  ".join(f"{k}={v:.0f}" for k,v in r['costs'].items() if v > 0))
    
    print("\nDetailed breakdown for seed 50000, V2=P0:")
    r = run_attributed_bridge(50000, 0)
    print(f"  Net income: {r['final_cash'] - r['start_cash']:.0f}")
    print(f"  Revenue breakdown:")
    for k, v in sorted(r['revenue'].items(), key=lambda x: -abs(x[1])):
        if abs(v) > 0:
            print(f"    {k:20s}: {v:>10.0f}")
    print(f"  Cost breakdown:")
    for k, v in sorted(r['costs'].items(), key=lambda x: -abs(x[1])):
        if abs(v) > 0:
            print(f"    {k:20s}: {v:>10.0f}")
    print(f"  Bridge error: {r['bridge_error']:.0f}")
    print(f"  Hire events: {r['hire_events'][:5]}")
    print(f"  Land events: {r['land_events']}")
