import sys, os
sys.path.insert(0, os.path.abspath("."))
import json
import copy
from typing import Dict, Any, List

from research.v40.env.fast_sim import FastKagricultureSim
import kaggle_environments.envs.kaggriculture.kaggriculture as kg
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

# Wrap _apply_unit_action to log no-ops
orig_apply = kg._apply_unit_action

blocked_events = []

def instrumented_apply(farm, private, idx, action, board_size, day, turns_per_day, shed_capacity=100):
    if not isinstance(action, list) or not action:
        return orig_apply(farm, private, idx, action, board_size, day, turns_per_day, shed_capacity)
    op = action[0]
    if op == "PASS":
        return orig_apply(farm, private, idx, action, board_size, day, turns_per_day, shed_capacity)
        
    pos = kg._farmer_position(farm, idx)
    fx, fy = pos[0], pos[1] if pos else (-1, -1)
    tile_before = copy.deepcopy(farm["tiles"][fy][fx]) if pos else None
    inv_before = copy.deepcopy(kg._farmer_inventory(private, idx))
    shed_before = copy.deepcopy(private["shed"])
    seeds_before = copy.deepcopy(private["seeds"])
    
    # Run original
    orig_apply(farm, private, idx, action, board_size, day, turns_per_day, shed_capacity)
    
    pos_after = kg._farmer_position(farm, idx)
    tile_after = farm["tiles"][fy][fx] if pos else None
    inv_after = kg._farmer_inventory(private, idx)
    shed_after = private["shed"]
    seeds_after = private["seeds"]
    
    # Check if anything changed
    changed = False
    if pos != pos_after:
        changed = True
    elif tile_before != tile_after:
        changed = True
    elif inv_before != inv_after:
        changed = True
    elif shed_before != shed_after:
        changed = True
    elif seeds_before != seeds_after:
        changed = True
        
    if not changed:
        reason = "UNKNOWN"
        if op in kg.FARMER_MOVES:
            reason = "MOVE_OUT_OF_BOUNDS"
        elif op == "PLANT":
            if tile_before == "LOCKED":
                reason = "TILE_LOCKED"
            elif tile_before is not None:
                reason = f"TILE_OCCUPIED_{tile_before.get('kind') if isinstance(tile_before, dict) else tile_before}"
            elif seeds_before.get(action[1], 0) <= 0:
                reason = "NO_SEEDS"
        elif op == "WATER":
            if not (isinstance(tile_before, dict) and tile_before.get("kind") == "PLANT"):
                reason = "NOT_A_PLANT"
            elif tile_before.get("watered_today"):
                reason = "ALREADY_WATERED"
        elif op == "FEED":
            if not (isinstance(tile_before, dict) and "animal" in tile_before):
                reason = "NOT_AN_ANIMAL"
            elif tile_before.get("fed_today"):
                reason = "ALREADY_FED"
            elif shed_before.get("WHEAT", 0) <= 0:
                reason = "NO_WHEAT_IN_SHED"
        elif op == "CARE":
            if not (isinstance(tile_before, dict) and "animal" in tile_before):
                reason = "NOT_AN_ANIMAL"
            elif tile_before.get("cared_today"):
                reason = "ALREADY_CARED"
        elif op == "HARVEST":
            if not (isinstance(tile_before, dict) and tile_before.get("kind") == "PLANT"):
                reason = "NOT_A_PLANT"
            elif tile_before.get("yield_units", 0) <= 0:
                reason = "ZERO_YIELD"
        elif op == "COLLECT":
            if not (isinstance(tile_before, dict) and "animal" in tile_before):
                reason = "NOT_AN_ANIMAL"
            elif tile_before.get("yield_units", 0) <= 0:
                reason = "ZERO_YIELD"
        elif op == "PICKUP":
            if not kg._is_shed_adjacent((fx, fy), board_size):
                reason = "NOT_SHED_ADJACENT"
            elif shed_before.get(action[1], 0) <= 0:
                reason = "ITEM_NOT_IN_SHED"
        elif op == "PLACE":
            if not (isinstance(tile_before, dict) and "animal" not in tile_before):
                reason = "TILE_NOT_EMPTY_STRUCTURE"
            elif inv_before.get(action[1], 0) <= 0:
                reason = "ITEM_NOT_IN_BACKPACK"
                
        blocked_events.append({
            "idx": idx,
            "action": action,
            "op": op,
            "pos": [fx, fy],
            "reason": reason,
            "tile": str(tile_before)
        })

kg._apply_unit_action = instrumented_apply

AUDIT_SEEDS = [250400 + i for i in range(16)]

stats_by_op = {}
stats_by_reason = {}

print("Auditing V49 for blocked / no-op actions across 16 matches...")
for s in AUDIT_SEEDS:
    blocked_events.clear()
    sim = FastKagricultureSim(seed=s)
    obs = sim.reset()
    for step in range(719):
        a0 = v49_mod.agent(obs[0], sim.configuration)
        a1 = v44_mod.agent(obs[1], sim.configuration)
        obs, _, done, _ = sim.step([a0, a1])
        if done:
            break
            
    for ev in blocked_events:
        op = ev["op"]
        reason = ev["reason"]
        stats_by_op[op] = stats_by_op.get(op, 0) + 1
        stats_by_reason[reason] = stats_by_reason.get(reason, 0) + 1

kg._apply_unit_action = orig_apply

print("\n=== BLOCKED ACTIONS BY OP ===")
for op, count in sorted(stats_by_op.items(), key=lambda x: -x[1]):
    print(f"  {op:<15}: {count} blocked events across 16 matches (avg {count/16:.1f}/match)")

print("\n=== BLOCKED ACTIONS BY REASON ===")
for r, count in sorted(stats_by_reason.items(), key=lambda x: -x[1]):
    print(f"  {r:<30}: {count} blocked events across 16 matches (avg {count/16:.1f}/match)")

os.makedirs("research/v55/analysis", exist_ok=True)
with open("research/v55/analysis/blocked_action_inventory.json", "w") as f:
    json.dump({
        "seeds_tested": len(AUDIT_SEEDS),
        "by_op": stats_by_op,
        "by_reason": stats_by_reason
    }, f, indent=2)

print("\nSaved research/v55/analysis/blocked_action_inventory.json")
