#!/usr/bin/env python3
"""Fresh Validation Benchmark for V52 (Section 15).

Evaluates V49 baseline and candidate counterfactual variants on 32 strictly disjoint fresh seeds [250600..250631]
across 9 opponents (6 elite + 3 adversarial) over 576 legs per candidate.
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

PROTECTED_HOLDOUTS = [(214200, 214249), (340090, 340199), (249695, 249734)]
FRESH_SEEDS = [250600 + i for i in range(32)]  # 32 seeds * 2 seats * 9 opponents = 576 legs

for s in FRESH_SEEDS:
    for start, end in PROTECTED_HOLDOUTS:
        assert not (start <= s <= end), f"CRITICAL: Protected holdout seed {s} accessed!"
    assert not (250400 <= s <= 250527), f"CRITICAL: Discovery seed {s} accessed in fresh evaluation!"


def compute_bootstrap_ci(data: np.ndarray, n_boot: int = 10000, ci: float = 95.0) -> Tuple[float, float]:
    if len(data) == 0:
        return 0.0, 0.0
    rng = np.random.default_rng(42)
    indices = rng.integers(0, len(data), size=(n_boot, len(data)))
    boot_means = np.mean(data[indices], axis=1)
    lower = float(np.percentile(boot_means, (100.0 - ci) / 2.0))
    upper = float(np.percentile(boot_means, 100.0 - (100.0 - ci) / 2.0))
    return lower, upper


def make_adversary(strategy: str) -> Any:
    def _adv(obs, cfg=None):
        step = int(obs.get("step", 0))
        seat = int(obs.get("player", 0))
        farm = obs["farms"][seat]
        shed = farm.get("shed", {}) or {}
        hands = farm.get("hands", []) or []
        mkt = []

        if strategy == "DAIRY_FLOOD":
            milk = shed.get("MILK", 0)
            if milk > 0:
                mkt.append(["SELL", "MILK", milk])
            if step < 240 and farm.get("money", 0) >= 400:
                mkt.append(["BUY_ANIMAL", "COW", 1])

        elif strategy == "WOOL_FLOOD":
            wool = shed.get("WOOL", 0)
            if wool > 0:
                mkt.append(["SELL", "WOOL", wool])
            if step < 240 and farm.get("money", 0) >= 500:
                mkt.append(["BUY_ANIMAL", "SHEEP", 1])

        elif strategy == "TERMINAL_DUMPER":
            if step >= 680:
                for item in ("MILK", "WOOL", "WHEAT", "CARROT", "EGG"):
                    qty = shed.get(item, 0)
                    if qty > 0 and len(mkt) < 10:
                        mkt.append(["SELL", item, qty])

        return {
            "farmer": ["PASS"],
            "hands": [["PASS"] for _ in hands],
            "market": mkt[:10],
        }

    return _adv


def load_any_agent(opp_name: str) -> Any:
    if opp_name in ("DAIRY_FLOOD", "WOOL_FLOOD", "TERMINAL_DUMPER"):
        return make_adversary(opp_name)
    return load_elite_agent(opp_name)


def make_candidate_agent(candidate_key: str):
    def _agent(obs, cfg=None):
        step = int(obs.get("step", 0) or 0)
        orig_options = v49_mod._CS_OPTIONS

        if candidate_key == "V52_COWSWAP_Suppression":
            # Suppress COWSWAP
            v49_mod._CS_OPTIONS = ()
        else:
            v49_mod._CS_OPTIONS = orig_options

        act = v49_mod.agent(obs, cfg)
        v49_mod._CS_OPTIONS = orig_options

        if not isinstance(act, dict):
            return act

        if candidate_key == "V52_Barn_Priority" and 518 <= step <= 524:
            units = [act.get("farmer") or ["PASS"]] + list(act.get("hands") or [])
            act = dict(act)
            act["farmer"] = units[0]
            act["hands"] = units[1:]

        return act

    return _agent


def run_single_simulation(seed: int, seat: int, opp_name: str, candidate_key: str) -> Tuple[float, float, bool]:
    opp_seat = 1 - seat
    sim = FastKagricultureSim(seed=seed)
    obs = sim.reset(seed=seed)
    
    agent = make_candidate_agent(candidate_key)
    opp = load_any_agent(opp_name)

    shadow = 1400.0 if candidate_key == "V52_Liquidity_Float" else 0.0

    for step in range(719):
        if step == 1 and shadow > 0.0:
            sim.state[0].observation["farms"][seat]["money"] += shadow

        a_cand = agent(obs[seat])
        a_opp = opp.act(obs[opp_seat]) if hasattr(opp, "act") else opp(obs[opp_seat])
        obs, _, _, _ = sim.step([a_cand, a_opp] if seat == 0 else [a_opp, a_cand])

    c_cand = float(obs[seat]["farms"][seat]["money"]) - shadow
    c_opp = float(obs[opp_seat]["farms"][opp_seat]["money"])
    win = c_cand > c_opp
    return c_cand, c_opp, win


def run_baseline_and_candidate_leg(task: Tuple[int, int, str, str]) -> Dict[str, Any]:
    seed, seat, opp_name, candidate_key = task
    
    # 1. Baseline V49
    cash49, cash_opp49, win49 = run_single_simulation(seed, seat, opp_name, "V49_Meta_Fusion")
    
    # 2. Candidate
    if candidate_key == "V49_Meta_Fusion":
        cash_c, cash_opp_c, win_c = cash49, cash_opp49, win49
    else:
        cash_c, cash_opp_c, win_c = run_single_simulation(seed, seat, opp_name, candidate_key)

    delta = cash_c - cash49
    rescue = (not win49) and win_c
    casualty = win49 and (not win_c)

    return {
        "seed": seed,
        "seat": seat,
        "opp": opp_name,
        "candidate": candidate_key,
        "cash49": cash49,
        "cash_c": cash_c,
        "delta": delta,
        "win49": win49,
        "win_c": win_c,
        "rescue": rescue,
        "casualty": casualty,
    }


def compute_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not results:
        return {}
    deltas = np.array([r["delta"] for r in results], dtype=float)
    active = [r for r in results if r["delta"] != 0.0]
    rescues = sum(r["rescue"] for r in results)
    casualties = sum(r["casualty"] for r in results)
    wins49 = sum(r["win49"] for r in results)
    wins_c = sum(r["win_c"] for r in results)
    boot_ci = compute_bootstrap_ci(deltas)

    return {
        "legs": len(results),
        "mean_delta_vs_v49": float(np.mean(deltas)),
        "median_delta": float(np.median(deltas)),
        "bootstrap_95_ci": list(boot_ci),
        "win_rate_v49": float(wins49 / len(results)),
        "win_rate_cand": float(wins_c / len(results)),
        "rescues": rescues,
        "casualties": casualties,
        "active_legs": len(active),
        "active_fraction": float(len(active) / len(results)),
    }


def evaluate_candidate(candidate_key: str, elite_opponents: List[str], adversarial_opponents: List[str]) -> Dict[str, Any]:
    all_opponents = elite_opponents + adversarial_opponents
    tasks = [(s, seat, opp, candidate_key) for opp in all_opponents for s in FRESH_SEEDS for seat in (0, 1)]
    print(f"\n--- Running Fresh Evaluation: {candidate_key} ({len(tasks)} legs across 9 opponents) ---")
    t0 = time.time()

    with concurrent.futures.ProcessPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(run_baseline_and_candidate_leg, tasks))
    elapsed = time.time() - t0

    overall = compute_metrics(results)
    elite_metrics = compute_metrics([r for r in results if r["opp"] in elite_opponents])
    adv_metrics = compute_metrics([r for r in results if r["opp"] in adversarial_opponents])

    per_opp = {}
    for opp in all_opponents:
        per_opp[opp] = compute_metrics([r for r in results if r["opp"] == opp])

    summary = {
        "candidate": candidate_key,
        "time_seconds": elapsed,
        "overall": overall,
        "elite_suite": elite_metrics,
        "adversarial_suite": adv_metrics,
        "per_opponent": per_opp,
    }

    print(f"  Overall Mean Delta vs V49: {overall['mean_delta_vs_v49']:+.2f} (95% CI [{overall['bootstrap_95_ci'][0]:+.2f}, {overall['bootstrap_95_ci'][1]:+.2f}])")
    print(f"  Overall WR: V49 {overall['win_rate_v49']*100:.2f}% | Cand {overall['win_rate_cand']*100:.2f}% (Rescues: {overall['rescues']}, Casualties: {overall['casualties']})")
    print(f"  Elite Delta: {elite_metrics['mean_delta_vs_v49']:+.2f}, Cand WR: {elite_metrics['win_rate_cand']*100:.2f}%")
    print(f"  Adv Delta: {adv_metrics['mean_delta_vs_v49']:+.2f}, Cand WR: {adv_metrics['win_rate_cand']*100:.2f}%")
    return summary


def main():
    print("=" * 80)
    print("V52 FRESH OUT-OF-SAMPLE LADDER BENCHMARK (SECTION 15)")
    print("=" * 80)

    elite_opponents = [
        "V44",
        "dmitrii_lb2800",
        "tetsutani_pasture",
        "kaitofukami_v48_3009",
        "indarkarhana_top10",
        "saiteja_mega_3000",
    ]

    adversarial_opponents = [
        "DAIRY_FLOOD",
        "WOOL_FLOOD",
        "TERMINAL_DUMPER",
    ]

    ladder = {}

    # 1. Baseline Reference: V49 Meta Fusion
    ladder["V49_Meta_Fusion"] = evaluate_candidate("V49_Meta_Fusion", elite_opponents, adversarial_opponents)

    # 2. V52 COWSWAP Suppression (Herd Patch)
    ladder["V52_COWSWAP_Suppression"] = evaluate_candidate("V52_COWSWAP_Suppression", elite_opponents, adversarial_opponents)

    # 3. V52 Liquidity Float (+$1,400 shadow float)
    ladder["V52_Liquidity_Float"] = evaluate_candidate("V52_Liquidity_Float", elite_opponents, adversarial_opponents)

    # 4. V52 Barn Priority (Barn entrance coordination)
    ladder["V52_Barn_Priority"] = evaluate_candidate("V52_Barn_Priority", elite_opponents, adversarial_opponents)

    out_file = os.path.join(REPO_ROOT, "research", "v52", "benchmarks", "v52_fresh_ladder.json")
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w") as f:
        json.dump(ladder, f, indent=2)
    print(f"\nSaved fresh validation ladder to {out_file}!")


if __name__ == "__main__":
    main()
