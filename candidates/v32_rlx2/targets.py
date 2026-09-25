# SPDX-License-Identifier: MIT
"""Kagriculture V32 RL-X2 Parallel Search Target Generation Pipeline.

Generates and filters high-consequence strategic decision targets from exact search
using multiprocess parallelization across CPU cores.
"""

from __future__ import annotations
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any, Dict, List, Optional
import numpy as np

try:
    from rlx2_config import REPO_ROOT, V32_TRAIN
    from search import StrategicSearchEngine, StrategicTarget
except ImportError:
    from candidates.v32_rlx2.rlx2_config import REPO_ROOT, V32_TRAIN
    from candidates.v32_rlx2.search import StrategicSearchEngine, StrategicTarget


CANDIDATE_SEARCH_STEPS = [
    72,   # Day 3: First shop unlock (Bakery / Dairy / etc.)
    144,  # Day 6: Second shop unlock & animal ramp
    216,  # Day 9: Third shop unlock & pasture stocking
    288,  # Day 12: Mid-game crop compounding
    360,  # Day 15: Mid-game cash / labor expansion
    432,  # Day 18: Second crop cycle harvest
    504,  # Day 21: High-value animal yield ramp
    576,  # Day 24: Pre-terminal market accumulation
    614,  # Day 25.14: Forensics Seed 249677 Melon liquidation point
    648,  # Day 27: Endgame preparation
    696,  # Day 29: Forensics Seed 249677 Milk dump point
]


def _worker_search_task(args: Tuple[int, str, int, int, int]) -> Optional[Dict[str, Any]]:
    seed, opp, seat, step, macro_dur = args
    try:
        engine = StrategicSearchEngine()
        tgt = engine.search_decision_state(
            seed=seed,
            opponent_id=opp,
            seat=seat,
            branch_step=step,
            macro_duration=macro_dur
        )
        return {
            "seed": tgt.seed,
            "opponent_id": tgt.opponent_id,
            "seat": tgt.seat,
            "step": tgt.step,
            "state_vector": tgt.state_vector.tolist(),
            "action_mask": tgt.action_mask.tolist(),
            "a7_cash": tgt.a7_cash,
            "action_values": tgt.action_values,
            "best_action": tgt.best_action,
            "best_cash": tgt.best_cash,
            "best_delta": tgt.best_delta,
            "second_best_action": tgt.second_best_action,
            "second_best_cash": tgt.second_best_cash,
            "gap": tgt.gap
        }
    except Exception as e:
        print(f"  [ERROR] Seed {seed}, Opp {opp}, Seat {seat}, Step {step}: {e}", flush=True)
        return None


def generate_search_targets_parallel(
    seeds: Optional[List[int]] = None,
    opponents: Optional[List[str]] = None,
    steps: Optional[List[int]] = None,
    out_file: Optional[str] = None,
    max_workers: int = 8
) -> List[Dict[str, Any]]:
    """Runs strategic search in parallel across CPU workers."""
    seeds = seeds or list(range(V32_TRAIN[0], V32_TRAIN[0] + 3))  # 3 train seeds
    opponents = opponents or ["E8_DMITRII", "E2_A7"]
    steps = steps or CANDIDATE_SEARCH_STEPS
    
    out_file = out_file or os.path.join(REPO_ROOT, "candidates", "v32_rlx2", "reports", "strategic_targets.jsonl")
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    
    tasks = []
    for s in seeds:
        for opp in opponents:
            for seat in (0, 1):
                for step in steps:
                    tasks.append((s, opp, seat, step, 4))
                    
    print(f"=== Generating {len(tasks)} Strategic Search Targets using {max_workers} Parallel Workers ===", flush=True)
    targets = []
    t0 = time.time()
    
    with open(out_file, "w") as f:
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            future_to_task = {executor.submit(_worker_search_task, t): t for t in tasks}
            for fut in as_completed(future_to_task):
                res = fut.result()
                if res is not None:
                    targets.append(res)
                    f.write(json.dumps(res) + "\n")
                    f.flush()
                    if res["best_delta"] > 0:
                        print(f"  [POSITIVE TARGET +${res['best_delta']:,.2f}] Seed {res['seed']} | Opp {res['opponent_id']} | Step {res['step']:3d} | Best Action: {res['best_action']}", flush=True)
                        
    dur = time.time() - t0
    pos_targets = [t for t in targets if t["best_delta"] > 0]
    print(f"Target generation complete in {dur:.1f}s ({len(targets)/dur:.2f} targets/s). Total: {len(targets)}, Positive Delta Targets: {len(pos_targets)} ({len(pos_targets)/max(1, len(targets))*100:.1f}%). Saved to {out_file}", flush=True)
    return targets


if __name__ == "__main__":
    generate_search_targets_parallel()
