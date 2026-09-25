# SPDX-License-Identifier: MIT
"""Kagriculture V38 Expert Dataset Generator and Loader for Behavioral Cloning."""

from __future__ import annotations
import json
import multiprocessing as mp
import os
import sys
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

try:
    from config import (
        SCRATCH_DIR, SAFE_TRAIN_SEEDS, SAFE_DEV_SEEDS, assert_seed_safe, DEFAULT_MACRO_HORIZON
    )
    from counterfactual import CounterfactualEngine
except ImportError:
    from candidates.v38_heuristic_ppo.config import (
        SCRATCH_DIR, SAFE_TRAIN_SEEDS, SAFE_DEV_SEEDS, assert_seed_safe, DEFAULT_MACRO_HORIZON
    )
    from candidates.v38_heuristic_ppo.counterfactual import CounterfactualEngine


DATASET_FILE = os.path.join(SCRATCH_DIR, "expert_counterfactual_dataset.json")


def _eval_state_task(args: Tuple[int, str, int, int, int, float]) -> Optional[Dict[str, Any]]:
    """Worker function for multiprocessing pool."""
    seed, opp, seat, step, horizon, min_advantage_threshold = args
    try:
        assert_seed_safe(seed)
        engine = CounterfactualEngine(default_horizon=horizon)
        res = engine.evaluate_all_options_at_state(
            seed=seed, opponent_id=opp, seat=seat,
            branch_step=step, horizon=horizon
        )
        target_opt = res["best_option"] if res["best_delta"] >= min_advantage_threshold else 0
        return {
            "seed": seed,
            "opponent": opp,
            "seat": seat,
            "step": step,
            "horizon": horizon,
            "state_vector": res["state_vector"],
            "action_mask": res["action_mask"],
            "heuristic_cash": res["heuristic_cash"],
            "best_option": target_opt,
            "raw_best_option": res["best_option"],
            "best_delta": res["best_delta"],
            "advantages": {str(k): v for k, v in res["advantages"].items()}
        }
    except Exception as e:
        print(f"Error evaluating seed {seed}, opp {opp}, step {step}, seat {seat}: {e}")
        return None


def generate_expert_dataset(
    seeds: Optional[List[int]] = None,
    opponents: Optional[List[str]] = None,
    steps: Optional[List[int]] = None,
    horizon: int = DEFAULT_MACRO_HORIZON,
    output_path: str = DATASET_FILE,
    min_advantage_threshold: float = 50.0,
    num_workers: int = 4
) -> Dict[str, Any]:
    """Generates counterfactual expert dataset using multiprocessing."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    seeds = seeds or SAFE_TRAIN_SEEDS[:4]
    opponents = opponents or ["E2_A7", "E8_DMITRII"]
    steps = steps or [48, 72, 144, 216, 288, 360, 480, 576]
    
    tasks = []
    for seed in seeds:
        assert_seed_safe(seed)
        for opp in opponents:
            for step in steps:
                for seat in (0, 1):
                    tasks.append((seed, opp, seat, step, horizon, min_advantage_threshold))
                    
    print(f"Generating expert dataset: {len(tasks)} states across {num_workers} workers...")
    
    if num_workers > 1:
        with mp.Pool(processes=num_workers) as pool:
            results = pool.map(_eval_state_task, tasks)
    else:
        results = [_eval_state_task(t) for t in tasks]
        
    records = [r for r in results if r is not None]
    
    dataset = {
        "metadata": {
            "num_records": len(records),
            "seeds": seeds,
            "opponents": opponents,
            "steps": steps,
            "horizon": horizon,
            "min_advantage_threshold": min_advantage_threshold
        },
        "records": records
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)
        
    print(f"Dataset generated successfully with {len(records)} records saved to {output_path}")
    return dataset


def load_dataset(dataset_path: str = DATASET_FILE) -> Dict[str, Any]:
    with open(dataset_path, "r", encoding="utf-8") as f:
        return json.load(f)
