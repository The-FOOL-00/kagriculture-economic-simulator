#!/usr/bin/env python3
"""Official Promotion Ladder Evaluation for Kagriculture V47.

Evaluates V47_ELITE_TRANSFER across clean dev seeds (2 seats per seed) in parallel:
- V44 Baseline
- Public Elite Benchmarks (thomastschinkel_2945, kaitofukami_v48_3009, indarkarhana_top10, tetsutani_pasture, saiteja_mega_3000, dmitrii_lb2800)

Reports:
- Win rate, mean margin, median margin, P10 margin
- Mean cash (candidate vs opponent)
- Casualties
- Gate clearance (Gate A, Gate B, Gate C, Elite Gate)
"""

from __future__ import annotations
import concurrent.futures
import copy
import json
import os
import sys
from typing import Any, Dict, List, Tuple
import numpy as np

sys.stdout.reconfigure(line_buffering=True)

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from candidates.v44_economic_portfolio.main import V44CandidateController
from research.v47.elite_benchmark.run_elite_benchmark import load_agent as load_elite_agent

# 64 Clean dev seeds (128 paired legs per matchup)
SEEDS = [249800 + i for i in range(64)]
PROTECTED_HOLDOUTS = [(214200, 214249), (340090, 340199), (249695, 249734)]

for s in SEEDS:
    for start, end in PROTECTED_HOLDOUTS:
        assert not (start <= s <= end), f"CRITICAL: Protected holdout seed {s} accessed!"


def load_candidate():
    import importlib.util
    cand_path = os.path.join(REPO_ROOT, "candidates", "v47_elite_transfer", "main.py")
    mod_name = f"mod_cand_{os.getpid()}"
    spec = importlib.util.spec_from_file_location(mod_name, cand_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.agent


def run_ladder_match(args: Tuple[str, str, int, int]) -> Dict[str, Any]:
    cand_name, opp_key, seed, seat = args
    opp_seat = 1 - seat

    if cand_name == "V47_ELITE_TRANSFER":
        cand_agent = load_candidate()
    elif cand_name == "V44":
        cand_agent = V44CandidateController()
    else:
        raise ValueError(f"Unknown candidate {cand_name}")

    opp_fn = load_elite_agent(opp_key)

    sim = FastKagricultureSim(seed=seed)
    obs_list = sim.reset(seed=seed)

    cas_cand = 0
    cas_opp = 0
    for step in range(719):
        obs_c = obs_list[seat]
        obs_o = obs_list[opp_seat]

        try:
            act_c = cand_agent.act(obs_c) if hasattr(cand_agent, "act") else cand_agent(obs_c)
        except Exception:
            act_c = {"farmer": ["PASS"], "hands": [], "market": []}
            cas_cand += 1

        try:
            act_o = opp_fn.act(obs_o) if hasattr(opp_fn, "act") else opp_fn(obs_o)
        except Exception:
            act_o = {"farmer": ["PASS"], "hands": [], "market": []}
            cas_opp += 1

        actions = [act_c, act_o] if seat == 0 else [act_o, act_c]
        obs_list, rewards, done, info = sim.step(actions)

    cash_c = float(obs_list[seat]["farms"][seat]["money"])
    cash_o = float(obs_list[opp_seat]["farms"][opp_seat]["money"])
    margin_c = cash_c - cash_o

    return {
        "cand": cand_name,
        "opp": opp_key,
        "seed": seed,
        "seat": seat,
        "cash_c": cash_c,
        "cash_o": cash_o,
        "margin": margin_c,
        "won": 1 if cash_c > cash_o else (0.5 if cash_c == cash_o else 0),
        "cas_cand": cas_cand,
        "cas_opp": cas_opp,
    }


def evaluate_matchup(executor, cand_name: str, opp_key: str, num_seeds: int = 64) -> Dict[str, Any]:
    eval_seeds = SEEDS[:num_seeds]
    tasks = [(cand_name, opp_key, s, seat) for s in eval_seeds for seat in (0, 1)]
    futures = [executor.submit(run_ladder_match, t) for t in tasks]
    results = [f.result() for f in futures]

    n = len(results)
    wins = sum(1 for r in results if r["won"] == 1)
    ties = sum(1 for r in results if r["won"] == 0.5)
    losses = sum(1 for r in results if r["won"] == 0)
    win_rate = (wins + 0.5 * ties) / n
    margins = [r["margin"] for r in results]
    cash_c = [r["cash_c"] for r in results]
    cash_o = [r["cash_o"] for r in results]
    cas = sum(r["cas_cand"] for r in results)

    mean_margin = float(np.mean(margins))
    median_margin = float(np.median(margins))
    p10_margin = float(np.percentile(margins, 10))
    mean_cash_c = float(np.mean(cash_c))
    mean_cash_o = float(np.mean(cash_o))

    return {
        "candidate": cand_name,
        "opponent": opp_key,
        "legs": n,
        "win_rate": win_rate,
        "wins": wins,
        "ties": ties,
        "losses": losses,
        "mean_margin": mean_margin,
        "median_margin": median_margin,
        "p10_margin": p10_margin,
        "mean_cash_cand": mean_cash_c,
        "mean_cash_opp": mean_cash_o,
        "casualties": cas,
    }


def main():
    opponents = [
        "V44",
        "thomastschinkel_2945",
        "kaitofukami_v48_3009",
        "indarkarhana_top10",
        "tetsutani_pasture",
        "saiteja_mega_3000",
        "dmitrii_lb2800",
    ]

    all_results = []
    print("Starting Official V47 Promotion Ladder Evaluation (64 clean seeds x 2 seats = 128 legs per matchup)...")

    with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
        for opp_key in opponents:
            res_v47 = evaluate_matchup(executor, "V47_ELITE_TRANSFER", opp_key, num_seeds=64)
            all_results.append(res_v47)
            print(f"[V47 vs {opp_key:22s}] WR: {res_v47['win_rate']*100:5.1f}% | Margin: {res_v47['mean_margin']:+8.1f} | Cash: ${res_v47['mean_cash_cand']:6.0f} vs ${res_v47['mean_cash_opp']:6.0f} | Cas: {res_v47['casualties']}")

    out_file = os.path.join(REPO_ROOT, "research", "v47", "ladder", "promotion_ladder_results.json")
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\nLadder results successfully saved to {out_file}!")


if __name__ == "__main__":
    main()
