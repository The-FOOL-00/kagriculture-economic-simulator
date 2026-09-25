# SPDX-License-Identifier: MIT
"""HMEH Matchup-Aware Evaluation Suite.

Evaluates an HMEH policy against the full 6-opponent benchmark panel:
1. E0_V3 (Base tape player)
2. E1_V22R1 (Live Slot A champion)
3. E2_A7 / E9_AST (Live Slot B champion, +$1,286 alpha)
4. E8_DMITRII (Frontier terminal search agent)
5. V54 (Declarative backbone reference)
6. SYN_AGG (Synthetic aggressive market dumper)
Across paired development seeds (249675-249684).
"""

from __future__ import annotations
import argparse
import importlib.util
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any, Dict, List, Tuple

import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
HMEH_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in (REPO_ROOT, os.path.join(REPO_ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
if HMEH_ROOT not in sys.path:
    sys.path.append(HMEH_ROOT)

from kaggle_environments import make
from v32_common import assert_frozen, check_seed_allowed, load_agent
from candidates.v32_hmeh.main import make_hmeh_agent

DEV_SEEDS = list(range(249675, 249685))


def _synthetic_aggressive(obs, cfg=None):
    player = obs.get("player", 0)
    farms = obs.get("farms", [])
    farm = farms[player] if farms and player < len(farms) else {}
    private = obs.get("private", {}) or {}
    shed = private.get("shed", {})
    orders = []
    for prod in ["MILK", "WOOL", "MELON", "STRAWBERRY", "WHEAT"]:
        qty = shed.get(prod, 0)
        if qty > 0:
            orders.append(["SELL", prod, min(qty, 30)])
    orders = orders[:10]
    return {"market": orders, "farmer": ["PASS"], "hands": []}


def _load_opponent(opp_id: str):
    if opp_id == "SYN_AGG":
        return _synthetic_aggressive
    elif opp_id == "V54":
        path = os.path.join(REPO_ROOT, "external_repos", "lixingtao123-Kaggriculture", "variant_v54_h3q4", "main.py")
        import uuid
        with open(path, "r", encoding="utf-8") as f:
            code = f.read()
        ns = {"__name__": f"v54_iso_{uuid.uuid4().hex[:8]}"}
        exec(compile(code, path, "exec"), ns)
        return ns.get("agent")
    elif opp_id in ("E2_A7", "A7"):
        return load_agent("E9_AST")
    else:
        return load_agent(opp_id)


def _to_callable(agent):
    if hasattr(agent, "act") and callable(getattr(agent, "act")):
        return lambda o, c=None: agent.act(o, c)
    elif callable(agent):
        return agent
    raise ValueError(f"Agent {agent} is not callable")


def _run_match(args: Tuple[str, str, int, int]) -> Dict[str, Any]:
    stage, opp_id, seed, seat = args
    check_seed_allowed(seed)
    
    agent_fn, _ = make_hmeh_agent(stage=stage)
    opp_fn = _load_opponent(opp_id)
    
    p_callable = _to_callable(agent_fn)
    opp_callable = _to_callable(opp_fn)
    
    agents = [p_callable, opp_callable] if seat == 0 else [opp_callable, p_callable]
    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720}, debug=False)
    
    t0 = time.time()
    env.run(agents)
    dur = time.time() - t0
    
    final_step = env.steps[-1]
    p_reward = float(final_step[seat]["reward"] or 0.0)
    opp_reward = float(final_step[1 - seat]["reward"] or 0.0)
    delta = p_reward - opp_reward
    win = 1.0 if delta > 0 else (0.5 if delta == 0 else 0.0)
    
    return {
        "stage": stage,
        "opp": opp_id,
        "seed": seed,
        "seat": seat,
        "cash": p_reward,
        "opp_cash": opp_reward,
        "delta": delta,
        "win": win,
        "duration": dur
    }


def evaluate_benchmark(
    stage: str = "HMEH-0",
    opponents: List[str] = None,
    seeds: List[int] = None,
    max_workers: int = 4
) -> Dict[str, Any]:
    assert_frozen()
    opponents = opponents or ["E0_V3", "E1_V22R1", "E2_A7", "E8_DMITRII", "V54", "SYN_AGG"]
    seeds = seeds or DEV_SEEDS
    
    tasks = []
    for opp in opponents:
        for s in seeds:
            for seat in (0, 1):
                tasks.append((stage, opp, s, seat))
                
    print(f"\n=================================================================")
    print(f"RUNNING BENCHMARK: Stage={stage} against {len(opponents)} opponents across {len(seeds)} seeds (2 seats = {len(tasks)} legs)")
    print(f"=================================================================")
    
    results_by_opp: Dict[str, List[Dict[str, Any]]] = {o: [] for o in opponents}
    
    if max_workers <= 1:
        for t in tasks:
            res = _run_match(t)
            results_by_opp[res["opp"]].append(res)
            print(f"  [{res['opp']}] Seed {res['seed']} Seat {res['seat']}: Cash=${res['cash']:,.2f} Opp=${res['opp_cash']:,.2f} Delta=${res['delta']:+,.2f} ({res['duration']:.1f}s)")
    else:
        with ProcessPoolExecutor(max_workers=max_workers) as pool:
            futures = {pool.submit(_run_match, t): t for t in tasks}
            for fut in as_completed(futures):
                res = fut.result()
                results_by_opp[res["opp"]].append(res)
                print(f"  [{res['opp']}] Seed {res['seed']} Seat {res['seat']}: Cash=${res['cash']:,.2f} Opp=${res['opp_cash']:,.2f} Delta=${res['delta']:+,.2f} ({res['duration']:.1f}s)")
                
    summary = {}
    print("\n" + "=" * 80)
    print(f"{'Opponent':<15} {'Mean Cash':<12} {'Median Cash':<12} {'P25':<10} {'P75':<10} {'Win%':<8} {'Mean Delta':<12}")
    print("-" * 80)
    
    for opp, records in results_by_opp.items():
        cash = [r["cash"] for r in records]
        deltas = [r["delta"] for r in records]
        wins = [r["win"] for r in records]
        summary[opp] = {
            "mean_cash": float(np.mean(cash)),
            "median_cash": float(np.median(cash)),
            "p25_cash": float(np.percentile(cash, 25)),
            "p75_cash": float(np.percentile(cash, 75)),
            "win_rate": float(np.mean(wins)),
            "mean_delta": float(np.mean(deltas)),
            "legs": len(records)
        }
        print(f"{opp:<15} ${np.mean(cash):>10,.2f} ${np.median(cash):>10,.2f} ${np.percentile(cash, 25):>8,.2f} ${np.percentile(cash, 75):>8,.2f} {np.mean(wins)*100:>6.1f}% ${np.mean(deltas):>+10,.2f}")
        
    print("=" * 80 + "\n")
    return {"summary": summary, "records": results_by_opp}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", default="HMEH-0")
    parser.add_argument("--opponents", nargs="+", default=None)
    parser.add_argument("--seeds", type=int, nargs="+", default=None)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--out", default="candidates/v32_hmeh/reports/benchmark_summary.json")
    args = parser.parse_args()
    
    res = evaluate_benchmark(args.stage, args.opponents, args.seeds, args.workers)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(res, f, indent=2)
    print(f"Benchmark results written to {args.out}")
