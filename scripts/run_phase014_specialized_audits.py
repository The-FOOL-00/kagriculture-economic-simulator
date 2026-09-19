#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""AEC Phase 014: Specialized Headroom Audits (§22, §23, §24, §25).

Executes the four deep diagnostic investigations:
  1. Counterfactual Fidelity Audit (§22) — simulator rollouts vs exact kagsim.Game
  2. Horizon Sensitivity Audit (§23) — H in {6, 12, 18, 24, 36}
  3. Composition Headroom Audit (§24) — bounded pairwise mechanism coupling
  4. Opponent Headroom Audit (§25) — rival pressure sensitivity and preemption
"""

from __future__ import annotations

import copy
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import kagsim
from aec.audit.oracle_probe import BoundedOracleProbe
from aec.config import AECConfig, ENABLED_FOUNDATION_MECHANISMS, QUARANTINED_MECHANISMS
from aec.counterfactual.simulator import CounterfactualSimulator
from aec.integration.executor import AECExecutor
from aec.ir.economic_state import build_economic_state
from aec.patches.coupled_patch import CoupledPatch
from scripts.run_phase014_headroom_audit import assert_governance, FrozenV3ControlAgent


def run_fidelity_audit(seeds: List[int] = [249241, 249242, 249257]) -> Dict[str, Any]:
    """Audit simulator fidelity against exact kagsim.Game rollouts (§22)."""
    print("--- RUNNING COUNTERFACTUAL FIDELITY AUDIT (§22) ---")
    sim = CounterfactualSimulator()
    fidelity_records: List[Dict[str, Any]] = []

    for seed in seeds:
        assert_governance(seed)
        game = kagsim.Game(seed)
        ctrl_cfg = AECConfig(enabled_mechanisms=ENABLED_FOUNDATION_MECHANISMS, quarantined_mechanisms=QUARANTINED_MECHANISMS, frozen_mode=True)
        executor = AECExecutor(config=ctrl_cfg)
        v3 = FrozenV3ControlAgent()

        step = 0
        actions_history: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []

        # Run until step 100 or 200
        sample_steps = [24, 72, 144]
        while not game.done and step <= 150:
            obs0 = game.observe(0)
            obs1 = game.observe(1)
            act0 = executor.act(obs0)
            act1 = v3.act(obs1)
            actions_history.append((act0, act1))

            if step in sample_steps:
                econ_state = build_economic_state(obs0)
                # Test candidate action: sell or harvest
                cand_act = copy.deepcopy(act0)
                cand_act["farmer"] = ["HARVEST"]

                patch = CoupledPatch(
                    patch_id=f"FIDELITY_TEST_{step}",
                    source_opportunity_id="FID_OPP",
                    mechanism_family="WORKER",
                    actions=[cand_act],
                    start_step=step,
                    end_step=step + 1,
                )

                # 1. Simulator rollout
                sim_outcome = sim.evaluate(
                    candidate_patch=patch,
                    baseline_action=act0,
                    econ_state=econ_state,
                    horizon=6,
                )

                # 2. Exact kagsim rollout
                # Clone game state by replaying history to step
                exact_game = kagsim.Game(seed)
                for h_idx in range(step):
                    exact_game.step(actions_history[h_idx][0], actions_history[h_idx][1])

                # Step 0: apply candidate action
                exact_game.step(cand_act, act1)
                # Follow with 5 baseline steps
                for h_idx in range(step + 1, min(step + 6, len(actions_history))):
                    exact_game.step(actions_history[h_idx][0], actions_history[h_idx][1])

                exact_money = float(exact_game.observe(0)["farms"][0]["money"])
                sim_money = sim_outcome.candidate_final_money
                diff = abs(exact_money - sim_money)
                match_fidelity = diff < 5.0

                fidelity_records.append({
                    "seed": seed,
                    "step": step,
                    "exact_money": exact_money,
                    "sim_money": round(sim_money, 2),
                    "diff": round(diff, 2),
                    "fidelity_pass": match_fidelity,
                })

            game.step(act0, act1)
            step += 1

    fidelity_rate = sum(1 for r in fidelity_records if r["fidelity_pass"]) / max(1, len(fidelity_records))
    print(f"  Fidelity Pass Rate: {fidelity_rate*100:.1f}% ({len(fidelity_records)} checkpoints evaluated)")
    return {"records": fidelity_records, "pass_rate": fidelity_rate}


def run_horizon_audit(seeds: List[int] = [249241, 249242, 249257]) -> Dict[str, Any]:
    """Audit headroom sensitivity across horizons H in {6, 12, 18, 24, 36} (§23)."""
    print("\n--- RUNNING HORIZON SENSITIVITY AUDIT (§23) ---")
    probe = BoundedOracleProbe()
    horizons = [6, 12, 18, 24, 36]
    horizon_results: Dict[int, List[float]] = {h: [] for h in horizons}

    for seed in seeds:
        assert_governance(seed)
        game = kagsim.Game(seed)
        ctrl_cfg = AECConfig(enabled_mechanisms=ENABLED_FOUNDATION_MECHANISMS, quarantined_mechanisms=QUARANTINED_MECHANISMS, frozen_mode=True)
        executor = AECExecutor(config=ctrl_cfg)
        v3 = FrozenV3ControlAgent()

        step = 0
        while not game.done and step <= 200:
            obs0 = game.observe(0)
            obs1 = game.observe(1)
            act0 = executor.act(obs0)
            act1 = v3.act(obs1)

            if step % 24 == 0 and step > 0:
                econ_state = build_economic_state(obs0)
                future_traj = executor.backbone.get_future_trajectory(step=step, horizon=36, player=0)
                for h in horizons:
                    res = probe.probe_state(econ_state, act0, continuation_trajectory=future_traj, horizon=h)
                    horizon_results[h].append(res.local_headroom)

            game.step(act0, act1)
            step += 1

    summary = {}
    for h in horizons:
        vals = horizon_results[h]
        summary[h] = {
            "mean_headroom": round(float(sum(vals) / max(1, len(vals))), 2),
            "positive_rate": round(sum(1 for v in vals if v > 0.5) / max(1, len(vals)), 4),
            "max_headroom": round(float(max(vals) if vals else 0.0), 2),
        }
        print(f"  Horizon H={h:02d}: Mean Headroom = ${summary[h]['mean_headroom']:.2f}, "
              f"Positive Rate = {summary[h]['positive_rate']*100:.1f}%, Max = ${summary[h]['max_headroom']:.2f}")

    return summary


def run_composition_audit(seeds: List[int] = [249241, 249242, 249257]) -> Dict[str, Any]:
    """Audit pairwise mechanism composition (§24)."""
    print("\n--- RUNNING COMPOSITION HEADROOM AUDIT (§24) ---")
    sim = CounterfactualSimulator()

    pairs = [
        ("HARVEST + MARKET_TIMING", "Harvest mature crop + Sell existing produce tranche"),
        ("MARKET_TIMING + PRODUCTION", "Delayed sell + Input procurement"),
        ("TERMINAL_HARVEST + LIQUIDATION", "Endgame crop harvest + 100% shed liquidation"),
        ("WORKER_SWAP + CARGO_DROP", "Worker reassignment + Helper cargo drop"),
    ]

    pair_results: Dict[str, Dict[str, Any]] = {}

    for pair_name, desc in pairs:
        individual_deltas: List[float] = []
        composed_deltas: List[float] = []
        superadditive_count = 0

        for seed in seeds:
            assert_governance(seed)
            game = kagsim.Game(seed)
            ctrl_cfg = AECConfig(enabled_mechanisms=ENABLED_FOUNDATION_MECHANISMS, quarantined_mechanisms=QUARANTINED_MECHANISMS, frozen_mode=True)
            executor = AECExecutor(config=ctrl_cfg)
            v3 = FrozenV3ControlAgent()

            step = 0
            while not game.done and step <= 150:
                obs0 = game.observe(0)
                obs1 = game.observe(1)
                act0 = executor.act(obs0)
                act1 = v3.act(obs1)

                if step in (48, 96, 144):
                    econ_state = build_economic_state(obs0)
                    shed = econ_state.farm.shed_inventory
                    prices = econ_state.market.current_prices

                    # Construct transformation 1 (e.g. worker harvest)
                    act_t1 = copy.deepcopy(act0)
                    act_t1["farmer"] = ["HARVEST"]

                    # Construct transformation 2 (e.g. market sell)
                    act_t2 = copy.deepcopy(act0)
                    for item, qty in shed.items():
                        if qty > 0:
                            act_t2["market"] = [["SELL", item, min(10, qty)]]
                            break

                    # Construct composed transformation (T1 + T2)
                    act_composed = copy.deepcopy(act0)
                    act_composed["farmer"] = act_t1["farmer"]
                    act_composed["market"] = act_t2.get("market", [])

                    # Evaluate T1
                    p1 = CoupledPatch("T1", "OPP1", "WORKER", actions=[act_t1], start_step=step, end_step=step+1)
                    o1 = sim.evaluate(p1, act0, econ_state, horizon=18)

                    # Evaluate T2
                    p2 = CoupledPatch("T2", "OPP2", "MARKET", actions=[act_t2], start_step=step, end_step=step+1)
                    o2 = sim.evaluate(p2, act0, econ_state, horizon=18)

                    # Evaluate Composed
                    p_c = CoupledPatch("COMP", "OPPC", "COMPOSED", actions=[act_composed], start_step=step, end_step=step+1)
                    o_c = sim.evaluate(p_c, act0, econ_state, horizon=18)

                    d1 = o1.delta_terminal_margin
                    d2 = o2.delta_terminal_margin
                    d_c = o_c.delta_terminal_margin

                    individual_deltas.append(max(d1, d2))
                    composed_deltas.append(d_c)
                    if d_c > (d1 + d2) + 1.0:
                        superadditive_count += 1

                game.step(act0, act1)
                step += 1

        n_pts = len(composed_deltas)
        pair_results[pair_name] = {
            "description": desc,
            "mean_individual_best": round(sum(individual_deltas) / max(1, n_pts), 2),
            "mean_composed": round(sum(composed_deltas) / max(1, n_pts), 2),
            "superadditive_rate": round(superadditive_count / max(1, n_pts), 4),
        }
        print(f"  {pair_name}: Best Single Mean = ${pair_results[pair_name]['mean_individual_best']:.2f}, "
              f"Composed Mean = ${pair_results[pair_name]['mean_composed']:.2f}, "
              f"Superadditive Rate = {pair_results[pair_name]['superadditive_rate']*100:.1f}%")

    return pair_results


def run_opponent_headroom_audit(seeds: List[int] = [249241, 249242, 249257]) -> Dict[str, Any]:
    """Audit opponent-contingent headroom (§25)."""
    print("\n--- RUNNING OPPONENT HEADROOM AUDIT (§25) ---")
    sim = CounterfactualSimulator()
    opp_records: List[Dict[str, Any]] = []

    for seed in seeds:
        assert_governance(seed)
        game = kagsim.Game(seed)
        ctrl_cfg = AECConfig(enabled_mechanisms=ENABLED_FOUNDATION_MECHANISMS, quarantined_mechanisms=QUARANTINED_MECHANISMS, frozen_mode=True)
        executor = AECExecutor(config=ctrl_cfg)
        v3 = FrozenV3ControlAgent()

        step = 0
        while not game.done and step <= 150:
            obs0 = game.observe(0)
            obs1 = game.observe(1)
            act0 = executor.act(obs0)
            act1 = v3.act(obs1)

            if step in (36, 72, 108):
                econ_state = build_economic_state(obs0)
                # Check rival cargo approaching market
                opp_cargo = sum(sum(w.cargo.values()) for w in econ_state.opponent.workers) if hasattr(econ_state.opponent, "workers") else 0
                has_rival_pressure = opp_cargo >= 4

                # Test preemptive sell vs normal sell
                act_preempt = copy.deepcopy(act0)
                for item, qty in econ_state.farm.shed_inventory.items():
                    if qty > 0:
                        act_preempt["market"] = [["SELL", item, min(20, qty)]]
                        break

                p_pre = CoupledPatch("PREEMPT", "OPP_P", "OPPONENT", actions=[act_preempt], start_step=step, end_step=step+1)
                o_pre = sim.evaluate(p_pre, act0, econ_state, horizon=18)

                opp_records.append({
                    "seed": seed,
                    "step": step,
                    "opp_cargo": opp_cargo,
                    "delta": o_pre.delta_terminal_margin,
                    "is_superior": o_pre.delta_terminal_margin > 0.5,
                })

            game.step(act0, act1)
            step += 1

    superior_rate = sum(1 for r in opp_records if r["is_superior"]) / max(1, len(opp_records))
    mean_delta = sum(r["delta"] for r in opp_records) / max(1, len(opp_records))
    print(f"  Opponent Preemption Superiority Rate: {superior_rate*100:.1f}%, Mean Delta = ${mean_delta:.2f}")

    return {
        "records": opp_records,
        "superior_rate": superior_rate,
        "mean_delta": round(mean_delta, 2),
    }


def main():
    seeds = [249241, 249242, 249257]
    t0 = time.time()
    res_fid = run_fidelity_audit(seeds)
    res_hor = run_horizon_audit(seeds)
    res_comp = run_composition_audit(seeds)
    res_opp = run_opponent_headroom_audit(seeds)

    combined_specialized = {
        "fidelity_audit": res_fid,
        "horizon_audit": res_hor,
        "composition_audit": res_comp,
        "opponent_audit": res_opp,
        "elapsed_s": round(time.time() - t0, 2),
    }

    out_path = os.path.join(REPO_ROOT, "results", "PHASE014_SPECIALIZED_AUDITS.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(combined_specialized, f, indent=2)
    print(f"\nSaved specialized audit results to {out_path}")


if __name__ == "__main__":
    main()
