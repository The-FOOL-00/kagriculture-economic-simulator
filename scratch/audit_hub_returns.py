"""
Phase 7: Harbor / Hub Return Forensics & Ablation
=================================================
Forensically analyzes every single shed visit across 720 steps for V2 and CL-Commitment:
1. Classifies returns into:
   - Necessary Produce Drop (batched >= 3 items or end of day)
   - Premature Produce Drop (1-2 items when tasks remain in quad)
   - Necessary Feed Pickup (morning hungry animals)
   - Necessary Animal Placement
   - Redundant/Unnecessary visits (visiting shed with 0 payload)
2. Implements Batched Hub Return Ablation
"""

import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
import json
import numpy as np
from collections import defaultdict

from candidates.slot2_aethel_refined_v2 import agent as v2_agent
from candidates.candidate_closed_loop_commitment_v1 import ClosedLoopCommitmentV1, _dist, SHED_ACCESS, PRODUCE_TO_DROP

def audit_agent_shed_returns(agent_fn, agent_name="Agent", seed=42):
    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.run([agent_fn, "starter"])
    steps = env.steps

    total_shed_visits = 0
    reasons = defaultdict(int)

    for s_idx in range(1, len(steps)):
        prev_farm = steps[s_idx-1][0]['observation']['farms'][0]
        curr_farm = steps[s_idx][0]['observation']['farms'][0]
        prev_priv = steps[s_idx-1][0]['observation'].get('private') or {}
        invs = prev_priv.get('inventories') or []
        shed = prev_priv.get('shed') or {}

        prev_w = [tuple(prev_farm['farmer'])] + [tuple(h) for h in prev_farm['hands']]
        curr_w = [tuple(curr_farm['farmer'])] + [tuple(h) for h in curr_farm['hands']]

        hour = s_idx % 24
        day = s_idx // 24

        for w_idx in range(min(len(prev_w), len(curr_w))):
            p0, p1 = prev_w[w_idx], curr_w[w_idx]
            if p0 != p1 and p1 in SHED_ACCESS and p0 not in SHED_ACCESS:
                total_shed_visits += 1
                inv = invs[w_idx] if w_idx < len(invs) else {}
                produce_load = sum(int(inv.get(it, 0) or 0) for it in PRODUCE_TO_DROP)
                cow_inv = int(inv.get("COW", 0) or 0)
                sheep_inv = int(inv.get("SHEEP", 0) or 0)
                w_inv = int(inv.get("WHEAT", 0) or 0)

                if (cow_inv + sheep_inv) > 0:
                    reasons["animal_handling"] += 1
                elif w_inv > 0:
                    reasons["wheat_carrying"] += 1
                elif produce_load >= 4 or hour >= 20:
                    reasons["batched_produce_drop"] += 1
                elif produce_load in (1, 2, 3):
                    reasons["premature_produce_drop"] += 1
                elif int(shed.get("WHEAT", 0) or 0) > 0 and hour <= 6:
                    reasons["feed_pickup"] += 1
                elif (int(shed.get("COW", 0) or 0) + int(shed.get("SHEEP", 0) or 0)) > 0:
                    reasons["animal_pickup"] += 1
                else:
                    reasons["unnecessary_transit"] += 1

    return {
        "agent": agent_name,
        "seed": seed,
        "total_shed_visits": total_shed_visits,
        "reasons": dict(reasons)
    }

if __name__ == "__main__":
    print("=== Analyzing Hub Returns for Frozen V2 vs CL-Commitment-V1 (Seed 42) ===")
    v2_hub = audit_agent_shed_returns(v2_agent, "Frozen V2", seed=42)
    comm_hub = audit_agent_shed_returns(ClosedLoopCommitmentV1(), "CL-Commitment-V1", seed=42)

    print("\n--- HUB RETURN REASONS BREAKDOWN ---")
    print(f"{'Category':<30} | {'Frozen V2':<12} | {'CL-Commitment-V1':<18} | {'Delta':<10}")
    print("-" * 75)
    all_keys = set(v2_hub["reasons"].keys()).union(set(comm_hub["reasons"].keys()))
    for k in sorted(all_keys):
        v = v2_hub["reasons"].get(k, 0)
        c = comm_hub["reasons"].get(k, 0)
        print(f"{k:<30} | {v:<12} | {c:<18} | {c-v:+10}")

    print("-" * 75)
    print(f"{'TOTAL SHED VISITS':<30} | {v2_hub['total_shed_visits']:<12} | {comm_hub['total_shed_visits']:<18} | {comm_hub['total_shed_visits'] - v2_hub['total_shed_visits']:+10}")
