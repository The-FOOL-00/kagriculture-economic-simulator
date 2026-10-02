# SPDX-License-Identifier: MIT
"""V45 Market Counterfactual Search & Strategy Evaluation Engine.

Evaluates 10 systematic adversarial market strategies against V44 across
64 baseline match legs (8 clean seeds x 4 opponents x 2 seats):
- Dynamic Opponent-Pressure Pre-emption
- Early Pre-emption (Step 691-692)
- Tranche Ratio Variations (40/60, 60/40, 70/30)
- Market Depth & Order Slippage Capping
- Post-Dump Recovery Synchronization
- Full Adversarial Market Portfolio

All rollouts are FULL-TERMINAL (to Step 719).
Calculates cash alpha, relative matchup alpha, rescues, and casualties.
Outputs:
- research/v45/artifacts/market_counterfactuals.json
- research/v45/artifacts/market_rescue_library.json
- research/v45/artifacts/adversarial_alpha_catalog.json
"""

from __future__ import annotations
import copy
import json
import os
import sys
import time
from typing import Any, Callable, Dict, List, Tuple
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v45.governance import assert_seed_safe, assert_protected_artifacts
from research.v40.env.fast_sim import FastKagricultureSim
from candidates.v44_economic_portfolio.main import V44CandidateController
from candidates.v35_a7_opening.main import V35OpeningController
from candidates.v32_rlx2.opponents import load_league_opponent

# 8 diverse DEV seeds (including loss/near-tie forensic seeds 249657 and 249659)
SEARCH_SEEDS = [249635, 249636, 249645, 249646, 249655, 249656, 249657, 249659]
OPPONENTS = ["E8_DMITRII", "E2_A7", "E0_V3", "SYN_AGG"]

COMMODITIES = ["STRAWBERRY", "MILK", "WOOL", "MELON"]


class AdversarialMarketStrategy:
    """Configurable experimental adversarial market controller."""
    def __init__(
        self,
        name: str,
        preempt_window: Tuple[int, int] = (693, 694),
        first_tranche_pct: float = 0.50,
        second_window: Tuple[int, int] = (704, 705),
        second_tranche_pct: float = 0.50,
        final_flush_step: int = 716,
        depth_capping: bool = False,
        max_units_per_order: int = 15,
        dynamic_pressure_trigger: bool = False,
        pressure_threshold: float = 0.65,
    ):
        self.name = name
        self.v35 = V35OpeningController()
        self.preempt_window = preempt_window
        self.first_tranche_pct = first_tranche_pct
        self.second_window = second_window
        self.second_tranche_pct = second_tranche_pct
        self.final_flush_step = final_flush_step
        self.depth_capping = depth_capping
        self.max_units_per_order = max_units_per_order
        self.dynamic_pressure_trigger = dynamic_pressure_trigger
        self.pressure_threshold = pressure_threshold
        self.has_preempted = False

    def reset(self):
        self.v35.reset()
        self.has_preempted = False

    def act(self, obs: Dict[str, Any], cfg: Any = None) -> Dict[str, Any]:
        base_act = self.v35.act(obs, cfg)
        step = int(obs.get("step", 0) or 0)
        
        # Golden property for turns 0..519
        if step < 520:
            return base_act

        try:
            private = obs.get("private", {}) or {}
            shed = dict(private.get("shed", {}) or {})
            act = copy.deepcopy(base_act)
            mkt = act.setdefault("market", [])

            # Defensive investment payback cutoff
            if step >= 520:
                mkt = [o for o in mkt if not (len(o) > 0 and o[0] in ("BUY_ANIMAL", "BUY_LAND"))]

            if step < 685:
                act["market"] = mkt[:10]
                return act

            already_selling = {o[1] for o in mkt if len(o) > 1 and o[0] == "SELL"}

            # Dynamic pressure trigger check (steps 688..694)
            trigger_preempt = False
            if self.dynamic_pressure_trigger and 688 <= step <= 694 and not self.has_preempted:
                # Inferred opponent dump or rising inventory saturation
                mkt_state = obs.get("market", {}) or {}
                # Check if prices of high-value goods have started to tick down
                prices = mkt_state.get("prices", {}) or {}
                if any(prices.get(c, 200) < 110 for c in ["STRAWBERRY", "MILK"]):
                    trigger_preempt = True

            # First tranche execution
            in_first_window = (self.preempt_window[0] <= step <= self.preempt_window[1]) or trigger_preempt
            if in_first_window and not self.has_preempted:
                for item in COMMODITIES:
                    qty = shed.get(item, 0)
                    if qty >= 2 and item not in already_selling and len(mkt) < 10:
                        raw_qty = max(1, int(round(qty * self.first_tranche_pct)))
                        if self.depth_capping and item in ("STRAWBERRY", "MILK", "WOOL"):
                            sell_qty = min(raw_qty, self.max_units_per_order)
                        else:
                            sell_qty = raw_qty
                        mkt.append(["SELL", item, sell_qty])
                        already_selling.add(item)
                if any(o[0] == "SELL" for o in mkt):
                    self.has_preempted = True

            # Second tranche execution (steps 704..705)
            elif self.second_window[0] <= step <= self.second_window[1]:
                for item in COMMODITIES:
                    qty = shed.get(item, 0)
                    if qty >= 2 and item not in already_selling and len(mkt) < 10:
                        raw_qty = max(1, int(round(qty * self.second_tranche_pct)))
                        if self.depth_capping and item in ("STRAWBERRY", "MILK", "WOOL"):
                            sell_qty = min(raw_qty, self.max_units_per_order)
                        else:
                            sell_qty = raw_qty
                        mkt.append(["SELL", item, sell_qty])
                        already_selling.add(item)

            # Final flush (steps 716+)
            elif step >= self.final_flush_step:
                for item in COMMODITIES:
                    qty = shed.get(item, 0)
                    if qty > 0 and item not in already_selling and len(mkt) < 10:
                        mkt.append(["SELL", item, qty])
                        already_selling.add(item)

            act["market"] = mkt[:10]
            return act
        except Exception:
            return base_act


def _act(agent: Any, obs: Dict[str, Any]) -> Dict[str, Any]:
    if hasattr(agent, "act") and callable(getattr(agent, "act")):
        return agent.act(obs)
    return agent(obs)


def evaluate_strategies():
    print("=" * 80)
    print("V45 PHASE 3 & 5: MARKET COUNTERFACTUAL SEARCH & ADVERSARIAL DISCOVERY")
    print("=" * 80)
    assert_protected_artifacts()
    for s in SEARCH_SEEDS:
        assert_seed_safe(s)

    opp_masters = {opp_id: load_league_opponent(opp_id) for opp_id in OPPONENTS}

    # Define the 10 candidate adversarial market strategies
    strategies: Dict[str, Callable[[], Any]] = {
        "V44_BASELINE": lambda: V44CandidateController(),
        "PREEMPT_691_692": lambda: AdversarialMarketStrategy("PREEMPT_691_692", preempt_window=(691, 692), first_tranche_pct=0.50),
        "PREEMPT_692_693": lambda: AdversarialMarketStrategy("PREEMPT_692_693", preempt_window=(692, 693), first_tranche_pct=0.50),
        "TRANCHE_40_60": lambda: AdversarialMarketStrategy("TRANCHE_40_60", preempt_window=(693, 694), first_tranche_pct=0.40, second_tranche_pct=0.60),
        "TRANCHE_60_40": lambda: AdversarialMarketStrategy("TRANCHE_60_40", preempt_window=(693, 694), first_tranche_pct=0.60, second_tranche_pct=0.40),
        "TRANCHE_70_30": lambda: AdversarialMarketStrategy("TRANCHE_70_30", preempt_window=(693, 694), first_tranche_pct=0.70, second_tranche_pct=0.30),
        "DEPTH_CAPPED_15": lambda: AdversarialMarketStrategy("DEPTH_CAPPED_15", preempt_window=(693, 694), first_tranche_pct=0.50, depth_capping=True, max_units_per_order=15),
        "DEPTH_CAPPED_10": lambda: AdversarialMarketStrategy("DEPTH_CAPPED_10", preempt_window=(693, 694), first_tranche_pct=0.50, depth_capping=True, max_units_per_order=10),
        "DYNAMIC_PREEMPT": lambda: AdversarialMarketStrategy("DYNAMIC_PREEMPT", preempt_window=(693, 694), first_tranche_pct=0.50, dynamic_pressure_trigger=True),
        "ADVERSARIAL_PORTFOLIO": lambda: AdversarialMarketStrategy(
            "ADVERSARIAL_PORTFOLIO",
            preempt_window=(692, 693),  # Front-run step 695 by 2 steps
            first_tranche_pct=0.60,     # Monetize 60% before order book decays
            second_window=(704, 705),   # Secondary town drain absorption
            second_tranche_pct=0.50,
            depth_capping=True,         # Guard against extreme single-order slippage
            max_units_per_order=15,
            dynamic_pressure_trigger=True
        ),
    }

    # First, run the baseline across all 64 matchups to establish the exact reference
    print("Running baseline V44 across 64 match legs...")
    t0 = time.perf_counter()
    baseline_results: Dict[Tuple[int, str, int], dict] = {}

    for seed in SEARCH_SEEDS:
        for opp_id in OPPONENTS:
            opp_master = opp_masters[opp_id]
            for seat in [0, 1]:
                sim = FastKagricultureSim(seed=seed)
                cand = V44CandidateController()
                opp = copy.deepcopy(opp_master)
                oc0, oc1 = sim.reset(seed=seed)
                while not sim.done:
                    act0 = _act(cand, oc0) if seat == 0 else opp(oc0)
                    act1 = opp(oc1) if seat == 0 else _act(cand, oc1)
                    [oc0, oc1], _, _, _ = sim.step([act0, act1])
                cand_cash = float(oc0["farms"][0]["money"] if seat == 0 else oc1["farms"][1]["money"])
                opp_cash = float(oc1["farms"][1]["money"] if seat == 0 else oc0["farms"][0]["money"])
                margin = cand_cash - opp_cash
                win = margin > 0
                baseline_results[(seed, opp_id, seat)] = {
                    "cash": cand_cash, "opp_cash": opp_cash, "margin": margin, "win": win
                }

    print(f"Baseline completed in {time.perf_counter() - t0:.1f}s.")

    # Now evaluate each candidate strategy against baseline
    results_by_strategy = {}
    rescue_library = []

    for strat_name, strat_factory in strategies.items():
        if strat_name == "V44_BASELINE":
            continue
        print(f"\n--- Evaluating Candidate: {strat_name} ---")
        t_strat = time.perf_counter()
        cash_deltas = []
        margin_deltas = []
        rescues = 0
        casualties = 0
        cand_wins = 0

        for seed in SEARCH_SEEDS:
            for opp_id in OPPONENTS:
                opp_master = opp_masters[opp_id]
                for seat in [0, 1]:
                    sim = FastKagricultureSim(seed=seed)
                    cand = strat_factory()
                    opp = copy.deepcopy(opp_master)
                    oc0, oc1 = sim.reset(seed=seed)
                    while not sim.done:
                        act0 = _act(cand, oc0) if seat == 0 else opp(oc0)
                        act1 = opp(oc1) if seat == 0 else _act(cand, oc1)
                        [oc0, oc1], _, _, _ = sim.step([act0, act1])
                    c_cash = float(oc0["farms"][0]["money"] if seat == 0 else oc1["farms"][1]["money"])
                    o_cash = float(oc1["farms"][1]["money"] if seat == 0 else oc0["farms"][0]["money"])
                    c_margin = c_cash - o_cash
                    c_win = c_margin > 0

                    base = baseline_results[(seed, opp_id, seat)]
                    c_delta = c_cash - base["cash"]
                    m_delta = c_margin - base["margin"]

                    cash_deltas.append(c_delta)
                    margin_deltas.append(m_delta)
                    if c_win:
                        cand_wins += 1

                    if not base["win"] and c_win:
                        rescues += 1
                        rescue_library.append({
                            "strategy": strat_name, "seed": seed, "opp_id": opp_id, "seat": seat,
                            "base_cash": base["cash"], "cand_cash": c_cash,
                            "base_margin": base["margin"], "cand_margin": c_margin,
                            "margin_delta": m_delta, "type": "LOSE_TO_WIN"
                        })
                    elif not base["win"] and (c_margin > base["margin"]):
                        # deficit reduction
                        rescue_library.append({
                            "strategy": strat_name, "seed": seed, "opp_id": opp_id, "seat": seat,
                            "base_cash": base["cash"], "cand_cash": c_cash,
                            "base_margin": base["margin"], "cand_margin": c_margin,
                            "margin_delta": m_delta, "type": "DEFICIT_REDUCTION"
                        })
                    if base["win"] and not c_win:
                        casualties += 1

        mean_c_delta = float(np.mean(cash_deltas))
        median_c_delta = float(np.median(cash_deltas))
        mean_m_delta = float(np.mean(margin_deltas))
        win_rate = (cand_wins / len(cash_deltas)) * 100.0

        summary = {
            "strategy": strat_name,
            "total_legs": len(cash_deltas),
            "mean_cash_delta_vs_v44": round(mean_c_delta, 2),
            "median_cash_delta_vs_v44": round(median_c_delta, 2),
            "mean_margin_delta_vs_v44": round(mean_m_delta, 2),
            "win_rate": round(win_rate, 2),
            "rescues": rescues,
            "casualties": casualties,
            "p5_cash_delta": round(float(np.percentile(cash_deltas, 5)), 2),
            "worst_cash_delta": round(float(np.min(cash_deltas)), 2),
            "positive_hit_rate": round(float(np.mean(np.array(cash_deltas) > 0) * 100), 1),
        }
        results_by_strategy[strat_name] = summary
        dur_strat = time.perf_counter() - t_strat
        print(f"  Result: Mean Cash Delta: ${mean_c_delta:>+7.2f} (Med: ${median_c_delta:>+7.2f}) | Margin Delta: ${mean_m_delta:>+7.2f} | WR: {win_rate:.1f}% | Rescues: {rescues} | Casualties: {casualties} ({dur_strat:.1f}s)")

    # Save artifacts
    artifacts_dir = os.path.join(REPO_ROOT, "research", "v45", "artifacts")
    os.makedirs(artifacts_dir, exist_ok=True)

    out_cf = os.path.join(artifacts_dir, "market_counterfactuals.json")
    with open(out_cf, "w") as f:
        json.dump(results_by_strategy, f, indent=2)

    out_res = os.path.join(artifacts_dir, "market_rescue_library.json")
    with open(out_res, "w") as f:
        json.dump(rescue_library, f, indent=2)

    # Sort and rank strategies
    catalog = sorted(results_by_strategy.values(), key=lambda x: (x["casualties"], -x["mean_cash_delta_vs_v44"]))
    out_cat = os.path.join(artifacts_dir, "adversarial_alpha_catalog.json")
    with open(out_cat, "w") as f:
        json.dump(catalog, f, indent=2)

    print("\n" + "=" * 80)
    print("V45 COUNTERFACTUAL SEARCH & ALPHA CATALOG SUMMARY")
    print("=" * 80)
    print(f"{'Rank':<4} | {'Strategy Name':<25} | {'Mean Cash d':<12} | {'Med Cash d':<11} | {'Margin d':<10} | {'Cas':<5} | {'Res':<5} | {'Hit%':<6}")
    print("-" * 85)
    for r, s in enumerate(catalog, 1):
        print(f"{r:<4} | {s['strategy']:<25} | ${s['mean_cash_delta_vs_v44']:>+10.2f} | ${s['median_cash_delta_vs_v44']:>+9.2f} | ${s['mean_margin_delta_vs_v44']:>+8.2f} | {s['casualties']:<5} | {s['rescues']:<5} | {s['positive_hit_rate']}%")

    return catalog


if __name__ == "__main__":
    evaluate_strategies()
