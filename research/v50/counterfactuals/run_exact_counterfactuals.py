#!/usr/bin/env python3
"""Exact Full-Terminal Counterfactual Engine for V50 Dead-Action Mechanisms.

Evaluates paired counterfactual performance of candidate dead-action mechanisms
against V49 Meta Fusion on identical worlds.

Guaranteed properties:
- Full step-719 terminal authority (no truncated rollouts).
- Paired match-level delta (V50_cand cash - V49 cash).
- Exact casualty detection (V49 won, V50_cand lost).
- Exact rescue detection (V49 lost, V50_cand won).
- 10,000-sample bootstrap confidence intervals.
"""

import concurrent.futures
import copy
import json
import os
import sys
import time
from typing import Any, Callable, Dict, List, Tuple
import numpy as np

sys.stdout.reconfigure(line_buffering=True)

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from research.v47.elite_benchmark.run_elite_benchmark import load_agent as load_elite_agent
import candidates.v48_challenger.main as v48_mod
import candidates.v49_meta_fusion.main as v49_mod

PROTECTED_HOLDOUTS = [(214200, 214249), (340090, 340199), (249695, 249734)]

CROP_LATENCY = {
    "WHEAT": 2,
    "CARROT": 2,
    "TOMATO": 8,
    "STRAWBERRY": 10,
    "MELON": 10,
}

# Cache for future planting demand
_FUTURE_PLANT_CACHE: Dict[Tuple[int, int, str], int] = {}
_FUTURE_FERT_CACHE: Dict[Tuple[int, int], int] = {}


def get_remaining_actionable_plants(native: Dict[str, Any], step: int, chassis: Any, crop: str) -> int:
    route = native.get("route", 0)
    key = (route, step, crop)
    if key in _FUTURE_PLANT_CACHE:
        return _FUTURE_PLANT_CACHE[key]

    latency = CROP_LATENCY.get(crop, 2)
    need = 0
    for t in range(step + 1, 719):
        # A plant action at turn t can only mature if day + latency <= 29
        if (t // 24) + latency > 29:
            continue
        tape = chassis.routes[2 if t >= 648 else route]
        act = tape[t]
        units = [act.get("farmer") or ["PASS"]] + list(act.get("hands") or [])
        need += sum(1 for c in units if len(c) > 1 and c[0] == "PLANT" and c[1] == crop)

    _FUTURE_PLANT_CACHE[key] = need
    return need


def get_remaining_fertilize_demands(native: Dict[str, Any], step: int, chassis: Any) -> int:
    route = native.get("route", 0)
    key = (route, step)
    if key in _FUTURE_FERT_CACHE:
        return _FUTURE_FERT_CACHE[key]

    need = 0
    for t in range(step + 1, 719):
        tape = chassis.routes[2 if t >= 648 else route]
        act = tape[t]
        units = [act.get("farmer") or ["PASS"]] + list(act.get("hands") or [])
        need += sum(1 for c in units if len(c) > 0 and c[0] == "FERTILIZE")

    _FUTURE_FERT_CACHE[key] = need
    return need


# ---------------------------------------------------------------------------
# Mechanism Factory: builds policy overlays on top of V48 baseline
# ---------------------------------------------------------------------------
def make_candidate_agent(config: Dict[str, Any]) -> Callable:
    seed_thresh = config.get("seed_step_threshold", 624)
    fert_thresh = config.get("fert_step_threshold", 646)
    enable_fert_guard = config.get("enable_fert_guard", False)
    enable_extended_seeds = config.get("enable_extended_seeds", False)
    enable_post670_blackout = config.get("enable_post670_blackout", False)
    enable_market_wheat_guard = config.get("enable_market_wheat_guard", False)

    base_agent = v49_mod.agent
    chassis = v49_mod._IMPL.chassis

    def agent(obs: Dict[str, Any], configuration: Any = None) -> Dict[str, Any]:
        act = base_agent(obs, configuration)
        try:
            step = int(obs.get("step", 0) or 0)
            if step == 0:
                _FUTURE_PLANT_CACHE.clear()
                _FUTURE_FERT_CACHE.clear()

            if not isinstance(act, dict):
                return act

            mkt = list(act.get("market") or [])
            if not mkt:
                return act

            seat = int(obs["player"])
            native = chassis.players[seat]
            units = [act.get("farmer") or ["PASS"]] + list(act.get("hands") or [])
            changed = False
            out_mkt = []

            # Seeds inventory
            seeds_inv = obs.get("private", {}).get("seeds", {}) or {}
            avail_seeds = {}
            for crop in ("WHEAT", "CARROT", "MELON", "TOMATO", "STRAWBERRY"):
                avail_seeds[crop] = max(0, int(seeds_inv.get(crop, 0)) - sum(c[:2] == ["PLANT", crop] for c in units))

            # Shed inventory (Fertilizer, Products)
            shed = obs.get("private", {}).get("shed", {}) or {}
            avail_fert = int(shed.get("FERTILIZER", 0))


            for o in mkt:
                if not (isinstance(o, list) and len(o) >= 3):
                    out_mkt.append(o)
                    continue

                op = o[0]
                item = o[1]
                qty = max(0, int(o[2]))

                # 1. POST-670 UNIVERSAL SEED BLACKOUT
                if enable_post670_blackout and op == "BUY_SEED" and step >= 670:
                    changed = True
                    o = []

                # 2. EXTENDED NON-WHEAT/CARROT SEED GUARD (Tomato, Strawberry, Melon)
                elif enable_extended_seeds and op == "BUY_SEED" and item in ("MELON", "TOMATO", "STRAWBERRY") and step >= seed_thresh:
                    rem_plant = get_remaining_actionable_plants(native, step, chassis, item)
                    rem_plant += sum(1 for queue in native.get("pending", {}).values() for pos, c in queue
                                    if len(c) > 1 and c[0] == "PLANT" and c[1] == item)
                    keep = min(qty, max(0, rem_plant - avail_seeds.get(item, 0)))
                    avail_seeds[item] = avail_seeds.get(item, 0) + keep
                    if keep < qty:
                        changed = True
                        o = [op, item, keep] if keep > 0 else []

                # 3. DEAD FERTILIZER GUARD
                elif enable_fert_guard and op == "BUY_PRODUCT" and item == "FERTILIZER" and step >= fert_thresh:
                    rem_fert = get_remaining_fertilize_demands(native, step, chassis)
                    rem_fert += sum(1 for queue in native.get("pending", {}).values() for pos, c in queue
                                   if len(c) > 0 and c[0] == "FERTILIZE")
                    keep = min(qty, max(0, rem_fert - avail_fert))
                    avail_fert += keep
                    if keep < qty:
                        changed = True
                        o = [op, item, keep] if keep > 0 else []

                # 4. LATE WHEAT BUY GUARD (if buying wheat but shed already has ample stock)
                elif enable_market_wheat_guard and op == "BUY_PRODUCT" and item == "WHEAT" and step >= 648:
                    wheat_stock = int(shed.get("WHEAT", 0))
                    if wheat_stock >= 10:
                        changed = True
                        o = []


                if o:
                    out_mkt.append(o)

            if changed:
                act = dict(act)
                act["market"] = [x for x in out_mkt if x][:10]
                agent.activations += 1
                if agent.div_step is None:
                    agent.div_step = step
        except Exception:
            pass
        return act

    agent.activations = 0
    agent.div_step = None
    return agent


def run_paired_counterfactual(args: Tuple[int, int, str, Dict[str, Any]]) -> Dict[str, Any]:
    seed, seat, opp_name, mech_cfg = args
    opp_seat = 1 - seat

    # 1. Baseline V49 vs Opponent
    sim_v49 = FastKagricultureSim(seed=seed)
    obs_v49 = sim_v49.reset(seed=seed)
    opp_v49 = load_elite_agent(opp_name)
    agent_v49 = v49_mod.agent

    for _ in range(719):
        a_v49 = agent_v49(obs_v49[seat])
        a_opp = opp_v49.act(obs_v49[opp_seat]) if hasattr(opp_v49, "act") else opp_v49(obs_v49[opp_seat])
        actions = [a_v49, a_opp] if seat == 0 else [a_opp, a_v49]
        obs_v49, _, _, _ = sim_v49.step(actions)

    cash_v49 = float(obs_v49[seat]["farms"][seat]["money"])
    cash_opp_v49 = float(obs_v49[opp_seat]["farms"][opp_seat]["money"])
    win_v49 = cash_v49 > cash_opp_v49

    # 2. Candidate V50 vs Opponent
    sim_cand = FastKagricultureSim(seed=seed)
    obs_cand = sim_cand.reset(seed=seed)
    opp_cand = load_elite_agent(opp_name)
    agent_cand = make_candidate_agent(mech_cfg)

    for step in range(719):
        a_cand = agent_cand(obs_cand[seat])
        a_opp = opp_cand.act(obs_cand[opp_seat]) if hasattr(opp_cand, "act") else opp_cand(obs_cand[opp_seat])
        actions = [a_cand, a_opp] if seat == 0 else [a_opp, a_cand]
        obs_cand, _, _, _ = sim_cand.step(actions)

    cash_cand = float(obs_cand[seat]["farms"][seat]["money"])
    cash_opp_cand = float(obs_cand[opp_seat]["farms"][opp_seat]["money"])
    win_cand = cash_cand > cash_opp_cand

    delta = cash_cand - cash_v49
    rescue = not win_v49 and win_cand
    casualty = win_v49 and not win_cand

    return {
        "seed": seed,
        "seat": seat,
        "opp": opp_name,
        "cash_v49": cash_v49,
        "cash_cand": cash_cand,
        "delta": delta,
        "win_v49": win_v49,
        "win_cand": win_cand,
        "rescue": rescue,
        "casualty": casualty,
        "div_step": agent_cand.div_step,
        "activations": agent_cand.activations,
    }


def compute_bootstrap_ci(data: np.ndarray, n_boot: int = 10000, ci: float = 95.0) -> Tuple[float, float]:
    rng = np.random.default_rng(42)
    indices = rng.integers(0, len(data), size=(n_boot, len(data)))
    boot_means = np.mean(data[indices], axis=1)
    lower = float(np.percentile(boot_means, (100.0 - ci) / 2.0))
    upper = float(np.percentile(boot_means, 100.0 - (100.0 - ci) / 2.0))
    return lower, upper


def evaluate_mechanism(name: str, mech_cfg: Dict[str, Any], seeds: List[int], opp_names: List[str]) -> Dict[str, Any]:
    tasks = [(s, seat, opp, mech_cfg) for opp in opp_names for s in seeds for seat in (0, 1)]
    print(f"\n--- Evaluating {name} ({len(tasks)} paired legs against V49) ---")
    t0 = time.time()

    with concurrent.futures.ProcessPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(run_paired_counterfactual, tasks))

    deltas = np.array([r["delta"] for r in results], dtype=float)
    active = [r for r in results if r["delta"] != 0.0]
    rescues = sum(r["rescue"] for r in results)
    casualties = sum(r["casualty"] for r in results)
    wins_v49 = sum(r["win_v49"] for r in results)
    wins_cand = sum(r["win_cand"] for r in results)

    boot_ci = compute_bootstrap_ci(deltas, n_boot=10000)

    summary = {
        "mechanism": name,
        "config": mech_cfg,
        "legs": len(results),
        "mean_delta_vs_v49": float(np.mean(deltas)),
        "median_delta": float(np.median(deltas)),
        "std_delta": float(np.std(deltas, ddof=1)),
        "sem_delta": float(np.std(deltas, ddof=1) / np.sqrt(len(deltas))),
        "p0_min": float(np.min(deltas)),
        "p10": float(np.percentile(deltas, 10.0)),
        "p25": float(np.percentile(deltas, 25.0)),
        "p75": float(np.percentile(deltas, 75.0)),
        "p90": float(np.percentile(deltas, 90.0)),
        "p100_max": float(np.max(deltas)),
        "bootstrap_mean_95_ci": list(boot_ci),
        "win_rate_v49": float(wins_v49 / len(results)),
        "win_rate_cand": float(wins_cand / len(results)),
        "rescues": rescues,
        "casualties": casualties,
        "active_legs": len(active),
        "active_fraction": float(len(active) / len(results)),
        "active_mean": float(np.mean([r["delta"] for r in active])) if active else 0.0,
        "active_median": float(np.median([r["delta"] for r in active])) if active else 0.0,
        "time_seconds": float(time.time() - t0),
    }

    print(f"  Mean Delta vs V49: {summary['mean_delta_vs_v49']:+.2f} (95% CI [{boot_ci[0]:+.2f}, {boot_ci[1]:+.2f}]), Median: {summary['median_delta']:+.2f}")
    print(f"  Active Legs: {summary['active_legs']} / {len(results)} ({summary['active_fraction']*100:.1f}%), Active Mean: {summary['active_mean']:+.2f}")
    print(f"  Rescues: {rescues}, Casualties: {casualties}")
    print(f"  Candidate Win Rate: {summary['win_rate_cand']*100:.2f}% (V49: {summary['win_rate_v49']*100:.2f}%)")
    print(f"  Downside Tail: P10={summary['p10']:.2f}, Min={summary['p0_min']:.2f}")

    return summary


def main():
    # Test on the primary incumbent V44 across 64 seeds (128 legs) for discovery screening
    discovery_seeds = [250400 + i for i in range(32)]
    for s in discovery_seeds:
        for start, end in PROTECTED_HOLDOUTS:
            assert not (start <= s <= end), f"CRITICAL: Protected holdout seed {s} accessed!"


    opponents = ["V44"]

    print("=" * 80)
    print("V50 EXACT FULL-TERMINAL COUNTERFACTUAL ENGINE")
    print("=" * 80)

    mechanisms_to_test = [
        # Baseline check: Exact V49 configuration (must have delta = 0 everywhere)
        ("V49_Parity_Check", {}),
        # M1: Extended Seed Guard (Cap Tomato, Strawberry, Melon)
        ("M1_Extended_Seeds_624", {
            "enable_extended_seeds": True,
            "seed_step_threshold": 624,
        }),
        # M2: Late Fertilizer Guard at step 646
        ("M2_Late_Fert_Guard_646", {
            "enable_fert_guard": True,
            "fert_step_threshold": 646,
        }),
        # M2 Threshold sweep: Fert Guard at 624
        ("M2_Late_Fert_Guard_624", {
            "enable_fert_guard": True,
            "fert_step_threshold": 624,
        }),
        # M2 Threshold sweep: Fert Guard at 631
        ("M2_Late_Fert_Guard_631", {
            "enable_fert_guard": True,
            "fert_step_threshold": 631,
        }),
        # M3: Post-670 Universal Seed Blackout
        ("M3_Post670_Seed_Blackout", {
            "enable_post670_blackout": True,
        }),
        # M4: Market Wheat Buy Guard
        ("M4_Market_Wheat_Guard_648", {
            "enable_market_wheat_guard": True,
        }),
        # Composite: M1 + M2 (646) + M3
        ("Composite_M1_M2_M3", {
            "enable_fert_guard": True,
            "fert_step_threshold": 646,
            "enable_extended_seeds": True,
            "seed_step_threshold": 624,
            "enable_post670_blackout": True,
        }),
    ]

    all_summaries = {}
    for name, cfg in mechanisms_to_test:
        summary = evaluate_mechanism(name, cfg, discovery_seeds, opponents)
        all_summaries[name] = summary

    out_file = os.path.join(REPO_ROOT, "research", "v50", "counterfactuals", "full_terminal_results.json")
    with open(out_file, "w") as f:
        json.dump(all_summaries, f, indent=2)
    print(f"\nAll counterfactual summaries saved to {out_file}!")


if __name__ == "__main__":
    main()
