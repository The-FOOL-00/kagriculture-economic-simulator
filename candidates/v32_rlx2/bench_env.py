# SPDX-License-Identifier: MIT
"""Kagriculture V32 RLX2-F0 Environment Throughput Benchmark.

Measures environment stepping speed (SPS), macro-decision SPS,
multiprocessing scaling, and system bottlenecks.
"""

import os
import sys
import time
import json
from concurrent.futures import ProcessPoolExecutor

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
sys.path.insert(0, os.path.join(REPO_ROOT, "candidates", "v32_rlx2"))

from candidates.v32_rlx2.rlx2_config import RLX2Config, V32_TRAIN
from candidates.v32_rlx2.env import RLX2Env


def _worker_run_episode(args):
    seed, opp_id, seat, macro_interval = args
    cfg = RLX2Config(macro_interval=macro_interval)
    env = RLX2Env(config=cfg)
    t0 = time.time()
    obs, mask = env.reset(seed=seed, opponent_id=opp_id, seat=seat)
    done = False
    macro_steps = 0
    while not done:
        # Action 0: FOLLOW_A7
        obs, r, done, info = env.step(0)
        macro_steps += 1
    dur = time.time() - t0
    sim_steps = 719
    return {
        "seed": seed,
        "opp_id": opp_id,
        "seat": seat,
        "duration": dur,
        "sim_steps": sim_steps,
        "macro_steps": macro_steps,
        "sim_sps": sim_steps / dur,
        "macro_sps": macro_steps / dur,
        "final_cash": info["final_cash"],
    }


def run_benchmark(num_episodes=12, workers_list=(1, 2, 4, 8, 12), macro_interval=4):
    seeds = [V32_TRAIN[0] + i for i in range(num_episodes)]
    opponents = ["E2_A7", "E8_DMITRII", "E0_V3"]
    
    tasks = []
    for i, s in enumerate(seeds):
        opp = opponents[i % len(opponents)]
        seat = i % 2
        tasks.append((s, opp, seat, macro_interval))
        
    results = {}
    print(f"=== RLX2-F0 Environment Throughput Benchmark ({num_episodes} episodes, H={macro_interval}) ===")
    
    for w in workers_list:
        t0 = time.time()
        if w == 1:
            worker_results = [_worker_run_episode(t) for t in tasks]
        else:
            with ProcessPoolExecutor(max_workers=w) as ex:
                worker_results = list(ex.map(_worker_run_episode, tasks))
        wall_time = time.time() - t0
        tot_sim_steps = sum(r["sim_steps"] for r in worker_results)
        tot_macro_steps = sum(r["macro_steps"] for r in worker_results)
        
        agg_sim_sps = tot_sim_steps / wall_time
        agg_macro_sps = tot_macro_steps / wall_time
        
        results[f"workers_{w}"] = {
            "workers": w,
            "wall_time": wall_time,
            "tot_sim_steps": tot_sim_steps,
            "tot_macro_steps": tot_macro_steps,
            "sim_sps": agg_sim_sps,
            "macro_sps": agg_macro_sps,
            "episodes_per_sec": num_episodes / wall_time,
        }
        print(f"Workers: {w:2d} | Wall Time: {wall_time:6.2f}s | Sim SPS: {agg_sim_sps:7.1f} | Macro SPS: {agg_macro_sps:6.1f} | Ep/s: {num_episodes / wall_time:5.2f}")
        
    out_path = os.path.join(REPO_ROOT, "candidates", "v32_rlx2", "reports", "rlx2_f0_benchmark.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved benchmark results to {out_path}")
    return results


if __name__ == "__main__":
    run_benchmark(num_episodes=12, workers_list=(1, 2, 4, 8, 12), macro_interval=4)
