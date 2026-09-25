# SPDX-License-Identifier: MIT
"""Kagriculture V32 RL-X2 Master Benchmark & Evaluation Harness.

Executes paired mirrored tournament matches across the frozen opponent league
and computes full distributional statistics and paired deltas vs A7.
"""

from __future__ import annotations
import copy
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np

try:
    from rlx2_config import REPO_ROOT, RLX2Config, V32_DEV_HIST, V32_DEV_FRESH
    from env import _get_shared_obs
    from executor import StrategicExecutor
    from opponents import LEAGUE_OPPONENTS, load_league_opponent
    from state import EconomicFeatures, extract_economic_features, vectorize_features
except ImportError:
    from candidates.v32_rlx2.rlx2_config import REPO_ROOT, RLX2Config, V32_DEV_HIST, V32_DEV_FRESH
    from candidates.v32_rlx2.env import _get_shared_obs
    from candidates.v32_rlx2.executor import StrategicExecutor
    from candidates.v32_rlx2.opponents import LEAGUE_OPPONENTS, load_league_opponent
    from candidates.v32_rlx2.state import EconomicFeatures, extract_economic_features, vectorize_features

from kaggle_environments import make


def evaluate_single_match(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Runs a single mirrored match leg."""
    from scripts.v32_common import check_seed_allowed, load_agent
    
    seed = spec["seed"]
    check_seed_allowed(seed)
    
    opp_id = spec["opponent_id"]
    seat = spec["seat"]
    policy_fn = spec.get("policy_fn")  # Callable(features, mask) -> macro_action
    actor_path = spec.get("actor_path")
    state_tier = spec.get("state_tier", "S2")
    
    actor = None
    if actor_path and os.path.exists(actor_path):
        import torch
        from candidates.v32_rlx2.policy import StrategicActor
        from candidates.v32_rlx2.state import get_feature_dim
        actor = StrategicActor(state_dim=get_feature_dim(state_tier), action_dim=10)
        actor.load_state_dict(torch.load(actor_path, map_location="cpu", weights_only=True))
        actor.eval()
    
    env = make("kaggriculture", configuration={"seed": seed})
    env.reset()
    
    a7_agent = load_agent("E9_AST")
    opp_agent = load_league_opponent(opp_id)
    executor = StrategicExecutor()
    
    macro_interval = spec.get("macro_interval", 4)
    current_features = None
    step_actions = []
    
    sub_count = 0
    current_macro = 0
    
    while not env.done:
        p_obs = _get_shared_obs(env, seat)
        opp_obs = _get_shared_obs(env, 1 - seat)
        cur_step = int(p_obs.get("step", 0) or 0)
        
        base_a7 = a7_agent.act(p_obs)
        opp_act = opp_agent(opp_obs)
        
        current_features = extract_economic_features(p_obs, player=seat)
        
        # Decide macro action at interval boundaries
        if cur_step % macro_interval == 0:
            from candidates.v32_rlx2.action_space import get_action_mask
            mask = get_action_mask(current_features)
            if actor is not None:
                vec = vectorize_features(current_features, tier=state_tier)
                current_macro, _, _ = actor.get_action(vec, mask, deterministic=True)
            elif callable(policy_fn):
                current_macro = policy_fn(current_features, mask)
            else:
                current_macro = 0
        step_actions.append(current_macro)
        
        # Translate via executor
        p_act = executor.execute(
            macro_action=current_macro,
            observation=p_obs,
            features=current_features,
            base_a7_action=base_a7
        )
        
        if seat == 0:
            env.step([p_act, opp_act])
        else:
            env.step([opp_act, p_act])
            
    final_p_cash = float(env.steps[-1][seat]["reward"] or 0.0)
    final_opp_cash = float(env.steps[-1][1 - seat]["reward"] or 0.0)
    
    # Baseline A7 score for this exact match
    a7_cash = spec.get("a7_cash", None)
    if a7_cash is None:
        # Run pure A7 reference
        a7_env = make("kaggriculture", configuration={"seed": seed})
        a7_env.reset()
        a7_ref = load_agent("E9_AST")
        opp_ref = load_league_opponent(opp_id)
        while not a7_env.done:
            o0 = _get_shared_obs(a7_env, seat)
            o1 = _get_shared_obs(a7_env, 1 - seat)
            act0 = a7_ref.act(o0)
            act1 = opp_ref(o1)
            if seat == 0:
                a7_env.step([act0, act1])
            else:
                a7_env.step([act1, act0])
        a7_cash = float(a7_env.steps[-1][seat]["reward"] or 0.0)
        
    delta = final_p_cash - a7_cash
    win = final_p_cash > final_opp_cash
    tie = final_p_cash == final_opp_cash
    loss = final_p_cash < final_opp_cash
    
    return {
        "seed": seed,
        "opponent_id": opp_id,
        "seat": seat,
        "cash": final_p_cash,
        "opp_cash": final_opp_cash,
        "a7_cash": a7_cash,
        "delta": delta,
        "win": win,
        "loss": loss,
        "tie": tie,
        "action_distribution": {a: step_actions.count(a) for a in set(step_actions)}
    }


def run_full_benchmark(
    policy_fn: Optional[Callable[[EconomicFeatures, np.ndarray], int]] = None,
    actor_path: Optional[str] = None,
    state_tier: str = "S2",
    policy_name: str = "Candidate",
    seeds: Optional[List[int]] = None,
    opponents: Optional[List[str]] = None,
    max_workers: int = 8
) -> Dict[str, Any]:
    """Runs master benchmark evaluation across seeds and opponents."""
    seeds = seeds or (list(range(V32_DEV_HIST[0], V32_DEV_HIST[1] + 1)) + list(range(V32_DEV_FRESH[0], V32_DEV_FRESH[1] + 1)))
    opponents = opponents or list(LEAGUE_OPPONENTS)
    
    specs = []
    for s in seeds:
        for opp in opponents:
            for seat in (0, 1):
                specs.append({
                    "seed": s,
                    "opponent_id": opp,
                    "seat": seat,
                    "policy_fn": policy_fn,
                    "actor_path": actor_path,
                    "state_tier": state_tier,
                    "macro_interval": 4
                })
                
    print(f"=== Running Master Benchmark for {policy_name} ({len(specs)} legs across {max_workers} workers) ===")
    t0 = time.time()
    if max_workers > 1:
        with ProcessPoolExecutor(max_workers=max_workers) as pool:
            results = list(pool.map(evaluate_single_match, specs))
    else:
        results = [evaluate_single_match(s) for s in specs]
    elapsed = time.time() - t0
    print(f"Finished {len(specs)} legs in {elapsed:.1f}s ({elapsed/max(1, len(specs)):.2f}s/leg).", flush=True)
    
    # Aggregate by opponent
    by_opp: Dict[str, List[Dict[str, Any]]] = {}
    for r in results:
        by_opp.setdefault(r["opponent_id"], []).append(r)
        
    summary_table = []
    overall_cash = [r["cash"] for r in results]
    overall_deltas = [r["delta"] for r in results]
    overall_wins = sum(1 for r in results if r["win"])
    overall_losses = sum(1 for r in results if r["loss"])
    overall_ties = sum(1 for r in results if r["tie"])
    
    for opp, opp_res in by_opp.items():
        cashes = [r["cash"] for r in opp_res]
        deltas = [r["delta"] for r in opp_res]
        wins = sum(1 for r in opp_res if r["win"])
        losses = sum(1 for r in opp_res if r["loss"])
        ties = sum(1 for r in opp_res if r["tie"])
        
        row = {
            "Policy": policy_name,
            "Opponent": opp,
            "Seeds": len(cashes),
            "Mean": float(np.mean(cashes)),
            "Median": float(np.median(cashes)),
            "P25": float(np.percentile(cashes, 25)),
            "P75": float(np.percentile(cashes, 75)),
            "Min": float(np.min(cashes)),
            "W": wins,
            "L": losses,
            "T": ties,
            "Paired_Delta": float(np.mean(deltas)),
        }
        summary_table.append(row)
        
    overall_row = {
        "Policy": policy_name,
        "Opponent": "OVERALL",
        "Seeds": len(overall_cash),
        "Mean": float(np.mean(overall_cash)),
        "Median": float(np.median(overall_cash)),
        "P25": float(np.percentile(overall_cash, 25)),
        "P75": float(np.percentile(overall_cash, 75)),
        "Min": float(np.min(overall_cash)),
        "W": overall_wins,
        "L": overall_losses,
        "T": overall_ties,
        "Paired_Delta": float(np.mean(overall_deltas)),
    }
    summary_table.append(overall_row)
    
    return {
        "policy_name": policy_name,
        "legs": len(results),
        "summary": summary_table,
        "raw_results": results
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="RL-X2 Master Benchmark")
    parser.add_argument("--actor", type=str, default=None, help="Path to actor checkpoint (.pt)")
    parser.add_argument("--name", type=str, default="RLX2-F7", help="Policy display name")
    parser.add_argument("--tier", type=str, default="S2", help="State tier")
    parser.add_argument("--workers", type=int, default=8, help="Number of parallel workers")
    parser.add_argument("--num_seeds", type=int, default=4, help="Number of dev seeds per cohort")
    args = parser.parse_args()
    
    dev_seeds = list(range(V32_DEV_HIST[0], V32_DEV_HIST[0] + args.num_seeds))
    res = run_full_benchmark(
        actor_path=args.actor,
        state_tier=args.tier,
        policy_name=args.name,
        seeds=dev_seeds,
        max_workers=args.workers
    )
    print("\n" + "=" * 80)
    print(f"MASTER TOURNAMENT BENCHMARK SUMMARY: {args.name}")
    print("=" * 80)
    for r in res["summary"]:
        print(f"{r['Policy']:<12} | {r['Opponent']:<10} | N={r['Seeds']:2d} | Mean: ${r['Mean']:>9.1f} | Med: ${r['Median']:>9.1f} | W/L/T: {r['W']:2d}/{r['L']:2d}/{r['T']:2d} | Paired Delta vs A7: ${r['Paired_Delta']:>+9.1f}")
    print("=" * 80)
