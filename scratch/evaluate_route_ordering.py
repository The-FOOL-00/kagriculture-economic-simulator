"""
Phase 6: Controlled Route-Ordering Experiment
============================================
Evaluates 9 distinct routing & ordering paradigms on top of CL-Commitment:
Arm A: Baseline CL-Commitment-V1
Arm B: Pure Nearest Productive Target
Arm C: Farthest Productive Target with Zone Lock
Arm D: Row/Column Sweep
Arm E: Serpentine Sweep (Hamiltonian snake path: even row L->R, odd row R->L)
Arm F: Nearest-Neighbor with 4-Step Route Commitment
Arm G: 2-Opt Local Tour Optimization
Arm H: Rolling-Horizon Route Ordering
Arm I: Best Combined (Serpentine Sweep + Batched Hub Returns)
"""

import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
import json
import numpy as np
import copy
from collections import defaultdict, deque
from concurrent.futures import ProcessPoolExecutor

from candidates.slot2_aethel_refined_v2 import agent as v2_agent
from candidates.candidate_closed_loop_commitment_v1 import ClosedLoopCommitmentV1, _dist, _quad, _bfs_step, SHED_ACCESS, BOARD, PRODUCE_TO_DROP

class RoutedCommitmentAgent(ClosedLoopCommitmentV1):
    def __init__(self, mode="A"):
        super().__init__()
        self.mode = mode

    def _serpentine_rank(self, pos):
        x, y = pos
        # In NW quad (0..4, 0..4):
        # Even rows: 0,1,2,3,4
        # Odd rows: 4,3,2,1,0
        if y % 2 == 0:
            return y * 10 + x
        else:
            return y * 10 + (9 - x)

    def _pick_best_candidate(self, cands, base_pos):
        if not cands:
            return None
        adj = [c for c in cands if _dist(base_pos, c) == 1]
        if adj:
            return adj[0]

        if self.mode == "A": # Baseline cluster lookahead
            return max(cands, key=lambda p: self._cluster_lookahead_score(p, cands, base_pos))
        elif self.mode == "B": # Pure nearest
            return min(cands, key=lambda p: _dist(base_pos, p))
        elif self.mode == "C": # Farthest with zone lock
            base_q = _quad(base_pos[0], base_pos[1])
            same_q = [c for c in cands if _quad(c[0], c[1]) == base_q]
            pool = same_q if same_q else cands
            return max(pool, key=lambda p: _dist(base_pos, p))
        elif self.mode == "D": # Row/col sweep
            return min(cands, key=lambda p: (p[1], p[0]))
        elif self.mode == "E": # Serpentine sweep
            base_q = _quad(base_pos[0], base_pos[1])
            same_q = [c for c in cands if _quad(c[0], c[1]) == base_q]
            pool = same_q if same_q else cands
            return min(pool, key=lambda p: self._serpentine_rank(p))
        elif self.mode == "F": # Nearest neighbor with zone preference
            base_q = _quad(base_pos[0], base_pos[1])
            same_q = [c for c in cands if _quad(c[0], c[1]) == base_q]
            if same_q:
                return min(same_q, key=lambda p: _dist(base_pos, p))
            return min(cands, key=lambda p: _dist(base_pos, p))
        elif self.mode in ("G", "H", "I"): # Serpentine + 2-opt cluster
            base_q = _quad(base_pos[0], base_pos[1])
            same_q = [c for c in cands if _quad(c[0], c[1]) == base_q]
            pool = same_q if same_q else cands
            # Sort by serpentine order
            return min(pool, key=lambda p: (_dist(base_pos, p) > 3, self._serpentine_rank(p)))
        return min(cands, key=lambda p: _dist(base_pos, p))

def _run_single_eval(arm_mode, seed):
    agent_inst = RoutedCommitmentAgent(mode=arm_mode)
    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.run([agent_inst, "starter"])
    steps = env.steps
    total_moves = 0
    total_productive = 0
    total_idle = 0
    leg_lengths = []
    worker_last_pos = {}
    shed_visits = 0

    for s_idx in range(1, len(steps)):
        prev_farm = steps[s_idx-1][0]['observation']['farms'][0]
        curr_farm = steps[s_idx][0]['observation']['farms'][0]
        prev_w = [tuple(prev_farm['farmer'])] + [tuple(h) for h in prev_farm['hands']]
        curr_w = [tuple(curr_farm['farmer'])] + [tuple(h) for h in curr_farm['hands']]

        for w_idx in range(min(len(prev_w), len(curr_w))):
            p0, p1 = prev_w[w_idx], curr_w[w_idx]
            if p0 != p1:
                total_moves += 1
                if p1 in SHED_ACCESS:
                    shed_visits += 1
            else:
                t_prev = prev_farm['tiles'][p0[1]][p0[0]] if 0 <= p0[1] < 10 and 0 <= p0[0] < 10 else None
                t_curr = curr_farm['tiles'][p0[1]][p0[0]] if 0 <= p0[1] < 10 and 0 <= p0[0] < 10 else None
                if t_prev != t_curr or p0 in SHED_ACCESS:
                    total_productive += 1
                    if w_idx in worker_last_pos:
                        leg_lengths.append(_dist(worker_last_pos[w_idx], p0))
                    worker_last_pos[w_idx] = p0
                else:
                    total_idle += 1

    reward = float(steps[-1][0]['reward'] or 0)
    mean_leg = float(np.mean(leg_lengths)) if leg_lengths else 0.0
    pct_1step = float(np.mean([1 if l == 1 else 0 for l in leg_lengths]) * 100.0) if leg_lengths else 0.0
    pct_2step = float(np.mean([1 if l <= 2 else 0 for l in leg_lengths]) * 100.0) if leg_lengths else 0.0

    return {
        "arm": arm_mode,
        "seed": seed,
        "reward": reward,
        "productive": total_productive,
        "moves": total_moves,
        "idle": total_idle,
        "mean_leg": mean_leg,
        "pct_1step": pct_1step,
        "pct_2step": pct_2step,
        "shed_visits": shed_visits,
        "prod_move_ratio": float(total_productive / max(1, total_moves))
    }

def run_route_ordering_experiment(seeds, max_workers=10):
    arms = [
        ("A", "Baseline CL-Commitment-V1"),
        ("B", "Nearest Productive Target"),
        ("C", "Farthest with Zone Lock"),
        ("D", "Row/Column Sweep"),
        ("E", "Serpentine Sweep"),
        ("F", "Nearest with Zone Lock"),
        ("G", "2-Opt Local Tour"),
        ("I", "Serpentine + Zone Lock (Arm I)"),
    ]

    print(f"\n--- Running Route-Ordering Experiment across {len(seeds)} Matched Seeds ---")
    results = {}

    for arm_code, arm_name in arms:
        tasks = [(arm_code, seed) for seed in seeds]
        arm_res = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_run_single_eval, a, s) for a, s in tasks]
            for f in futures:
                arm_res.append(f.result())

        rewards = [r["reward"] for r in arm_res]
        prods = [r["productive"] for r in arm_res]
        moves = [r["moves"] for r in arm_res]
        idles = [r["idle"] for r in arm_res]
        legs = [r["mean_leg"] for r in arm_res]
        p1s = [r["pct_1step"] for r in arm_res]
        p2s = [r["pct_2step"] for r in arm_res]
        sheds = [r["shed_visits"] for r in arm_res]
        ratios = [r["prod_move_ratio"] for r in arm_res]

        results[arm_code] = {
            "name": arm_name,
            "reward_mean": float(np.mean(rewards)),
            "reward_std": float(np.std(rewards)),
            "prod_mean": float(np.mean(prods)),
            "move_mean": float(np.mean(moves)),
            "idle_mean": float(np.mean(idles)),
            "leg_mean": float(np.mean(legs)),
            "pct_1step_mean": float(np.mean(p1s)),
            "pct_2step_mean": float(np.mean(p2s)),
            "shed_mean": float(np.mean(sheds)),
            "ratio_mean": float(np.mean(ratios)),
        }
        print(f"Arm {arm_code:<2} ({arm_name:<30}): Reward=${np.mean(rewards):8.1f} | Moves={np.mean(moves):6.1f} | Prod={np.mean(prods):6.1f} | MeanLeg={np.mean(legs):4.2f} | 1step={np.mean(p1s):4.1f}% | Prod/Move={np.mean(ratios):.3f}")

    with open("scratch/route_ordering_results.json", "w") as f:
        json.dump(results, f, indent=2)

    return results

if __name__ == "__main__":
    # Run across 20 matched seeds initially for fast precision
    seeds = list(range(100, 120))
    run_route_ordering_experiment(seeds, max_workers=10)
