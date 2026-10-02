#!/usr/bin/env python3
"""Run exact causal ablations on thomastschinkel_2945 to identify which layers cause its advantage.

Ablations:
1. FULL: Full 2945 (all layers: CARROT + ORDERPRI2 + CAPHARV + SHEDROOM + HERD2 + COWSWAP)
2. NO_COWSWAP: Cut before line 5523 (stops at line 5520)
3. NO_HERD2: Cut before line 5237 (stops at line 5234)
4. NO_SHEDROOM: Cut before line 5130 (stops at line 5119)
5. NO_CAPHARV: Cut before line 5010 (stops at line 4969)
6. NO_ORDERPRI2: Cut before line 4750 (stops at line 4721)
7. NO_CARROT: Cut before line 4468 (stops at line 4464) -> Raw underlying route chassis

Evaluates each ablation directly vs V44 across 32 seeds x 2 seats = 64 legs in parallel.
"""

from __future__ import annotations
import concurrent.futures
import copy
import json
import os
import sys
import tempfile
from typing import Any, Dict, List, Tuple
import numpy as np

sys.stdout.reconfigure(line_buffering=True)

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from candidates.v44_economic_portfolio.main import V44CandidateController

SEEDS = [249800 + i for i in range(32)]
PROTECTED_HOLDOUTS = [(214200, 214249), (340090, 340199), (249695, 249734)]

for s in SEEDS:
    for start, end in PROTECTED_HOLDOUTS:
        assert not (start <= s <= end), f"CRITICAL: Protected holdout seed {s} accessed!"


def create_ablated_agent_files():
    source_path = os.path.join(REPO_ROOT, "research", "v47", "elite_corpus", "agents", "thomastschinkel_2945", "main.py")
    with open(source_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    ablations = {
        "A0_FULL": len(lines),
        "A1_NO_COWSWAP": 5521,
        "A2_NO_HERD2": 5235,
        "A3_NO_SHEDROOM": 5120,
        "A4_NO_CAPHARV": 4970,
        "A5_NO_ORDERPRI2": 4722,
        "A6_NO_CARROT": 4465,
    }

    out_dir = os.path.join(REPO_ROOT, "research", "v47", "ablations", "generated_agents")
    os.makedirs(out_dir, exist_ok=True)

    agent_paths = {}
    for name, line_count in ablations.items():
        p = os.path.join(out_dir, f"{name}.py")
        with open(p, "w", encoding="utf-8") as f:
            f.writelines(lines[:line_count])
        agent_paths[name] = p

    return agent_paths


def load_raw_agent(agent_path: str):
    import importlib.util
    spec = importlib.util.spec_from_file_location(f"mod_{os.path.basename(agent_path)[:-3]}_{os.getpid()}", agent_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.agent


def run_leg(args: Tuple[str, str, int, int]) -> Dict[str, Any]:
    abl_name, abl_path, seed, seat = args
    opp_seat = 1 - seat

    v44 = V44CandidateController()
    opp_agent = load_raw_agent(abl_path)

    sim = FastKagricultureSim(seed=seed)
    obs_list = sim.reset(seed=seed)

    cas_v44 = 0
    cas_opp = 0
    for step in range(719):
        obs_v44 = obs_list[seat]
        obs_opp = obs_list[opp_seat]

        try:
            act_v44 = v44.act(obs_v44)
        except Exception:
            act_v44 = {"farmer": ["PASS"], "hands": [], "market": []}
            cas_v44 += 1

        try:
            act_opp = opp_agent(obs_opp)
        except Exception:
            act_opp = {"farmer": ["PASS"], "hands": [], "market": []}
            cas_opp += 1

        actions = [act_v44, act_opp] if seat == 0 else [act_opp, act_v44]
        obs_list, rewards, done, info = sim.step(actions)

    cash_v44 = float(obs_list[seat]["farms"][seat]["money"])
    cash_opp = float(obs_list[opp_seat]["farms"][opp_seat]["money"])
    margin_opp = cash_opp - cash_v44

    return {
        "ablation": abl_name,
        "seed": seed,
        "seat": seat,
        "cash_v44": cash_v44,
        "cash_opp": cash_opp,
        "margin_opp": margin_opp,
        "opp_won": 1 if cash_opp > cash_v44 else (0.5 if cash_opp == cash_v44 else 0),
        "cas_v44": cas_v44,
        "cas_opp": cas_opp,
    }


def main():
    agent_paths = create_ablated_agent_files()
    print("Created ablated agent files. Starting parallel evaluation vs V44 across 32 seeds x 2 seats = 64 legs each...")

    results_by_ablation = {}
    with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
        for abl_name, abl_path in agent_paths.items():
            tasks = [(abl_name, abl_path, s, seat) for s in SEEDS for seat in (0, 1)]
            futures = [executor.submit(run_leg, t) for t in tasks]
            results = [f.result() for f in futures]
            results_by_ablation[abl_name] = results

            n = len(results)
            opp_wins = sum(r["opp_won"] for r in results)
            opp_wr = opp_wins / n
            opp_margins = [r["margin_opp"] for r in results]
            opp_cash = [r["cash_opp"] for r in results]
            v44_cash = [r["cash_v44"] for r in results]

            print(f"[{abl_name:16s}] 2945 WR vs V44: {opp_wr*100:5.1f}% | 2945 Margin: {np.mean(opp_margins):+7.1f} | 2945 Cash: ${np.mean(opp_cash):6.0f} | V44 Cash: ${np.mean(v44_cash):6.0f}")

    out_file = os.path.join(REPO_ROOT, "research", "v47", "ablations", "2945_ablation_results.json")
    with open(out_file, "w") as f:
        # Save summary
        summary = {
            k: {
                "wr_vs_v44": float(np.mean([r["opp_won"] for r in v])),
                "mean_margin": float(np.mean([r["margin_opp"] for r in v])),
                "mean_cash_2945": float(np.mean([r["cash_opp"] for r in v])),
                "mean_cash_v44": float(np.mean([r["cash_v44"] for r in v])),
            }
            for k, v in results_by_ablation.items()
        }
        json.dump(summary, f, indent=2)

    print(f"\nAblation study complete! Saved to {out_file}")


if __name__ == "__main__":
    main()
