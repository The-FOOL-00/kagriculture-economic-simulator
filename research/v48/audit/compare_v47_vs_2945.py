#!/usr/bin/env python3
"""Exact differential analysis between V47 and raw thomastschinkel_2945.

Runs across the 64 clean dev seeds (128 legs) to:
1. Classify every game as EXACT_PARITY, MINOR_OVERLAY, MATERIAL_DIFFERENCE.
2. Isolate the exact 9 wins and 9 losses from the 128-leg ladder.
3. Inspect step-by-step action divergences, first divergence step, and causal factors.
"""

from __future__ import annotations
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

SEEDS = [249800 + i for i in range(64)]
PROTECTED_HOLDOUTS = [(214200, 214249), (340090, 340199), (249695, 249734)]

for s in SEEDS:
    for start, end in PROTECTED_HOLDOUTS:
        assert not (start <= s <= end), f"CRITICAL: Protected holdout seed {s} accessed!"


def load_raw_2945():
    import importlib.util
    p = os.path.join(REPO_ROOT, "research", "v47", "elite_corpus", "agents", "thomastschinkel_2945", "main.py")
    mod_name = f"mod_raw_2945_{os.getpid()}"
    spec = importlib.util.spec_from_file_location(mod_name, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.agent


def load_v47():
    import importlib.util
    p = os.path.join(REPO_ROOT, "candidates", "v47_elite_transfer", "main.py")
    mod_name = f"mod_v47_{os.getpid()}"
    spec = importlib.util.spec_from_file_location(mod_name, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.agent


def run_differential_leg(seed: int, seat_v47: int):
    seat_2945 = 1 - seat_v47
    agent_v47 = load_v47()
    agent_2945 = load_raw_2945()

    sim = FastKagricultureSim(seed=seed)
    obs_list = sim.reset(seed=seed)

    first_div_step = None
    div_steps = []
    div_details = []

    for step in range(719):
        obs_v47 = obs_list[seat_v47]
        obs_2945 = obs_list[seat_2945]

        act_v47 = agent_v47(obs_v47)
        act_2945 = agent_2945(obs_2945)

        # Check action identity
        diffs = []
        if act_v47.get("farmer") != act_2945.get("farmer"):
            diffs.append("farmer")
        if act_v47.get("hands") != act_2945.get("hands"):
            diffs.append("hands")
        if act_v47.get("market") != act_2945.get("market"):
            diffs.append("market")

        if diffs:
            div_steps.append(step)
            if first_div_step is None:
                first_div_step = step
            if len(div_details) < 10:
                div_details.append({
                    "step": step,
                    "diffs": diffs,
                    "v47_mkt": act_v47.get("market"),
                    "2945_mkt": act_2945.get("market"),
                    "v47_farmer": act_v47.get("farmer"),
                    "2945_farmer": act_2945.get("farmer"),
                })

        actions = [act_v47, act_2945] if seat_v47 == 0 else [act_2945, act_v47]
        obs_list, rewards, done, info = sim.step(actions)

    cash_v47 = float(obs_list[seat_v47]["farms"][seat_v47]["money"])
    cash_2945 = float(obs_list[seat_2945]["farms"][seat_2945]["money"])
    margin = cash_v47 - cash_2945

    if margin > 0:
        outcome = "V47_WIN"
    elif margin == 0:
        outcome = "TIE"
    else:
        outcome = "V47_LOSS"

    if len(div_steps) == 0:
        classification = "EXACT_PARITY"
    elif len(div_steps) <= 5 and all(d["diffs"] == ["market"] for d in div_details):
        classification = "MINOR_OVERLAY"
    else:
        classification = "MATERIAL_DIFFERENCE"

    return {
        "seed": seed,
        "seat_v47": seat_v47,
        "cash_v47": cash_v47,
        "cash_2945": cash_2945,
        "margin": margin,
        "outcome": outcome,
        "classification": classification,
        "first_div_step": first_div_step,
        "num_div_steps": len(div_steps),
        "div_details": div_details,
    }


def main():
    print("Running differential audit across 64 seeds x 2 seats = 128 legs...")
    results = []
    for s in SEEDS:
        for seat in (0, 1):
            res = run_differential_leg(s, seat)
            results.append(res)
            if res["outcome"] != "TIE":
                print(f"  Seed {s} (V47 Seat {seat}): {res['outcome']} | Margin: {res['margin']:+.1f} | 1st Div Step: {res['first_div_step']} | Total Div Steps: {res['num_div_steps']}")

    outcomes = [r["outcome"] for r in results]
    classes = [r["classification"] for r in results]

    print("\n=== SUMMARY ===")
    print(f"Outcomes: V47 Wins={outcomes.count('V47_WIN')}, Ties={outcomes.count('TIE')}, Losses={outcomes.count('V47_LOSS')}")
    print(f"Classifications: EXACT_PARITY={classes.count('EXACT_PARITY')}, MINOR_OVERLAY={classes.count('MINOR_OVERLAY')}, MATERIAL_DIFFERENCE={classes.count('MATERIAL_DIFFERENCE')}")

    out_file = os.path.join(REPO_ROOT, "research", "v48", "audit", "2945_diff.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Differential results saved to {out_file}")


if __name__ == "__main__":
    main()
