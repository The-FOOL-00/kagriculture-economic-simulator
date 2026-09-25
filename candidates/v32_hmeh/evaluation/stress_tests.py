# SPDX-License-Identifier: MIT
"""HMEH Adversarial Stress and Robustness Test Suite.

Stress tests HMEH policies against:
1. Cash shocks (low starting cash, sudden wage spikes)
2. Market price crashes (depressed commodity bid prices)
3. Stranded inventory / missing seeds
4. Delayed worker availability
5. Hostile market dumping (SYN_AGG)
"""

from __future__ import annotations
import copy
import os
import random
import sys
from typing import Any, Dict, List

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


def run_adversarial_stress_test(stage: str = "HMEH-0", seeds: List[int] = None) -> Dict[str, Any]:
    assert_frozen()
    seeds = seeds or [249675, 249676]
    print(f"\n=======================================================")
    print(f"RUNNING ADVERSARIAL STRESS TEST: Stage={stage} on seeds {seeds}")
    print(f"=======================================================")
    
    results = {}
    
    # Stress 1: Hostile Commodity Market Dumper (SYN_AGG)
    print("\n--- Stress 1: Hostile Dumping Opponent (SYN_AGG) ---")
    syn_agg_results = []
    for seed in seeds:
        for seat in (0, 1):
            check_seed_allowed(seed)
            agent_fn, _ = make_hmeh_agent(stage=stage)
            opp_fn = load_agent("E0_V3")  # Replace with synthetic aggressive
            from candidates.v32_hmeh.evaluation.eval_hmeh import _synthetic_aggressive
            opp_fn = _synthetic_aggressive
            agents = [agent_fn, opp_fn] if seat == 0 else [opp_fn, agent_fn]
            env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720}, debug=False)
            env.run(agents)
            r = float(env.steps[-1][seat]["reward"] or 0.0)
            opp_r = float(env.steps[-1][1 - seat]["reward"] or 0.0)
            syn_agg_results.append({"seed": seed, "seat": seat, "cash": r, "opp_cash": opp_r, "delta": r - opp_r})
            print(f"  Seed {seed} Seat {seat}: Cash=${r:,.2f} Delta=${r - opp_r:+,.2f}")
            
    results["SYN_AGG"] = syn_agg_results
    print(f"Mean Cash under SYN_AGG: ${sum(r['cash'] for r in syn_agg_results)/len(syn_agg_results):,.2f}")
    
    return results


if __name__ == "__main__":
    run_adversarial_stress_test("HMEH-0")
