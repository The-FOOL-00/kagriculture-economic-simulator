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
import candidates.v44_economic_portfolio.main as v44_mod
import candidates.v48_challenger.main as v48_mod
import candidates.v49_meta_fusion.main as v49_mod
from research.v50.counterfactuals.run_exact_counterfactuals import make_candidate_agent, compute_bootstrap_ci

PROTECTED_HOLDOUTS = [(214200, 214249), (340090, 340199), (249695, 249734)]

# Fresh Evaluation Seeds (strictly disjoint from discovery seeds 250400-250527 and holdouts)
FRESH_SEEDS = [250600 + i for i in range(32)] # 32 seeds * 2 seats * 9 opponents = 576 legs

for s in FRESH_SEEDS:
    for start, end in PROTECTED_HOLDOUTS:
        assert not (start <= s <= end), f"CRITICAL: Protected holdout seed {s} accessed!"
    assert not (250400 <= s <= 250527), f"CRITICAL: Discovery seed {s} accessed in fresh evaluation!"


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


def run_fresh_leg(args: Tuple[int, int, str, Dict[str, Any]]) -> Dict[str, Any]:
    seed, seat, opp_name, cand_cfg = args
    opp_seat = 1 - seat

    # 1. V49 Baseline
    sim49 = FastKagricultureSim(seed=seed)
    obs49 = sim49.reset(seed=seed)
    opp49 = load_any_agent(opp_name)
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
    opp_c = load_any_agent(opp_name)

    if cand_cfg.get("is_v44"):
        agent_c = v44_mod.agent
    elif cand_cfg.get("is_v48"):
        agent_c = v48_mod.agent
    else:
        agent_c = make_candidate_agent(cand_cfg)

    for step in range(719):
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
        "cash49": cash49,
        "cash_c": cash_c,
        "delta": delta,
        "win49": win49,
        "win_c": win_c,
        "rescue": rescue,
        "casualty": casualty,
    }


def compute_subset_metrics(sub_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not sub_results:
        return {}
    deltas = np.array([r["delta"] for r in sub_results], dtype=float)
    active = [r for r in sub_results if r["delta"] != 0.0]
    rescues = sum(r["rescue"] for r in sub_results)
    casualties = sum(r["casualty"] for r in sub_results)
    wins49 = sum(r["win49"] for r in sub_results)
    wins_c = sum(r["win_c"] for r in sub_results)
    boot_ci = compute_bootstrap_ci(deltas)

    return {
        "legs": len(sub_results),
        "mean_delta_vs_v49": float(np.mean(deltas)),
        "median_delta": float(np.median(deltas)),
        "bootstrap_95_ci": list(boot_ci),
        "win_rate_v49": float(wins49 / len(sub_results)),
        "win_rate_cand": float(wins_c / len(sub_results)),
        "rescues": rescues,
        "casualties": casualties,
        "active_legs": len(active),
        "active_fraction": float(len(active) / len(sub_results)),
    }


def evaluate_candidate(name: str, cand_cfg: Dict[str, Any], elite_opponents: List[str], adversarial_opponents: List[str]) -> Dict[str, Any]:
    all_opponents = elite_opponents + adversarial_opponents
    tasks = [(s, seat, opp, cand_cfg) for opp in all_opponents for s in FRESH_SEEDS for seat in (0, 1)]
    print(f"\n--- Running Fresh Evaluation: {name} ({len(tasks)} legs across 9 opponents) ---")
    t0 = time.time()

    with concurrent.futures.ProcessPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(run_fresh_leg, tasks))

    overall = compute_subset_metrics(results)

    # Elite subset (6 opponents)
    elite_results = [r for r in results if r["opp"] in elite_opponents]
    elite_metrics = compute_subset_metrics(elite_results)

    # Adversarial subset (3 opponents)
    adv_results = [r for r in results if r["opp"] in adversarial_opponents]
    adv_metrics = compute_subset_metrics(adv_results)

    # Per opponent breakdown
    per_opp = {}
    for opp in all_opponents:
        sub = [r for r in results if r["opp"] == opp]
        sub_metrics = compute_subset_metrics(sub)
        per_opp[opp] = sub_metrics

    summary = {
        "candidate": name,
        "config": cand_cfg,
        "time_seconds": float(time.time() - t0),
        "overall": overall,
        "elite_suite": elite_metrics,
        "adversarial_suite": adv_metrics,
        "per_opponent": per_opp,
    }

    print(f"  Overall Mean Delta vs V49: {overall['mean_delta_vs_v49']:+.2f} (95% CI [{overall['bootstrap_95_ci'][0]:+.2f}, {overall['bootstrap_95_ci'][1]:+.2f}])")
    print(f"  Overall WR: V49 {overall['win_rate_v49']*100:.2f}% | Cand {overall['win_rate_cand']*100:.2f}% (Rescues: {overall['rescues']}, Casualties: {overall['casualties']})")
    print(f"  Elite Suite: Delta {elite_metrics['mean_delta_vs_v49']:+.2f}, WR {elite_metrics['win_rate_cand']*100:.2f}% vs V49 {elite_metrics['win_rate_v49']*100:.2f}%")
    print(f"  Adversarial Suite: Delta {adv_metrics['mean_delta_vs_v49']:+.2f}, WR {adv_metrics['win_rate_cand']*100:.2f}% vs V49 {adv_metrics['win_rate_v49']*100:.2f}%")
    return summary


def main():
    print("=" * 80)
    print("V50 FRESH VALIDATION BENCHMARK (PHASE 9)")
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

    # 1. Historical Reference: Frozen V44 Incumbent
    ladder["V44_Incumbent"] = evaluate_candidate(
        "V44_Incumbent",
        {"is_v44": True},
        elite_opponents,
        adversarial_opponents,
    )

    # 2. Historical Reference: Frozen V48 Challenger
    ladder["V48_Challenger"] = evaluate_candidate(
        "V48_Challenger",
        {"is_v48": True},
        elite_opponents,
        adversarial_opponents,
    )

    # 3. Baseline Parity Reference: Frozen V49 Meta Fusion
    ladder["V49_Meta_Fusion"] = evaluate_candidate(
        "V49_Meta_Fusion",
        {},
        elite_opponents,
        adversarial_opponents,
    )

    # 4. V50 Dead Action Guard Candidate
    ladder["V50_Dead_Action_Guard"] = evaluate_candidate(
        "V50_Dead_Action_Guard",
        {
            "enable_extended_seeds": True,
            "seed_step_threshold": 624,
            "enable_post670_blackout": True,
        },
        elite_opponents,
        adversarial_opponents,
    )

    # 5. V50 Fertilizer Guard Variant (Ablation to document failure mechanism)
    ladder["V50_Fert_Guard_Variant"] = evaluate_candidate(
        "V50_Fert_Guard_Variant",
        {
            "enable_fert_guard": True,
            "fert_step_threshold": 646,
        },
        elite_opponents,
        adversarial_opponents,
    )

    out_file = os.path.join(REPO_ROOT, "research", "v50", "benchmarks", "v50_fresh_ladder.json")
    with open(out_file, "w") as f:
        json.dump(ladder, f, indent=2)
    print(f"\nFresh validation ladder successfully saved to {out_file}!")


if __name__ == "__main__":
    main()
