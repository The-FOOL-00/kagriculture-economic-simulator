"""
Phase 5: Task-Graph Analysis & Ordering Discovery
=================================================
Constructs directed task graphs G = (V, E) for workers in V2 and CL-Commitment:
Nodes: productive chore events (position, kind, step)
Edges: transit legs between consecutive productive events
Weights: movement turns taken
Identifies path inefficiencies and classifies ordering decisions.
"""

import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
import json
import numpy as np
from collections import defaultdict

from candidates.slot2_aethel_refined_v2 import agent as v2_agent
from candidates.candidate_closed_loop_commitment_v1 import agent as comm_agent, _dist, _quad

def build_worker_task_graph(agent_fn, agent_name="Agent", seed=42):
    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.run([agent_fn, "starter"])
    steps = env.steps

    # worker_id -> list of (step, pos, chore_kind)
    worker_nodes = defaultdict(list)
    worker_edges = defaultdict(list) # (from_node, to_node, travel_steps, manhattan_dist)

    last_productive_node = {}
    current_moves_since_prod = defaultdict(int)

    for s_idx in range(1, len(steps)):
        prev_farm = steps[s_idx-1][0]['observation']['farms'][0]
        curr_farm = steps[s_idx][0]['observation']['farms'][0]
        prev_w = [tuple(prev_farm['farmer'])] + [tuple(h) for h in prev_farm['hands']]
        curr_w = [tuple(curr_farm['farmer'])] + [tuple(h) for h in curr_farm['hands']]

        for w_idx in range(min(len(prev_w), len(curr_w))):
            p0, p1 = prev_w[w_idx], curr_w[w_idx]
            if p0 != p1:
                current_moves_since_prod[w_idx] += 1
            else:
                t_prev = prev_farm['tiles'][p0[1]][p0[0]] if 0 <= p0[1] < 10 and 0 <= p0[0] < 10 else None
                t_curr = curr_farm['tiles'][p0[1]][p0[0]] if 0 <= p0[1] < 10 and 0 <= p0[0] < 10 else None

                is_prod = (t_prev != t_curr) or (p0 in [(4, 4), (5, 4), (4, 5), (5, 5)])
                if is_prod:
                    kind = "SHED_EVENT"
                    if isinstance(t_curr, dict):
                        kind = t_curr.get("kind", "TILE_OP")

                    node = (s_idx, p0, kind)
                    worker_nodes[w_idx].append(node)

                    if w_idx in last_productive_node:
                        prev_n = last_productive_node[w_idx]
                        travel_steps = current_moves_since_prod[w_idx]
                        m_dist = _dist(prev_n[1], p0)
                        worker_edges[w_idx].append({
                            "from_step": prev_n[0],
                            "from_pos": prev_n[1],
                            "to_step": s_idx,
                            "to_pos": p0,
                            "travel_steps": travel_steps,
                            "manhattan_dist": m_dist,
                            "excess_travel": max(0, travel_steps - m_dist)
                        })

                    last_productive_node[w_idx] = node
                    current_moves_since_prod[w_idx] = 0

    all_edges = [e for edges in worker_edges.values() for e in edges]
    total_travel_steps = sum(e["travel_steps"] for e in all_edges)
    total_manhattan_dist = sum(e["manhattan_dist"] for e in all_edges)
    total_excess_travel = sum(e["excess_travel"] for e in all_edges)

    path_efficiency = total_manhattan_dist / max(1, total_travel_steps)

    # Edge weight distribution
    edge_weights = [e["travel_steps"] for e in all_edges]

    return {
        "agent": agent_name,
        "seed": seed,
        "total_nodes": sum(len(n) for n in worker_nodes.values()),
        "total_edges": len(all_edges),
        "total_travel_steps": total_travel_steps,
        "total_manhattan_dist": total_manhattan_dist,
        "total_excess_travel": total_excess_travel,
        "path_efficiency": float(path_efficiency),
        "mean_edge_weight": float(np.mean(edge_weights)) if edge_weights else 0.0,
        "pct_1step_edge": float(np.mean([1 if w == 1 else 0 for w in edge_weights]) * 100.0) if edge_weights else 0.0,
        "pct_2step_edge": float(np.mean([1 if w <= 2 else 0 for w in edge_weights]) * 100.0) if edge_weights else 0.0,
    }

if __name__ == "__main__":
    print("=== Task-Graph Comparison: Frozen V2 vs CL-Commitment-V1 (Seed 42) ===")
    v2_tg = build_worker_task_graph(v2_agent, "Frozen V2", seed=42)
    comm_tg = build_worker_task_graph(comm_agent, "CL-Commitment-V1", seed=42)

    print(f"{'Metric':<30} | {'Frozen V2':<15} | {'CL-Commitment-V1':<15} | {'Delta':<10}")
    print("-" * 75)
    for k in ["total_nodes", "total_edges", "total_travel_steps", "total_manhattan_dist",
              "total_excess_travel", "path_efficiency", "mean_edge_weight", "pct_1step_edge", "pct_2step_edge"]:
        v = v2_tg.get(k, 0)
        c = comm_tg.get(k, 0)
        if isinstance(v, float):
            print(f"{k:<30} | {v:15.3f} | {c:15.3f} | {c-v:+10.3f}")
        else:
            print(f"{k:<30} | {v:15} | {c:15} | {c-v:+10}")
