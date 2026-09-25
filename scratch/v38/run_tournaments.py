# SPDX-License-Identifier: MIT
"""Background tournament runner for Phase 12, 19, 21, and 22."""

from __future__ import annotations
import json
import multiprocessing as mp
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v38_heuristic_ppo.config import (
    SCRATCH_DIR, SAFE_DEV_SEEDS, SAFE_FRESH_SEEDS, assert_seed_safe
)
from candidates.v38_heuristic_ppo.evaluate import evaluate_single_match
from candidates.v32_rlx2.opponents import LEAGUE_OPPONENTS


def _eval_match_worker(args: Tuple[str, str, int, int, Optional[str], Optional[str]]) -> Dict[str, Any]:
    pol, opp, seed, seat, bc_p, ppo_p = args
    return evaluate_single_match(
        policy_name=pol, opponent_id=opp, seed=seed, seat=seat,
        bc_path=bc_p, ppo_path=ppo_p
    )


def run_parallel_tournament(
    policies: List[str],
    seeds: List[int],
    opponents: List[str],
    bc_path: Optional[str] = None,
    ppo_path: Optional[str] = None,
    num_workers: int = 4,
    output_json: Optional[str] = None
) -> Dict[str, Any]:
    for s in seeds:
        assert_seed_safe(s)
        
    tasks = []
    for pol in policies:
        for opp in opponents:
            for s in seeds:
                for seat in (0, 1):
                    tasks.append((pol, opp, s, seat, bc_path, ppo_path))
                    
    print(f"Running tournament: {len(tasks)} matches across {num_workers} workers...")
    t0 = time.time()
    
    if num_workers > 1:
        with mp.Pool(processes=num_workers) as pool:
            raw_results = pool.map(_eval_match_worker, tasks)
    else:
        raw_results = [_eval_match_worker(t) for t in tasks]
        
    elapsed = time.time() - t0
    print(f"Tournament completed in {elapsed:.1f}s.")
    
    # Analyze results anchored to V35
    v35_map = {(r["opponent"], r["seed"], r["seat"]): r for r in raw_results if r["policy"] == "V35"}
    
    summaries = {}
    for pol in policies:
        pol_recs = [r for r in raw_results if r["policy"] == pol]
        n = len(pol_recs)
        pts = sum(r["win"] for r in pol_recs)
        wr = pts / max(1, n) * 100.0
        mean_cash = float(np.mean([r["cand_cash"] for r in pol_recs]))
        mean_interv = float(np.mean([r["interventions"] for r in pol_recs]))
        mean_lat = float(np.mean([r["mean_latency_ms"] for r in pol_recs]))
        
        paired_deltas = []
        rescues = 0
        casualties = 0
        for r in pol_recs:
            k = (r["opponent"], r["seed"], r["seat"])
            if k in v35_map:
                v35_r = v35_map[k]
                d = r["cand_cash"] - v35_r["cand_cash"]
                paired_deltas.append(d)
                if v35_r["win"] < 1.0 and r["win"] == 1.0:
                    rescues += 1
                elif v35_r["win"] == 1.0 and r["win"] < 1.0:
                    casualties += 1
                    
        summaries[pol] = {
            "matches": n,
            "points": pts,
            "win_rate": wr,
            "mean_cash": mean_cash,
            "mean_paired_delta": float(np.mean(paired_deltas)) if paired_deltas else 0.0,
            "worst_paired_delta": float(np.min(paired_deltas)) if paired_deltas else 0.0,
            "rescues": rescues,
            "casualties": casualties,
            "mean_interventions": mean_interv,
            "mean_latency_ms": mean_lat
        }
        
    out = {
        "policies": policies,
        "seeds": seeds,
        "opponents": opponents,
        "elapsed_seconds": elapsed,
        "policy_summaries": summaries,
        "raw_results": raw_results
    }
    
    if output_json:
        os.makedirs(os.path.dirname(output_json), exist_ok=True)
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2)
            
    return out


def main():
    # 1. Dev Benchmark
    dev_out = os.path.join(SCRATCH_DIR, "tournament_dev_results.json")
    print("=== RUNNING DEV BENCHMARK TOURNAMENT ===")
    res_dev = run_parallel_tournament(
        policies=["V35", "V38_HEURISTIC", "V38_BC", "V38_PPO"],
        seeds=SAFE_DEV_SEEDS[:5],
        opponents=["E2_A7", "E8_DMITRII", "SYN_AGG"],
        bc_path=os.path.join(SCRATCH_DIR, "bc_policy.pt"),
        ppo_path=os.path.join(SCRATCH_DIR, "ppo_policy.pt"),
        num_workers=4,
        output_json=dev_out
    )
    
    # 2. Fresh Benchmark
    fresh_out = os.path.join(SCRATCH_DIR, "tournament_fresh_results.json")
    print("=== RUNNING FRESH HELD-OUT TOURNAMENT ===")
    res_fresh = run_parallel_tournament(
        policies=["V35", "V38_HEURISTIC", "V38_BC", "V38_PPO"],
        seeds=SAFE_FRESH_SEEDS[:5],
        opponents=["E2_A7", "E8_DMITRII", "SYN_AGG"],
        bc_path=os.path.join(SCRATCH_DIR, "bc_policy.pt"),
        ppo_path=os.path.join(SCRATCH_DIR, "ppo_policy.pt"),
        num_workers=4,
        output_json=fresh_out
    )
    
    # 3. Ablation Tournament (Control without safety fallback)
    abl_out = os.path.join(SCRATCH_DIR, "tournament_ablation_results.json")
    print("=== RUNNING ABLATION TOURNAMENT ===")
    res_abl = run_parallel_tournament(
        policies=["V38_PPO", "V38_PPO_NO_SAFETY"],
        seeds=SAFE_DEV_SEEDS[:3],
        opponents=["E2_A7", "E8_DMITRII"],
        bc_path=os.path.join(SCRATCH_DIR, "bc_policy.pt"),
        ppo_path=os.path.join(SCRATCH_DIR, "ppo_policy.pt"),
        num_workers=4,
        output_json=abl_out
    )
    
    done_file = os.path.join(SCRATCH_DIR, "tournaments.done")
    with open(done_file, "w") as f:
        f.write("TOURNAMENTS_DONE\n")
    print(f"All tournaments complete! Marker written to {done_file}.")

if __name__ == "__main__":
    main()
