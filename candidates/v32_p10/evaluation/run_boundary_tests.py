# SPDX-License-Identifier: MIT
"""EXP-V32-P10-06: Adversarial Boundary & Perturbation Audit.

Tests R02_B near its decision boundary by perturbing trigger thresholds:
- Cash threshold: $300 vs $400 vs $500
- Market inventory threshold: 20 vs 30 vs 40 units
- Opponent dump threshold: 4 vs 8 vs 12 units
Measures whether boundary perturbations cause catastrophic cliff-edge losses.
"""

from __future__ import annotations
import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
P10_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in (REPO_ROOT, os.path.join(REPO_ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
if P10_ROOT not in sys.path:
    sys.path.append(P10_ROOT)

from kaggle_environments import make
from v32_common import assert_frozen, check_seed_allowed, load_agent
from candidates.v32_p10.incumbent import load_fresh_a7
from candidates.v32_p10.regime_detector import DeterministicRegimeDetector


def run_boundary_audit() -> dict:
    assert_frozen()
    seed = 249687  # The seed where R02_B suffered -$489 tail loss
    check_seed_allowed(seed)
    
    thresholds = [
        {"name": "Aggressive_Threshold", "cash_min": 300.0, "inv_min": 20, "opp_dump_min": 4},
        {"name": "Nominal_R02_B", "cash_min": 400.0, "inv_min": 30, "opp_dump_min": 8},
        {"name": "Conservative_Threshold", "cash_min": 600.0, "inv_min": 40, "opp_dump_min": 12},
    ]
    
    results = {}
    print(f"\nRunning Adversarial Boundary Audit on Seed {seed} vs E0_V3...")
    
    # Baseline A7
    a7_agent = load_fresh_a7()
    opp_fn1 = load_agent("E0_V3")
    env_base = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720}, debug=False)
    env_base.run([a7_agent, opp_fn1])
    baseline_cash = float(env_base.steps[-1][0]["reward"] or 0.0)
    
    for th in thresholds:
        detector = DeterministicRegimeDetector()
        a7_inst = load_fresh_a7()
        acts = 0
        
        def _make_agent(th_cfg):
            def _agent(obs, cfg=None):
                nonlocal acts
                base = a7_inst(obs, cfg)
                s = int(obs.get("step", 0) or 0)
                if s <= 10 or s >= 680:
                    return base
                f = detector.detect(obs)
                for o in base.get("market") or []:
                    if o and o[0] == "SELL" and len(o) >= 3:
                        prod, qty = o[1], int(o[2])
                        opp_sold = f.opp_recent_sales.get(prod, 0)
                        inv = f.market_inventory.get(prod, 0)
                        if opp_sold >= th_cfg["opp_dump_min"] and inv >= th_cfg["inv_min"] and f.player_cash > th_cfg["cash_min"]:
                            acts += 1
                            mkt = copy.deepcopy(base.get("market") or [])
                            for m in mkt:
                                if m and m[0] == "SELL" and m[1] == prod:
                                    m[2] = max(4, int(m[2]) // 2)
                            act = copy.deepcopy(base)
                            act["market"] = mkt
                            return act
                return base
            import copy
            return _agent
            
        opp_fn2 = load_agent("E0_V3")
        env_test = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720}, debug=False)
        env_test.run([_make_agent(th), opp_fn2])
        cand_cash = float(env_test.steps[-1][0]["reward"] or 0.0)
        delta = cand_cash - baseline_cash
        
        results[th["name"]] = {
            "cash": cand_cash,
            "baseline": baseline_cash,
            "delta": delta,
            "activations": acts
        }
        print(f"  [{th['name']}]: Delta=${delta:+,.2f} ({acts} activations)")
        
    out_path = os.path.join(P10_ROOT, "reports", "adversarial_boundary_results.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    return results


if __name__ == "__main__":
    run_boundary_audit()
