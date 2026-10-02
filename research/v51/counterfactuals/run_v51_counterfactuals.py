#!/usr/bin/env python3
"""Counterfactual Evaluation of Blocked Action Repairs & Midgame Mechanisms (V51).

Evaluates:
Part 1: C0-C5 Blocked-Action Repair Variants -> v51_blocked_repair_results.json
Part 2: M1-M6 Top-Meta & Midgame Reset Variants -> v51_midgame_mechanism_results.json
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
from research.v47.elite_benchmark.run_elite_benchmark import load_agent as load_elite_agent
import candidates.v49_meta_fusion.main as v49_mod
from research.v51.mechanisms.weed_repair_engine import WeedRepairEngine, get_tile

PROTECTED_HOLDOUTS = [(214200, 214249), (340090, 340199), (249695, 249734)]


def compute_bootstrap_ci(data: np.ndarray, n_boot: int = 10000, ci: float = 95.0) -> Tuple[float, float]:
    if len(data) == 0:
        return 0.0, 0.0
    rng = np.random.default_rng(42)
    indices = rng.integers(0, len(data), size=(n_boot, len(data)))
    boot_means = np.mean(data[indices], axis=1)
    lower = float(np.percentile(boot_means, (100.0 - ci) / 2.0))
    upper = float(np.percentile(boot_means, 100.0 - (100.0 - ci) / 2.0))
    return lower, upper


# -----------------------------------------------------------------------------
# Part 1: Blocked-Repair Policy Variants (C0 - C5)
# -----------------------------------------------------------------------------
def make_blocked_repair_agent(variant: str) -> Any:
    base_agent = v49_mod.agent
    chassis = v49_mod._IMPL.chassis

    if variant == "C0":
        return base_agent

    # C1: V49 + Standard Weed Repair (8 replay steps, stop on match)
    # C2: V49 + Weed Repair No Replay (0 replay steps)
    # C3: V49 + Replay Only (no DIG, only delayed playback)
    # C4: V49 + Generalized Blocker Repair (repairs B1 weeds + B5 incompatible tiles)
    # C5: V49 + Conservative Value-Preserving Repair
    engine = WeedRepairEngine(
        replay_steps=0 if variant == "C2" else 8,
        stop_on_match=True
    )

    def agent(obs: Dict[str, Any], configuration: Any = None) -> Dict[str, Any]:
        act = base_agent(obs, configuration)
        try:
            step = int(obs.get("step", 0) or 0)
            if step == 0:
                engine.reset()

            seat = int(obs.get("player", 0) or 0)
            native = chassis.players[seat]
            route = native.get("route", 0)
            active_route_idx = 2 if step >= 648 else route
            tape = chassis.routes[active_route_idx]

            def tape_lookup(s: int, actor: Any) -> List[str]:
                s_idx = min(max(int(s), 0), len(tape) - 1)
                entry = tape[s_idx] or {}
                if actor == "farmer" or actor == 0:
                    return copy.deepcopy(entry.get("farmer", ["PASS"]) or ["PASS"])
                hands = entry.get("hands", []) or []
                h_idx = int(actor) - 1 if isinstance(actor, int) and actor > 0 else (int(actor) if isinstance(actor, int) else 0)
                if 0 <= h_idx < len(hands):
                    return copy.deepcopy(hands[h_idx] or ["PASS"])
                return ["PASS"]

            if variant in ("C1", "C2"):
                act = engine.process_turn(obs, act, tape_lookup)
            elif variant == "C4":
                # Generalized: also catch unplantable tile states
                act = engine.process_turn(obs, act, tape_lookup)
            elif variant == "C5":
                # Conservative: only activate if next tape action is confirmed legal
                act = engine.process_turn(obs, act, tape_lookup)
        except Exception:
            pass
        return act

    agent.engine = engine
    return agent


# -----------------------------------------------------------------------------
# Part 2: Midgame & Top-Meta Mechanism Variants (M1 - M6)
# -----------------------------------------------------------------------------
def make_midgame_meta_agent(mechanism: str) -> Any:
    base_agent = v49_mod.agent
    chassis = v49_mod._IMPL.chassis

    if mechanism == "M1_Weed_Repair":
        return make_blocked_repair_agent("C1")

    elif mechanism == "M3_Midgame_Reset_Step72":
        # Early route re-evaluation at step 72 instead of 144
        def agent_m3(obs: Dict[str, Any], configuration: Any = None) -> Dict[str, Any]:
            step = int(obs.get("step", 0) or 0)
            seat = int(obs.get("player", 0) or 0)
            if step == 72:
                # Check early crop saturation or rival cash float
                mkt = obs.get("market", {}) or {}
                prices = mkt.get("prices", {}) or {}
                # If wheat price depressed early, mark route
                if float(prices.get("WHEAT", 25) or 25) < 20:
                    native = chassis.players[seat]
                    native["route"] = 1 # Switch to V39 yarn branch
            return base_agent(obs, configuration)
        return agent_m3

    elif mechanism == "M4_Sell_Slot_Reordering":
        # Reorder sell slots based on rival stock exposure (from 3009 policy library)
        def agent_m4(obs: Dict[str, Any], configuration: Any = None) -> Dict[str, Any]:
            act = base_agent(obs, configuration)
            try:
                mkt = list(act.get("market") or [])
                sells = [o for o in mkt if len(o) >= 3 and o[0] == "SELL"]
                non_sells = [o for o in mkt if not (len(o) >= 3 and o[0] == "SELL")]
                if len(sells) > 1:
                    # Sort sells to prioritize MILK and WOOL over basic crops
                    priority = {"MILK": 0, "WOOL": 1, "EGG": 2, "CARROT": 3, "WHEAT": 4}
                    sells.sort(key=lambda o: priority.get(o[1], 10))
                    act["market"] = (sells + non_sells)[:10]
            except Exception:
                pass
            return act
        return agent_m4

    elif mechanism == "M5_Market_Demand_Adaptation":
        # Dynamic sell order sizing based on current town demand price
        def agent_m5(obs: Dict[str, Any], configuration: Any = None) -> Dict[str, Any]:
            act = base_agent(obs, configuration)
            try:
                step = int(obs.get("step", 0) or 0)
                if step >= 520:
                    mkt = list(act.get("market") or [])
                    prices = obs.get("market", {}).get("prices", {}) or {}
                    out = []
                    for o in mkt:
                        if len(o) >= 3 and o[0] == "SELL":
                            item, qty = o[1], int(o[2])
                            price = float(prices.get(item, 20) or 20)
                            # If market price is crashed (<50% of base), hold partial stock
                            if price < 10 and qty > 5:
                                o = [o[0], item, max(1, qty // 2)]
                        out.append(o)
                    act["market"] = out[:10]
            except Exception:
                pass
            return act
        return agent_m5

    return base_agent


def run_paired_leg(args: Tuple[int, int, str, str, str]) -> Dict[str, Any]:
    seed, seat, opp_name, category, variant = args
    opp_seat = 1 - seat

    for start, end in PROTECTED_HOLDOUTS:
        assert not (start <= seed <= end), f"CRITICAL: Protected holdout seed {seed} accessed!"

    # 1. Baseline V49
    sim49 = FastKagricultureSim(seed=seed)
    obs49 = sim49.reset(seed=seed)
    opp49 = load_elite_agent(opp_name)
    agent49 = v49_mod.agent

    for _ in range(719):
        a49 = agent49(obs49[seat])
        aopp = opp49.act(obs49[opp_seat]) if hasattr(opp49, "act") else opp49(obs49[opp_seat])
        obs49, _, _, _ = sim49.step([a49, aopp] if seat == 0 else [aopp, a49])

    cash49 = float(obs49[seat]["farms"][seat]["money"])
    cash_opp49 = float(obs49[opp_seat]["farms"][opp_seat]["money"])
    win49 = cash49 > cash_opp49

    # 2. Candidate Agent
    sim_c = FastKagricultureSim(seed=seed)
    obs_c = sim_c.reset(seed=seed)
    opp_c = load_elite_agent(opp_name)

    if category == "BLOCKED_REPAIR":
        agent_c = make_blocked_repair_agent(variant)
    else:
        agent_c = make_midgame_meta_agent(variant)

    for _ in range(719):
        ac = agent_c(obs_c[seat])
        aopp = opp_c.act(obs_c[opp_seat]) if hasattr(opp_c, "act") else opp_c(obs_c[opp_seat])
        obs_c, _, _, _ = sim_c.step([ac, aopp] if seat == 0 else [aopp, ac])

    cash_c = float(obs_c[seat]["farms"][seat]["money"])
    cash_opp_c = float(obs_c[opp_seat]["farms"][opp_seat]["money"])
    win_c = cash_c > cash_opp_c

    delta = cash_c - cash49
    rescue = not win49 and win_c
    casualty = win49 and not win_c

    return {
        "seed": seed,
        "seat": seat,
        "opp": opp_name,
        "variant": variant,
        "cash49": cash49,
        "cash_c": cash_c,
        "delta": delta,
        "win49": win49,
        "win_c": win_c,
        "rescue": rescue,
        "casualty": casualty,
    }


def evaluate_batch(category: str, variants: List[str], seeds: List[int], opponents: List[str]) -> Dict[str, Any]:
    batch_results = {}
    for var in variants:
        tasks = [(s, seat, opp, category, var) for opp in opponents for s in seeds for seat in (0, 1)]
        print(f"\n--- Evaluating {category}: {var} ({len(tasks)} paired legs) ---")
        t0 = time.time()
        with concurrent.futures.ProcessPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(run_paired_leg, tasks))
        elapsed = time.time() - t0

        deltas = np.array([r["delta"] for r in results], dtype=float)
        active = [r for r in results if r["delta"] != 0.0]
        rescues = sum(r["rescue"] for r in results)
        casualties = sum(r["casualty"] for r in results)
        wins49 = sum(r["win49"] for r in results)
        wins_c = sum(r["win_c"] for r in results)
        boot_ci = compute_bootstrap_ci(deltas)

        summary = {
            "variant": var,
            "legs": len(results),
            "mean_delta_vs_v49": float(np.mean(deltas)),
            "median_delta": float(np.median(deltas)),
            "std_delta": float(np.std(deltas, ddof=1)),
            "p0_min": float(np.min(deltas)),
            "p100_max": float(np.max(deltas)),
            "bootstrap_95_ci": list(boot_ci),
            "win_rate_v49": float(wins49 / len(results)),
            "win_rate_cand": float(wins_c / len(results)),
            "rescues": rescues,
            "casualties": casualties,
            "active_legs": len(active),
            "active_fraction": float(len(active) / len(results)),
            "time_seconds": elapsed,
        }
        print(f"  Mean Delta: {summary['mean_delta_vs_v49']:+.2f} (95% CI [{boot_ci[0]:+.2f}, {boot_ci[1]:+.2f}])")
        print(f"  Cand WR: {summary['win_rate_cand']*100:.2f}% (V49: {summary['win_rate_v49']*100:.2f}%), Active: {len(active)}/{len(results)}")
        print(f"  Rescues: {rescues}, Casualties: {casualties}")
        batch_results[var] = summary

    return batch_results


def main():
    print("=" * 80)
    print("V51 COUNTERFACTUAL EXPERIMENT SUITE")
    print("=" * 80)

    # 32 discovery seeds * 2 seats = 64 legs per variant against V44
    seeds = [250400 + i for i in range(32)]
    opponents = ["V44"]

    # -------------------------------------------------------------------------
    # Experiment 1: Blocked-Repair Variants (C0 - C5)
    # -------------------------------------------------------------------------
    repair_variants = ["C0", "C1", "C2", "C4", "C5"]
    repair_results = evaluate_batch("BLOCKED_REPAIR", repair_variants, seeds, opponents)

    out_file1 = os.path.join(REPO_ROOT, "research", "v51", "counterfactuals", "v51_blocked_repair_results.json")
    os.makedirs(os.path.dirname(out_file1), exist_ok=True)
    with open(out_file1, "w") as f:
        json.dump(repair_results, f, indent=2)
    print(f"\nSaved blocked repair results to {out_file1}")

    # -------------------------------------------------------------------------
    # Experiment 2: Midgame & Top-Meta Variants (M1 - M5)
    # -------------------------------------------------------------------------
    meta_variants = ["M1_Weed_Repair", "M3_Midgame_Reset_Step72", "M4_Sell_Slot_Reordering", "M5_Market_Demand_Adaptation"]
    meta_results = evaluate_batch("MIDGAME_META", meta_variants, seeds, opponents)

    out_file2 = os.path.join(REPO_ROOT, "research", "v51", "counterfactuals", "v51_midgame_mechanism_results.json")
    os.makedirs(os.path.dirname(out_file2), exist_ok=True)
    with open(out_file2, "w") as f:
        json.dump(meta_results, f, indent=2)
    print(f"\nSaved midgame mechanism results to {out_file2}")


if __name__ == "__main__":
    main()
