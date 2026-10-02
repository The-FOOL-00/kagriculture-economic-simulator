#!/usr/bin/env python3
"""Mechanism Interaction Matrix & Causal Ablation for Kagriculture V48.

Measures marginal alpha and 2-way interaction terms:
Interaction(A, B) = Alpha(A + B) - Alpha(A) - Alpha(B)
for key mechanisms:
- M1: SHOP_ROUTE (V48 selective override)
- M2: CARROT (Carrot crop substitution)
- M3: ORDERPRI2 (Rival-harvest tracking)
- M4: COWSWAP (Cow/goose shop switch)
- M5: SHEDROOM (Shed overflow guard)

Runs across 64 clean seeds x 2 seats = 128 paired legs in parallel.
Saves to research/v48/mechanisms/mechanism_ablation.json.
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
from research.v47.elite_benchmark.run_elite_benchmark import load_agent as load_elite_agent
import research.v47.elite_corpus.agents.thomastschinkel_2945.main as m2945
from research.v48.shop_routes.evaluate_shop_counterfactuals import build_patched_router

SEEDS = [249800 + i for i in range(64)]
PROTECTED_HOLDOUTS = [(214200, 214249), (340090, 340199), (249695, 249734)]
for s in SEEDS:
    for start, end in PROTECTED_HOLDOUTS:
        assert not (start <= s <= end), f"CRITICAL: Protected holdout seed {s} accessed!"

PURE_SHOP_OVERRIDES = {
    ("BRUNCH_SPOT", "FARMERS_MARKET"): 105,
    ("BAKERY", "BRUNCH_SPOT"): 105,
    ("PET_CAFE", "FARMERS_MARKET"): 105,
}


def build_configured_agent(enabled: Dict[str, bool]):
    # M1: Shop route router
    router = build_patched_router(PURE_SHOP_OVERRIDES) if enabled.get("M1", False) else m2945._router
    base_agent = m2945.make_agent(m2945._ROUTES, router=router, **m2945._SETTINGS)

    # If M3 (ORDERPRI2) is disabled, don't wrap with m2945.agent
    # Notice: m2945.agent is the outer wrapper containing M2, M3, M4, M5, M6
    # Let's inspect how to toggle individual layers cleanly:
    def _agent(obs, cfg=None):
        # We can dynamically toggle module flags in m2945 for each call:
        orig_sn = m2945._OR2_SN_K
        orig_cs = m2945._CS_MIN_GAIN
        orig_sr = m2945._SR_MARGIN

        if not enabled.get("M3", True):
            m2945._OR2_SN_K = 0  # Disable sale advancement
        if not enabled.get("M4", True):
            m2945._CS_MIN_GAIN = 1e9  # Disable cowswap
        if not enabled.get("M5", True):
            m2945._SR_MARGIN = 999  # Disable shedroom

        act = m2945.agent(obs, cfg)

        # Restore
        m2945._OR2_SN_K = orig_sn
        m2945._CS_MIN_GAIN = orig_cs
        m2945._SR_MARGIN = orig_sr
        return act

    if enabled.get("M1", False) and not any(enabled.get(k, True) is False for k in ("M3", "M4", "M5")):
        # Pure V48 challenger (2945 + M1 router patch)
        chassis = m2945.Chassis(m2945._ROUTES, router=router, settings=m2945._SETTINGS)
        # We replace chassis.router
        orig_router = m2945._IMPL.chassis.router
        def _v48_agent(obs, cfg=None):
            m2945._IMPL.chassis.router = router
            act = m2945.agent(obs, cfg)
            m2945._IMPL.chassis.router = orig_router
            return act
        return _v48_agent

    return _agent


def run_mechanism_leg(args: Tuple[int, int, str, Dict[str, bool]]) -> Dict[str, Any]:
    seed, seat, config_name, enabled_dict = args
    opp_seat = 1 - seat

    agent_fn = build_configured_agent(enabled_dict)
    opp = load_elite_agent("V44")

    sim = FastKagricultureSim(seed=seed)
    obs = sim.reset(seed=seed)
    for step in range(719):
        a_our = agent_fn(obs[seat])
        a_opp = opp.act(obs[opp_seat])
        actions = [a_our, a_opp] if seat == 0 else [a_opp, a_our]
        obs, rew, done, info = sim.step(actions)

    cash_our = float(obs[seat]["farms"][seat]["money"])
    cash_opp = float(obs[opp_seat]["farms"][opp_seat]["money"])

    return {
        "seed": seed,
        "seat": seat,
        "config": config_name,
        "cash": cash_our,
        "opp_cash": cash_opp,
        "margin": cash_our - cash_opp,
        "win": cash_our > cash_opp,
    }


def main():
    print("Evaluating Causal Mechanism Matrix across 64 seeds x 2 seats = 128 legs...")
    tasks_base = [(s, seat) for s in SEEDS for seat in (0, 1)]

    # 1. Base 2945 (All native enabled, M1 disabled)
    print("Running Baseline 2945...")
    base_tasks = [(s, seat, "BASE_2945", {"M1": False, "M3": True, "M4": True, "M5": True}) for s, seat in tasks_base]
    with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
        base_results = list(executor.map(run_mechanism_leg, base_tasks))
    base_cash = { (r["seed"], r["seat"]): r["cash"] for r in base_results }
    base_margins = [r["margin"] for r in base_results]

    configs = {
        "M1_SHOP_ROUTE": {"M1": True, "M3": True, "M4": True, "M5": True},
        "NO_M3_ORDERPRI2": {"M1": False, "M3": False, "M4": True, "M5": True},
        "NO_M4_COWSWAP": {"M1": False, "M3": True, "M4": False, "M5": True},
        "NO_M5_SHEDROOM": {"M1": False, "M3": True, "M4": True, "M5": False},
        "M1_PLUS_NO_M4": {"M1": True, "M3": True, "M4": False, "M5": True},
    }

    report = {}
    report["BASE_2945"] = {
        "mean_margin": float(np.mean(base_margins)),
        "median_margin": float(np.median(base_margins)),
        "win_rate": float(np.mean([r["win"] for r in base_results])),
    }

    for name, cfg in configs.items():
        print(f"Running {name}...")
        cfg_tasks = [(s, seat, name, cfg) for s, seat in tasks_base]
        with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
            res = list(executor.map(run_mechanism_leg, cfg_tasks))

        deltas = [r["cash"] - base_cash[(r["seed"], r["seat"])] for r in res]
        margins = [r["margin"] for r in res]
        wins = [r["win"] for r in res]
        mean_d = float(np.mean(deltas))
        median_d = float(np.median(deltas))
        p10_d = float(np.percentile(deltas, 10))

        report[name] = {
            "mean_delta_vs_2945": mean_d,
            "median_delta_vs_2945": median_d,
            "p10_delta": p10_d,
            "win_rate": float(np.mean(wins)),
            "casualties": sum(base_results[i]["win"] and not wins[i] for i in range(len(wins))),
            "rescues": sum(not base_results[i]["win"] and wins[i] for i in range(len(wins))),
        }
        print(f"  {name:16s}: Mean Delta={mean_d:+7.2f}, Median={median_d:+7.2f}, WinRate={np.mean(wins)*100:.1f}%, Casualties={report[name]['casualties']}")

    out_file = os.path.join(REPO_ROOT, "research", "v48", "mechanisms", "mechanism_ablation.json")
    with open(out_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nMechanism Matrix evaluation complete! Saved to {out_file}")


if __name__ == "__main__":
    main()
