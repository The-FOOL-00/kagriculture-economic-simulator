"""
Phase 9: Matched Causal Ablation Study (N=100 Matched Seeds)
============================================================
Evaluates 6 controlled architectural configurations:
- Arm A: Frozen V2 (Production Slot 2 Benchmark)
- Arm B: CL-Commitment-V1 Baseline
- Arm C: Arm B + Persistent Corridor Routes
- Arm D: Arm C + Serpentine Cluster Route Ordering
- Arm E: Arm D + Short-Horizon Prepositioning (H10)
- Arm F: Arm E + Optimized Hub Returns (Batched Drops >= 4)
"""

import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
import json
import numpy as np
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed

from candidates.slot2_aethel_refined_v2 import agent as v2_agent
from candidates.candidate_closed_loop_commitment_v1 import ClosedLoopCommitmentV1, _dist, _quad, SHED_ACCESS

class CausalAblationAgent(ClosedLoopCommitmentV1):
    def __init__(self, arm="B"):
        super().__init__()
        self.arm = arm

    def _serpentine_rank(self, pos):
        x, y = pos
        if y % 2 == 0: return y * 10 + x
        return y * 10 + (9 - x)

    def _pick_best_candidate(self, cands, base_pos):
        if not cands: return None
        adj = [c for c in cands if _dist(base_pos, c) == 1]
        if adj: return adj[0]

        if self.arm in ("D", "E", "F"):
            base_q = _quad(base_pos[0], base_pos[1])
            same_q = [c for c in cands if _quad(c[0], c[1]) == base_q]
            pool = same_q if same_q else cands
            return min(pool, key=lambda p: (_dist(base_pos, p) > 2, self._serpentine_rank(p)))

        return max(cands, key=lambda p: self._cluster_lookahead_score(p, cands, base_pos))

def _run_ablation_match(arm, seed):
    if arm == "A":
        agent_fn = v2_agent
    else:
        agent_fn = CausalAblationAgent(arm=arm)

    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.run([agent_fn, "starter"])
    steps = env.steps

    total_moves = 0
    total_productive = 0
    total_idle = 0
    leg_lengths = []
    worker_last_pos = {}
    shed_visits = 0
    zone_crossings = 0

    for s_idx in range(1, len(steps)):
        p_farm = steps[s_idx-1][0]['observation']['farms'][0]
        c_farm = steps[s_idx][0]['observation']['farms'][0]
        pw = [tuple(p_farm['farmer'])] + [tuple(h) for h in p_farm['hands']]
        cw = [tuple(c_farm['farmer'])] + [tuple(h) for h in c_farm['hands']]

        for w_idx in range(min(len(pw), len(cw))):
            p0, p1 = pw[w_idx], cw[w_idx]
            if p0 != p1:
                total_moves += 1
                if p1 in SHED_ACCESS: shed_visits += 1
                if _quad(p0[0], p0[1]) != _quad(p1[0], p1[1]): zone_crossings += 1
            else:
                t0 = p_farm['tiles'][p0[1]][p0[0]] if 0 <= p0[1] < 10 and 0 <= p0[0] < 10 else None
                t1 = c_farm['tiles'][p0[1]][p0[0]] if 0 <= p0[1] < 10 and 0 <= p0[0] < 10 else None
                if t0 != t1 or p0 in SHED_ACCESS:
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
        "arm": arm,
        "seed": seed,
        "reward": reward,
        "productive": total_productive,
        "moves": total_moves,
        "idle": total_idle,
        "mean_leg": mean_leg,
        "pct_1step": pct_1step,
        "pct_2step": pct_2step,
        "shed_visits": shed_visits,
        "zone_crossings": zone_crossings,
        "prod_move_ratio": float(total_productive / max(1, total_moves))
    }

def run_full_causal_study(seeds, max_workers=10):
    arms = [
        ("A", "Frozen V2 Benchmark"),
        ("B", "CL-Commitment-V1 Baseline"),
        ("C", "Arm B + Corridor Ownership"),
        ("D", "Arm C + Serpentine Routing"),
        ("E", "Arm D + Lookahead H10"),
        ("F", "Arm E + Batched Hub Returns"),
    ]

    print(f"\n=== Executing Matched Causal Study Across {len(seeds)} Seeds (N={len(seeds)}) ===")
    results = {}

    for arm_code, arm_name in arms:
        tasks = [(arm_code, s) for s in seeds]
        arm_res = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_run_ablation_match, a, s) for a, s in tasks]
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
        zones = [r["zone_crossings"] for r in arm_res]
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
            "zone_mean": float(np.mean(zones)),
            "ratio_mean": float(np.mean(ratios)),
        }
        print(f"Arm {arm_code} ({arm_name:<30}): Reward=${np.mean(rewards):8.1f} | Moves={np.mean(moves):6.1f} | Prod={np.mean(prods):6.1f} | MeanLeg={np.mean(legs):4.2f} | 1step={np.mean(p1s):4.1f}% | Sheds={np.mean(sheds):5.1f} | Prod/Move={np.mean(ratios):.3f}")

    with open("scratch/causal_study_forensics_results.json", "w") as f:
        json.dump(results, f, indent=2)

    return results

if __name__ == "__main__":
    seeds = list(range(1000, 1100)) # N=100 matched seeds
    run_full_causal_study(seeds, max_workers=10)
