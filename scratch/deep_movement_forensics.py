"""
Deep Forensic Movement Decomposition & Contention Analysis
==========================================================
Instruments Frozen V2 and CL-Commitment-V1 across 720 steps to:
1. Test contention mechanisms A-J (physical collision, same-target contention, route overlap, etc.)
2. Decompose every single movement step into 10 forensic categories
3. Measure commitment persistence, duration, target/zone switches, and shed visits
4. Analyze route continuity, Manhattan lower bound ratios, direction reversals, and chain efficiency
"""

import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
import json
import numpy as np
from collections import defaultdict, deque

from candidates.slot2_aethel_refined_v2 import agent as v2_agent
from candidates.candidate_closed_loop_commitment_v1 import agent as comm_agent

SHED_ACCESS = frozenset([(4, 4), (5, 4), (4, 5), (5, 5)])
WELL_ACCESS = frozenset([(4, 5), (5, 5), (4, 6), (5, 6)])

def _dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def _quad(x, y):
    if x < 5 and y < 5: return "NW"
    if x >= 5 and y < 5: return "NE"
    if x < 5 and y >= 5: return "SW"
    return "SE"

def analyze_match_forensics(agent_fn, agent_name="Agent", seed=42):
    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    
    # Run full match against starter baseline
    env.run([agent_fn, "starter"])
    
    steps = env.steps
    total_steps = len(steps)
    
    # Metrics
    movement_categories = defaultdict(int)
    total_moves = 0
    total_productive = 0
    total_idle = 0
    
    # Contention tracking
    same_tile_occupancy = 0
    same_target_contention = 0
    shed_visits_total = 0
    
    # Route continuity tracking
    leg_lengths = []
    consecutive_same_zone = 0
    consecutive_same_row_col = 0
    total_transitions = 0
    transitions_within_2 = 0
    direction_reversals = 0
    direction_continuations = 0
    
    # Worker-specific tracking
    worker_last_pos = {}
    worker_last_dir = {}
    worker_zone_switches = defaultdict(int)
    
    for s_idx in range(1, total_steps):
        prev_farm = steps[s_idx-1][0]['observation']['farms'][0]
        curr_farm = steps[s_idx][0]['observation']['farms'][0]
        
        prev_farmer = tuple(prev_farm['farmer'])
        prev_hands = [tuple(h) for h in prev_farm['hands']]
        prev_workers = [prev_farmer] + prev_hands
        
        curr_farmer = tuple(curr_farm['farmer'])
        curr_hands = [tuple(h) for h in curr_farm['hands']]
        curr_workers = [curr_farmer] + curr_hands
        
        # Check multi-occupancy
        if len(curr_workers) != len(set(curr_workers)):
            same_tile_occupancy += 1
            
        # Check if multiple workers claimed exact same destination this step
        move_destinations = []
        for w_idx in range(min(len(prev_workers), len(curr_workers))):
            p0 = prev_workers[w_idx]
            p1 = curr_workers[w_idx]
            if p0 != p1:
                move_destinations.append(p1)
        if len(move_destinations) != len(set(move_destinations)):
            same_target_contention += 1
            
        for w_idx in range(min(len(prev_workers), len(curr_workers))):
            p0 = prev_workers[w_idx]
            p1 = curr_workers[w_idx]
            
            # Check move vs productive vs idle
            if p0 != p1:
                total_moves += 1
                dx = p1[0] - p0[0]
                dy = p1[1] - p0[1]
                curr_dir = (dx, dy)
                
                # Check direction continuity
                if w_idx in worker_last_dir:
                    last_dx, last_dy = worker_last_dir[w_idx]
                    if (dx, dy) == (last_dx, last_dy):
                        direction_continuations += 1
                    elif (dx, dy) == (-last_dx, -last_dy):
                        direction_reversals += 1
                worker_last_dir[w_idx] = curr_dir
                
                # Check zone crossing
                z0 = _quad(p0[0], p0[1])
                z1 = _quad(p1[0], p1[1])
                if z0 != z1:
                    worker_zone_switches[w_idx] += 1
                    
                # Classify move category
                if p1 in SHED_ACCESS:
                    movement_categories['return_to_shed'] += 1
                    shed_visits_total += 1
                elif p1 in WELL_ACCESS:
                    movement_categories['resource_pickup'] += 1
                elif z0 != z1:
                    movement_categories['zone_crossing'] += 1
                else:
                    movement_categories['productive_corridor'] += 1
            else:
                # Same position: either productive action or idle
                t_prev = prev_farm['tiles'][p0[1]][p0[0]] if 0 <= p0[1] < 10 and 0 <= p0[0] < 10 else None
                t_curr = curr_farm['tiles'][p0[1]][p0[0]] if 0 <= p0[1] < 10 and 0 <= p0[0] < 10 else None
                
                is_productive = False
                if t_prev != t_curr:
                    is_productive = True
                elif p0 in SHED_ACCESS or p0 in WELL_ACCESS:
                    is_productive = True
                    
                if is_productive:
                    total_productive += 1
                    if w_idx in worker_last_pos:
                        lp = worker_last_pos[w_idx]
                        d = _dist(lp, p0)
                        leg_lengths.append(d)
                        total_transitions += 1
                        if d <= 2:
                            transitions_within_2 += 1
                        if _quad(lp[0], lp[1]) == _quad(p0[0], p0[1]):
                            consecutive_same_zone += 1
                        if lp[0] == p0[0] or lp[1] == p0[1]:
                            consecutive_same_row_col += 1
                    worker_last_pos[w_idx] = p0
                else:
                    total_idle += 1
                    
    reward = float(steps[-1][0]['reward'] or 0)
    
    chain_efficiency = total_productive / max(1, total_moves)
    local_continuity = (transitions_within_2 / max(1, total_transitions)) * 100.0 if total_transitions else 0.0
    same_zone_pct = (consecutive_same_zone / max(1, total_transitions)) * 100.0 if total_transitions else 0.0
    same_row_col_pct = (consecutive_same_row_col / max(1, total_transitions)) * 100.0 if total_transitions else 0.0
    
    return {
        "agent": agent_name,
        "seed": seed,
        "reward": reward,
        "total_moves": total_moves,
        "total_productive": total_productive,
        "total_idle": total_idle,
        "chain_efficiency": float(chain_efficiency),
        "local_continuity_pct": float(local_continuity),
        "same_zone_pct": float(same_zone_pct),
        "same_row_col_pct": float(same_row_col_pct),
        "direction_continuations": direction_continuations,
        "direction_reversals": direction_reversals,
        "reversal_ratio": float(direction_reversals / max(1, direction_continuations + direction_reversals)),
        "same_tile_occupancy_steps": same_tile_occupancy,
        "same_target_contention_events": same_target_contention,
        "shed_visits_total": shed_visits_total,
        "movement_categories": dict(movement_categories),
        "mean_leg_length": float(np.mean(leg_lengths)) if leg_lengths else 0.0,
        "pct_1step": float(np.mean([1 if l == 1 else 0 for l in leg_lengths]) * 100.0) if leg_lengths else 0.0,
        "pct_2step": float(np.mean([1 if l <= 2 else 0 for l in leg_lengths]) * 100.0) if leg_lengths else 0.0,
    }

if __name__ == "__main__":
    print("=== Running Forensic Comparison: Frozen V2 vs Commitment-V1 ===")
    v2_res = analyze_match_forensics(v2_agent, "Frozen V2", seed=42)
    comm_res = analyze_match_forensics(comm_agent, "CL-Commitment-V1", seed=42)
    
    print("\n--- FORENSIC COMPARISON SUMMARY (Seed 42) ---")
    print(f"{'Metric':<35} | {'Frozen V2':<15} | {'CL-Commitment-V1':<15} | {'Delta':<12}")
    print("-" * 85)
    for k in ["reward", "total_productive", "total_moves", "total_idle", "chain_efficiency",
              "mean_leg_length", "pct_1step", "pct_2step", "local_continuity_pct",
              "same_zone_pct", "same_row_col_pct", "reversal_ratio", "same_tile_occupancy_steps",
              "same_target_contention_events", "shed_visits_total"]:
        v2_v = v2_res.get(k, 0)
        c_v = comm_res.get(k, 0)
        if isinstance(v2_v, float):
            delta = c_v - v2_v
            print(f"{k:<35} | {v2_v:15.2f} | {c_v:15.2f} | {delta:+12.2f}")
        else:
            delta = c_v - v2_v
            print(f"{k:<35} | {v2_v:15} | {c_v:15} | {delta:+12}")
            
    print("\n--- MOVEMENT CATEGORIES BREAKDOWN ---")
    print("Frozen V2 Movement Categories:", v2_res["movement_categories"])
    print("Commitment-V1 Movement Categories:", comm_res["movement_categories"])
