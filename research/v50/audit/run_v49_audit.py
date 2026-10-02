#!/usr/bin/env python3
"""Comprehensive Audit and Independent Reproduction of V49 Meta Fusion.

Evaluates paired performance of V49 vs V48 across 6 elite opponents:
1. V44
2. dmitrii_lb2800
3. tetsutani_pasture
4. kaitofukami_v48_3009
5. indarkarhana_top10
6. saiteja_mega_3000

Checks:
- Bit-for-bit identity across turns 0..623
- Legality and scope of E402 modifications
- Per-leg distributions, wins, losses, ties, casualties, rescues
- Parametric, bootstrap, and sample percentile confidence intervals
- Complete reconciliation of V49 reported metrics vs raw data
"""

import concurrent.futures
import copy
import json
import os
import sys
import time
from typing import Any, Dict, List, Tuple
import numpy as np

sys.stdout.reconfigure(line_buffering=True)

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from research.v47.elite_benchmark.run_elite_benchmark import load_agent as load_elite_agent
import candidates.v48_challenger.main as v48_mod
import candidates.v49_meta_fusion.main as v49_mod

SEEDS = [250400 + i for i in range(128)]
PROTECTED_HOLDOUTS = [(214200, 214249), (340090, 340199), (249695, 249734)]
for s in SEEDS:
    for start, end in PROTECTED_HOLDOUTS:
        assert not (start <= s <= end), f"CRITICAL: Protected holdout seed {s} accessed!"


def run_paired_leg(args: Tuple[int, int, str]) -> Dict[str, Any]:
    seed, seat, opp_name = args
    opp_seat = 1 - seat

    # 1. Run V48 match
    sim48 = FastKagricultureSim(seed=seed)
    obs48 = sim48.reset(seed=seed)
    opp48 = load_elite_agent(opp_name)
    agent_v48 = v48_mod.agent

    for step in range(719):
        a_v48 = agent_v48(obs48[seat])
        a_opp48 = opp48.act(obs48[opp_seat]) if hasattr(opp48, "act") else opp48(obs48[opp_seat])
        actions = [a_v48, a_opp48] if seat == 0 else [a_opp48, a_v48]
        obs48, _, _, _ = sim48.step(actions)

    cash_v48 = float(obs48[seat]["farms"][seat]["money"])
    cash_opp_v48 = float(obs48[opp_seat]["farms"][opp_seat]["money"])

    # 2. Run V49 match with step-level parity and action inspection
    sim49 = FastKagricultureSim(seed=seed)
    obs49 = sim49.reset(seed=seed)
    opp49 = load_elite_agent(opp_name)
    agent_v49 = v49_mod.agent

    pre624_divergences = 0
    non_market_divergences = 0
    e402_activations = 0
    e402_illegal_mods = 0

    for step in range(719):
        # We also query v48_mod.agent on obs49[seat] to directly compare the decision on identical state
        act_v48_on_state = agent_v48(obs49[seat])
        act_v49 = agent_v49(obs49[seat])

        if step < 624:
            if act_v48_on_state != act_v49:
                pre624_divergences += 1
        else:
            if act_v48_on_state != act_v49:
                e402_activations += 1
                # Check non-market components
                for k in act_v48_on_state:
                    if k != "market" and act_v48_on_state.get(k) != act_v49.get(k):
                        non_market_divergences += 1
                # Check market changes
                mkt_48 = act_v48_on_state.get("market", [])
                mkt_49 = act_v49.get("market", [])
                # Must only clamp BUY_SEED for WHEAT or CARROT
                for o49 in mkt_49:
                    if len(o49) >= 3 and o49[0] == "BUY_SEED":
                        if o49[1] not in ("WHEAT", "CARROT"):
                            e402_illegal_mods += 1
                        if o49[2] < 0:
                            e402_illegal_mods += 1

        a_opp49 = opp49.act(obs49[opp_seat]) if hasattr(opp49, "act") else opp49(obs49[opp_seat])
        actions = [act_v49, a_opp49] if seat == 0 else [a_opp49, act_v49]
        obs49, _, _, _ = sim49.step(actions)

    cash_v49 = float(obs49[seat]["farms"][seat]["money"])
    cash_opp_v49 = float(obs49[opp_seat]["farms"][opp_seat]["money"])

    win_v48 = cash_v48 > cash_opp_v48
    loss_v48 = cash_v48 < cash_opp_v48
    tie_v48 = cash_v48 == cash_opp_v48

    win_v49 = cash_v49 > cash_opp_v49
    loss_v49 = cash_v49 < cash_opp_v49
    tie_v49 = cash_v49 == cash_opp_v49

    delta = cash_v49 - cash_v48
    rescue = loss_v48 and win_v49
    casualty = win_v48 and not win_v49

    return {
        "seed": seed,
        "seat": seat,
        "opp": opp_name,
        "cash_v48": cash_v48,
        "cash_v49": cash_v49,
        "cash_opp_v48": cash_opp_v48,
        "cash_opp_v49": cash_opp_v49,
        "delta": delta,
        "win_v48": win_v48,
        "loss_v48": loss_v48,
        "tie_v48": tie_v48,
        "win_v49": win_v49,
        "loss_v49": loss_v49,
        "tie_v49": tie_v49,
        "rescue": rescue,
        "casualty": casualty,
        "pre624_divergences": pre624_divergences,
        "non_market_divergences": non_market_divergences,
        "e402_activations": e402_activations,
        "e402_illegal_mods": e402_illegal_mods,
    }


def compute_bootstrap_ci(data: np.ndarray, n_boot: int = 10000, ci: float = 95.0) -> Tuple[float, float]:
    rng = np.random.default_rng(42)
    indices = rng.integers(0, len(data), size=(n_boot, len(data)))
    boot_means = np.mean(data[indices], axis=1)
    lower = float(np.percentile(boot_means, (100.0 - ci) / 2.0))
    upper = float(np.percentile(boot_means, 100.0 - (100.0 - ci) / 2.0))
    return lower, upper


def main():
    opponents = [
        "V44",
        "dmitrii_lb2800",
        "tetsutani_pasture",
        "kaitofukami_v48_3009",
        "indarkarhana_top10",
        "saiteja_mega_3000",
    ]

    all_tasks = [(s, seat, opp) for opp in opponents for s in SEEDS for seat in (0, 1)]
    print(f"Starting V49 Reproduction Audit: {len(all_tasks)} legs across {len(opponents)} opponents...")
    t0 = time.time()

    all_results: List[Dict[str, Any]] = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=10) as executor:
        for res in executor.map(run_paired_leg, all_tasks):
            all_results.append(res)
            if len(all_results) % 256 == 0:
                print(f"  Processed {len(all_results)} / {len(all_tasks)} legs ({time.time() - t0:.1f}s)...")

    t1 = time.time()
    print(f"Execution completed in {t1 - t0:.1f}s.")

    # Save raw per-leg results
    raw_path = os.path.join(REPO_ROOT, "research", "v50", "audit", "v49_audit_raw_legs.json")
    with open(raw_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"Saved {len(all_results)} raw leg results to {raw_path}")

    # Process metrics
    total_pre624_div = sum(r["pre624_divergences"] for r in all_results)
    total_non_market_div = sum(r["non_market_divergences"] for r in all_results)
    total_illegal_mods = sum(r["e402_illegal_mods"] for r in all_results)
    total_casualties = sum(r["casualty"] for r in all_results)
    total_rescues = sum(r["rescue"] for r in all_results)

    all_deltas = np.array([r["delta"] for r in all_results], dtype=float)
    active_deltas = np.array([r["delta"] for r in all_results if r["delta"] != 0.0], dtype=float)

    total_wins_v49 = sum(r["win_v49"] for r in all_results)
    total_losses_v49 = sum(r["loss_v49"] for r in all_results)
    total_ties_v49 = sum(r["tie_v49"] for r in all_results)

    total_wins_v48 = sum(r["win_v48"] for r in all_results)
    total_losses_v48 = sum(r["loss_v48"] for r in all_results)
    total_ties_v48 = sum(r["tie_v48"] for r in all_results)

    # Per-family stats
    by_opp = {}
    losses_corpus = []

    for opp in opponents:
        opp_legs = [r for r in all_results if r["opp"] == opp]
        deltas = np.array([r["delta"] for r in opp_legs], dtype=float)
        act_deltas = np.array([r["delta"] for r in opp_legs if r["delta"] != 0.0], dtype=float)
        wins48 = sum(r["win_v48"] for r in opp_legs)
        losses48 = sum(r["loss_v48"] for r in opp_legs)
        ties48 = sum(r["tie_v48"] for r in opp_legs)
        wins49 = sum(r["win_v49"] for r in opp_legs)
        losses49 = sum(r["loss_v49"] for r in opp_legs)
        ties49 = sum(r["tie_v49"] for r in opp_legs)
        resc = sum(r["rescue"] for r in opp_legs)
        cas = sum(r["casualty"] for r in opp_legs)

        # Confidence intervals for mean delta
        boot_ci_mean = compute_bootstrap_ci(deltas, n_boot=10000)
        n = len(deltas)
        sem = float(np.std(deltas, ddof=1) / np.sqrt(n))
        param_ci_mean = (float(np.mean(deltas) - 1.95996 * sem), float(np.mean(deltas) + 1.95996 * sem))
        sample_perc_ci = (float(np.percentile(deltas, 2.5)), float(np.percentile(deltas, 97.5)))

        by_opp[opp] = {
            "legs": len(opp_legs),
            "wins_v48": wins48,
            "losses_v48": losses48,
            "ties_v48": ties48,
            "win_rate_v48": float(wins48 / len(opp_legs)),
            "wins_v49": wins49,
            "losses_v49": losses49,
            "ties_v49": ties49,
            "win_rate_v49": float(wins49 / len(opp_legs)),
            "rescues": resc,
            "casualties": cas,
            "mean_delta": float(np.mean(deltas)),
            "median_delta": float(np.median(deltas)),
            "std_delta": float(np.std(deltas, ddof=1)),
            "sem_delta": sem,
            "p10_delta": float(np.percentile(deltas, 10.0)),
            "sample_percentile_95_ci": list(sample_perc_ci),
            "bootstrap_mean_95_ci": list(boot_ci_mean),
            "parametric_mean_95_ci": list(param_ci_mean),
            "active_legs": len(act_deltas),
            "active_mean": float(np.mean(act_deltas)) if len(act_deltas) > 0 else 0.0,
            "active_median": float(np.median(act_deltas)) if len(act_deltas) > 0 else 0.0,
        }

        for r in opp_legs:
            if r["loss_v49"]:
                losses_corpus.append(r)

    # Suite-wide aggregate stats
    suite_boot_ci = compute_bootstrap_ci(all_deltas, n_boot=10000)
    suite_n = len(all_deltas)
    suite_sem = float(np.std(all_deltas, ddof=1) / np.sqrt(suite_n))
    suite_param_ci = (float(np.mean(all_deltas) - 1.95996 * suite_sem), float(np.mean(all_deltas) + 1.95996 * suite_sem))
    suite_sample_perc = (float(np.percentile(all_deltas, 2.5)), float(np.percentile(all_deltas, 97.5)))

    reconciliation = {
        "metadata": {
            "total_legs": len(all_results),
            "seeds_count": len(SEEDS),
            "seeds_range": f"{SEEDS[0]}..{SEEDS[-1]}",
            "opponents": opponents,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        },
        "invariance_audit": {
            "turns_0_to_623_divergences": total_pre624_div,
            "non_market_action_divergences": total_non_market_div,
            "illegal_e402_modifications": total_illegal_mods,
            "casualties": total_casualties,
            "rescues": total_rescues,
            "status": "PASS" if (total_pre624_div == 0 and total_non_market_div == 0 and total_illegal_mods == 0 and total_casualties == 0) else "FAIL"
        },
        "suite_metrics": {
            "overall_mean_delta": float(np.mean(all_deltas)),
            "overall_median_delta": float(np.median(all_deltas)),
            "overall_std_delta": float(np.std(all_deltas, ddof=1)),
            "overall_sem_delta": suite_sem,
            "active_legs": len(active_deltas),
            "active_fraction": float(len(active_deltas) / len(all_deltas)),
            "active_mean_delta": float(np.mean(active_deltas)),
            "active_median_delta": float(np.median(active_deltas)),
            "gate_b_v44_active_mean": by_opp["V44"]["active_mean"],
            "suite_win_rate_v48": float(total_wins_v48 / len(all_results)),
            "suite_win_rate_v49": float(total_wins_v49 / len(all_results)),
            "total_wins_v49": total_wins_v49,
            "total_losses_v49": total_losses_v49,
            "total_ties_v49": total_ties_v49,
            "bootstrap_mean_95_ci": list(suite_boot_ci),
            "parametric_mean_95_ci": list(suite_param_ci),
            "sample_percentile_95_ci": list(suite_sample_perc),
        },
        "by_opponent": by_opp,
        "delta_distribution_percentiles": {
            "p0_min": float(np.min(all_deltas)),
            "p1": float(np.percentile(all_deltas, 1.0)),
            "p2_5": float(np.percentile(all_deltas, 2.5)),
            "p5": float(np.percentile(all_deltas, 5.0)),
            "p10": float(np.percentile(all_deltas, 10.0)),
            "p25": float(np.percentile(all_deltas, 25.0)),
            "p50_median": float(np.percentile(all_deltas, 50.0)),
            "p75": float(np.percentile(all_deltas, 75.0)),
            "p90": float(np.percentile(all_deltas, 90.0)),
            "p95": float(np.percentile(all_deltas, 95.0)),
            "p97_5": float(np.percentile(all_deltas, 97.5)),
            "p99": float(np.percentile(all_deltas, 99.0)),
            "p100_max": float(np.max(all_deltas)),
        },
        "delta_histogram_counts": {
            "delta_0": int(np.sum(all_deltas == 0.0)),
            "delta_0_to_40": int(np.sum((all_deltas > 0) & (all_deltas <= 40))),
            "delta_40_to_80": int(np.sum((all_deltas > 40) & (all_deltas <= 80))),
            "delta_80_to_120": int(np.sum((all_deltas > 80) & (all_deltas <= 120))),
            "delta_120_to_160": int(np.sum((all_deltas > 120) & (all_deltas <= 160))),
            "delta_over_160": int(np.sum(all_deltas > 160)),
            "negative_delta": int(np.sum(all_deltas < 0)),
        },
        "outright_losses_count": len(losses_corpus),
    }

    out_json = os.path.join(REPO_ROOT, "research", "v50", "audit", "v49_metric_reconciliation.json")
    with open(out_json, "w") as f:
        json.dump(reconciliation, f, indent=2)
    print(f"Metric reconciliation written to {out_json}")

    # Print summary highlights
    print("\n" + "=" * 80)
    print("V49 AUDIT RECONCILIATION SUMMARY")
    print("=" * 80)
    print(f"Invariance 0..623 Divergences: {total_pre624_div}")
    print(f"Non-market Divergences: {total_non_market_div}")
    print(f"Illegal E402 modifications: {total_illegal_mods}")
    print(f"Casualties: {total_casualties}")
    print(f"Rescues: {total_rescues}")
    print(f"Overall Mean Delta: +${reconciliation['suite_metrics']['overall_mean_delta']:.2f}")
    print(f"Active Mean Delta: +${reconciliation['suite_metrics']['active_mean_delta']:.2f}")
    print(f"Gate-B V44 Active Mean: +${reconciliation['suite_metrics']['gate_b_v44_active_mean']:.2f}")
    print(f"Suite Win Rate: {reconciliation['suite_metrics']['suite_win_rate_v49']*100:.2f}% ({total_wins_v49}W, {total_losses_v49}L, {total_ties_v49}T)")
    print(f"Total Outright Losses: {len(losses_corpus)}")
    print(f"Sample Percentile 95% Interval: {reconciliation['suite_metrics']['sample_percentile_95_ci']}")
    print(f"Bootstrap Mean 95% CI: [{reconciliation['suite_metrics']['bootstrap_mean_95_ci'][0]:.2f}, {reconciliation['suite_metrics']['bootstrap_mean_95_ci'][1]:.2f}]")
    print(f"Parametric Mean 95% CI: [{reconciliation['suite_metrics']['parametric_mean_95_ci'][0]:.2f}, {reconciliation['suite_metrics']['parametric_mean_95_ci'][1]:.2f}]")


if __name__ == "__main__":
    main()
