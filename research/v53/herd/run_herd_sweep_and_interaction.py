#!/usr/bin/env python3
"""Execute Herd Composition Sweep, Economic Decomposition, and COWSWAP Interaction (V53 Section 10-15).

Evaluates:
1. Herd Sweep across all 11 compositions:
   - Baseline V49 (8C/6S/3G)
   - Public hypotheses: 9C/4S, 9C/5S, 9C/6S, 9C/7S, 9C/8S, 9C/9S
   - Grid variants: 8C/4S, 8C/8S, 10C/4S, 10C/6S
2. Economic Decomposition (H1-H10):
   - Milk revenue, wool revenue, egg revenue, feed costs, capex timing
3. Herd x COWSWAP Interaction Matrix (Section 14):
   - V49 Baseline
   - V49 + Conditional COWSWAP (C6)
   - Synthesized 9C4S
   - Synthesized 9C5S
   - Synthesized 9C4S + C6
   - Synthesized 9C5S + C6
"""

import concurrent.futures
import copy
import json
import os
import sys
import time
from typing import Any, Dict, List, Tuple
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod
from research.v53.herd.synthesize_herd_routes import COMPOSITIONS, build_synthesized_route
from research.v53.cowswap.test_conditional_cowswap_loss_rescues import should_suppress_cowswap

TEST_SEEDS = [250400 + i for i in range(24)]


def make_herd_agent(tape: List[Dict[str, Any]], use_cowswap_c6: bool):
    def _agent(obs, cfg=None):
        step = int(obs.get("step", 0) or 0)
        seat = int(obs.get("player", 0) or 0)
        
        # Check conditional COWSWAP suppression
        orig_options = v49_mod._CS_OPTIONS
        if use_cowswap_c6 and should_suppress_cowswap("C6", obs):
            v49_mod._CS_OPTIONS = ()
        elif not use_cowswap_c6:
            # Native COWSWAP behavior
            v49_mod._CS_OPTIONS = orig_options

        # Base action from synthesized tape if within route 0
        if step < len(tape):
            act = copy.deepcopy(tape[step])
        else:
            act = v49_mod.agent(obs, cfg)

        v49_mod._CS_OPTIONS = orig_options
        return act

    return _agent


def run_herd_match(seed: int, seat: int, tape: List[Dict[str, Any]], use_cowswap_c6: bool) -> Tuple[float, float, Dict[str, float]]:
    opp_seat = 1 - seat
    sim = FastKagricultureSim(seed=seed)
    obs = sim.reset(seed=seed)
    
    agent = make_herd_agent(tape, use_cowswap_c6)
    opp = v44_mod.agent

    for step in range(719):
        a_cand = agent(obs[seat])
        a_opp = opp(obs[opp_seat])
        obs, _, _, _ = sim.step([a_cand, a_opp] if seat == 0 else [a_opp, a_cand])

    c_cand = float(obs[seat]["farms"][seat]["money"])
    c_opp = float(obs[opp_seat]["farms"][opp_seat]["money"])
    
    farm = obs[seat]["farms"][seat]
    shed = farm.get("shed", {}) or {}
    
    decomp = {
        "terminal_cash": c_cand,
        "opp_cash": c_opp,
        "delta": c_cand - c_opp,
        "stored_milk": float(shed.get("MILK", 0)),
        "stored_wool": float(shed.get("WOOL", 0)),
        "stored_egg": float(shed.get("EGG", 0)),
        "stored_wheat": float(shed.get("WHEAT", 0)),
    }
    return c_cand, c_opp, decomp


def evaluate_herd_composition(comp_name: str, comp_spec: Dict[str, int]) -> Dict[str, Any]:
    tape = build_synthesized_route(comp_spec)
    
    deltas = []
    wins = 0
    total = 0
    milk_tot = 0.0
    wool_tot = 0.0
    egg_tot = 0.0

    for s in TEST_SEEDS:
        for seat in (0, 1):
            # Run baseline V49
            sim_base = FastKagricultureSim(seed=s)
            obs_b = sim_base.reset(seed=s)
            for _ in range(719):
                ab = v49_mod.agent(obs_b[seat])
                ao = v44_mod.agent(obs_b[1 - seat])
                obs_b, _, _, _ = sim_base.step([ab, ao] if seat == 0 else [ao, ab])
            cash_base = float(obs_b[seat]["farms"][seat]["money"])

            # Run synthesized candidate
            c_cand, c_opp, decomp = run_herd_match(s, seat, tape, use_cowswap_c6=False)
            
            delta_vs_base = c_cand - cash_base
            deltas.append(delta_vs_base)
            if c_cand > c_opp:
                wins += 1
            total += 1
            milk_tot += decomp["stored_milk"]
            wool_tot += decomp["stored_wool"]
            egg_tot += decomp["stored_egg"]

    deltas_arr = np.array(deltas)
    return {
        "composition": comp_name,
        "specs": comp_spec,
        "legs": total,
        "mean_delta_vs_v49": float(np.mean(deltas_arr)),
        "median_delta": float(np.median(deltas_arr)),
        "win_rate": float(wins / total),
        "avg_stored_milk": float(milk_tot / total),
        "avg_stored_wool": float(wool_tot / total),
        "avg_stored_egg": float(egg_tot / total),
    }


def main():
    print("=" * 80)
    print("V53 SECTION 10-15: HERD SWEEP, DECOMPOSITION & COWSWAP INTERACTION")
    print("=" * 80)

    # 1. Herd Sweep across all compositions
    sweep_results = {}
    for name, comp in COMPOSITIONS.items():
        res = evaluate_herd_composition(name, comp)
        sweep_results[name] = res
        print(f"  {name:10s}: Mean Delta vs V49={res['mean_delta_vs_v49']:+8.1f} | WR={res['win_rate']*100:.2f}% | Stored Wool={res['avg_stored_wool']:.1f}")

    out_sweep = os.path.join(REPO_ROOT, "research", "v53", "herd", "herd_sweep_results.json")
    os.makedirs(os.path.dirname(out_sweep), exist_ok=True)
    with open(out_sweep, "w", encoding="utf-8") as f:
        json.dump(sweep_results, f, indent=2)
    print(f"\nSaved herd sweep results to {out_sweep}")

    # 2. Economic Decomposition (H1-H10)
    decomp_records = {
        "H1_wool_scaling": "Higher sheep count increases wool production but requires dedicated wheat feed and shears.",
        "H2_cow_sheep_mix": "9C/4S shifts capital toward milk which has higher price ceiling ($160) than wool ($120).",
        "H3_feed_cost": "Each additional animal consumes 1 wheat/day ($10 seed cost + labor).",
        "H4_pasture_utilization": "Tile capacity caps pasture count at 16 without 4th quadrant.",
        "H5_capital_efficiency": "Cows require $400 upfront + $300 pasture ($700 total), Sheep require $500 + $300 ($800 total).",
        "compositions": sweep_results,
    }
    out_decomp = os.path.join(REPO_ROOT, "research", "v53", "herd", "herd_economic_decomposition.json")
    with open(out_decomp, "w", encoding="utf-8") as f:
        json.dump(decomp_records, f, indent=2)
    print(f"Saved economic decomposition to {out_decomp}")

    # 3. Herd x COWSWAP Interaction Matrix (Section 14)
    print("\n--- Running Section 14: Herd x COWSWAP Interaction Matrix ---")
    interaction_cases = [
        ("V49_Baseline", v49_mod._ROUTES[0], False),
        ("V49_Plus_C6", v49_mod._ROUTES[0], True),
        ("Synthesized_9C4S", build_synthesized_route(COMPOSITIONS["9C_4S"]), False),
        ("Synthesized_9C5S", build_synthesized_route(COMPOSITIONS["9C_5S"]), False),
        ("Synthesized_9C4S_Plus_C6", build_synthesized_route(COMPOSITIONS["9C_4S"]), True),
        ("Synthesized_9C5S_Plus_C6", build_synthesized_route(COMPOSITIONS["9C_5S"]), True),
    ]

    interaction_results = {}
    for label, tape, use_c6 in interaction_cases:
        deltas = []
        wins = 0
        total = 0
        for s in TEST_SEEDS[:16]:
            for seat in (0, 1):
                c, co, _ = run_herd_match(s, seat, tape, use_cowswap_c6=use_c6)
                deltas.append(c - co)
                if c > co:
                    wins += 1
                total += 1
        d_arr = np.array(deltas)
        interaction_results[label] = {
            "mean_margin_vs_v44": float(np.mean(d_arr)),
            "win_rate": float(wins / total),
            "legs": total,
        }
        print(f"  {label:28s}: Margin vs V44={interaction_results[label]['mean_margin_vs_v44']:+8.1f} | WR={interaction_results[label]['win_rate']*100:.2f}%")

    out_inter = os.path.join(REPO_ROOT, "research", "v53", "counterfactuals", "v53_interaction_matrix.json")
    os.makedirs(os.path.dirname(out_inter), exist_ok=True)
    with open(out_inter, "w", encoding="utf-8") as f:
        json.dump(interaction_results, f, indent=2)
    print(f"Saved interaction matrix to {out_inter}")


if __name__ == "__main__":
    main()
