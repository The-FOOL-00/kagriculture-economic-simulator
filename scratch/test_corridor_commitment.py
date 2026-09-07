"""
Corridor Ownership & Target Reservation Forensics (Phases 8 & 10)
================================================================
Tests whether assigning dedicated row/corridor ownership to workers
eliminates target interleaving and reduces chore transition edge weights.
"""

import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
import json
import numpy as np
from collections import defaultdict

from candidates.slot2_aethel_refined_v2 import agent as v2_agent
from candidates.candidate_closed_loop_commitment_v1 import ClosedLoopCommitmentV1, _dist, _quad, _bfs_step, SHED_ACCESS, BOARD, PRODUCE_TO_DROP

class CorridorZonedAgent(ClosedLoopCommitmentV1):
    def __init__(self, mode="corridor"):
        super().__init__()
        self.mode = mode

    def _worker_preferred_corridor(self, worker_idx, day):
        # Worker 0: Farmer -> Livestock / Hub manager
        # Worker 1: NW Top Rows (y=0, 1)
        # Worker 2: NW Mid Rows (y=2, 3)
        # Worker 3: NW Bot Row / Pastures (y=4, 5)
        # Worker 4: NE Top Rows (y=0, 1, x>=5)
        # Worker 5: NE Mid Rows (y=2, 3, x>=5)
        # Worker 6+: Dynamic harvest/water assist
        if worker_idx == 0:
            return "HUB"
        elif worker_idx == 1:
            return "NW_ROW01"
        elif worker_idx == 2:
            return "NW_ROW23"
        elif worker_idx == 3:
            return "PASTURE"
        elif worker_idx == 4:
            return "NE_ROW01"
        elif worker_idx == 5:
            return "NE_ROW23"
        return "FLEX"

    def _filter_corridor_cands(self, cands, worker_idx, base_pos, day):
        if not cands: return None
        corr = self._worker_preferred_corridor(worker_idx, day)

        if corr == "NW_ROW01":
            match = [p for p in cands if p[1] in (0, 1) and p[0] < 5]
            if match: return min(match, key=lambda p: _dist(base_pos, p))
        elif corr == "NW_ROW23":
            match = [p for p in cands if p[1] in (2, 3) and p[0] < 5]
            if match: return min(match, key=lambda p: _dist(base_pos, p))
        elif corr == "NE_ROW01":
            match = [p for p in cands if p[1] in (0, 1) and p[0] >= 5]
            if match: return min(match, key=lambda p: _dist(base_pos, p))
        elif corr == "NE_ROW23":
            match = [p for p in cands if p[1] in (2, 3) and p[0] >= 5]
            if match: return min(match, key=lambda p: _dist(base_pos, p))

        # Fallback to local cluster lookahead
        return self._pick_best_candidate(cands, base_pos)

def evaluate_corridor_agent(seed=42):
    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    agent = CorridorZonedAgent()
    env.run([agent, "starter"])
    steps = env.steps
    r = float(steps[-1][0]['reward'] or 0)

    total_moves = 0
    total_productive = 0
    leg_lengths = []
    prev_w_pos = {}

    for s_idx in range(1, len(steps)):
        p_farm = steps[s_idx-1][0]['observation']['farms'][0]
        c_farm = steps[s_idx][0]['observation']['farms'][0]
        pw = [tuple(p_farm['farmer'])] + [tuple(h) for h in p_farm['hands']]
        cw = [tuple(c_farm['farmer'])] + [tuple(h) for h in c_farm['hands']]

        for w_idx in range(min(len(pw), len(cw))):
            p0, p1 = pw[w_idx], cw[w_idx]
            if p0 != p1:
                total_moves += 1
            else:
                t0 = p_farm['tiles'][p0[1]][p0[0]] if 0 <= p0[1] < 10 and 0 <= p0[0] < 10 else None
                t1 = c_farm['tiles'][p0[1]][p0[0]] if 0 <= p0[1] < 10 and 0 <= p0[0] < 10 else None
                if t0 != t1 or p0 in SHED_ACCESS:
                    total_productive += 1
                    if w_idx in prev_w_pos:
                        leg_lengths.append(_dist(prev_w_pos[w_idx], p0))
                    prev_w_pos[w_idx] = p0

    return {
        "reward": r,
        "productive": total_productive,
        "moves": total_moves,
        "mean_leg": float(np.mean(leg_lengths)) if leg_lengths else 0.0,
        "pct_1step": float(np.mean([1 if l == 1 else 0 for l in leg_lengths]) * 100.0) if leg_lengths else 0.0,
        "prod_move_ratio": float(total_productive / max(1, total_moves))
    }

if __name__ == "__main__":
    print("Evaluating Corridor Zoned Agent across 10 seeds...")
    results = [evaluate_corridor_agent(s) for s in range(100, 110)]
    r_mean = np.mean([r["reward"] for r in results])
    m_mean = np.mean([r["moves"] for r in results])
    p_mean = np.mean([r["productive"] for r in results])
    leg_mean = np.mean([r["mean_leg"] for r in results])
    ratio_mean = np.mean([r["prod_move_ratio"] for r in results])

    print(f"Corridor Agent (10 seeds): Reward=${r_mean:.1f} | Moves={m_mean:.1f} | Prod={p_mean:.1f} | MeanLeg={leg_mean:.2f} | Ratio={ratio_mean:.3f}")
