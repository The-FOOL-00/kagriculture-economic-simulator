#!/usr/bin/env python3
"""Build the 2945 Loss Corpus for Kagriculture V48.

Runs thomastschinkel_2945 against the elite opponent suite (V44, dmitrii, indarkarhana, pasture, 3009)
across clean dev seeds in parallel.
For every game where 2945 loses (or has margin < $500):
Captures complete synchronized trajectories, checkpoint states (72, 144, 216, 288, 360, 432, 520, 648, 693, 704, 716, 718),
cash curves, market price curves, shop sequences, and classifies into causal failure taxonomy.
Saves to research/v48/loss_forensics/2945_loss_corpus.jsonl.
"""

from __future__ import annotations
import concurrent.futures
import copy
import json
import os
import sys
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

sys.stdout.reconfigure(line_buffering=True)

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from candidates.v44_economic_portfolio.main import V44CandidateController
from research.v47.elite_benchmark.run_elite_benchmark import load_agent as load_elite_agent

# 128 Clean dev seeds (256 legs per opponent suite)
SEEDS = [249800 + i for i in range(128)]
PROTECTED_HOLDOUTS = [(214200, 214249), (340090, 340199), (249695, 249734)]

for s in SEEDS:
    for start, end in PROTECTED_HOLDOUTS:
        assert not (start <= s <= end), f"CRITICAL: Protected holdout seed {s} accessed!"

CHECKPOINTS = (72, 144, 216, 288, 360, 432, 520, 648, 693, 704, 716, 718)


def extract_snapshot(obs: Dict[str, Any], seat: int) -> Dict[str, Any]:
    farm = obs["farms"][seat]
    animals = defaultdict(int)
    crops = defaultdict(int)
    for row in farm["tiles"]:
        for t in row:
            if isinstance(t, dict):
                if t.get("animal"):
                    animals[t["animal"]] += 1
                elif t.get("crop"):
                    crops[t["crop"]] += 1

    priv = obs.get("private", {}) or {}
    shed = dict(priv.get("shed", {}) or {})
    mkt = obs.get("market", {}) or {}
    prices = dict(mkt.get("prices", {}) or {})
    inv = dict(mkt.get("inventory", {}) or {})

    return {
        "cash": float(farm.get("money", 0) or 0),
        "hands": len(farm.get("hands", []) or []),
        "land": len(farm.get("unlocked_quadrants", ["NW"]) or ["NW"]),
        "animals": dict(animals),
        "crops": dict(crops),
        "shed": shed,
        "market_prices": prices,
        "market_inventory": inv,
    }


def classify_loss_causality(loss_record: Dict[str, Any]) -> str:
    """Classify the loss into a specific causal taxonomy category."""
    shops = loss_record.get("shops", [])
    snaps = loss_record.get("checkpoints", {})
    t718 = snaps.get(718, {})
    t144 = snaps.get(144, {})
    t520 = snaps.get(520, {})
    
    # 1. Shop Route: Did 2945 pick a sub-optimal route given revealed shops?
    if len(shops) >= 2:
        shop_pair = tuple(shops[:2])
        if "YARN_STORE" not in shop_pair and "PIZZA_SHOP" in shop_pair:
            # Pizza shop worlds without yarn
            if t718.get("animals", {}).get("COW", 0) < 6:
                return "SHOP_ROUTE"
        if "YARN_STORE" in shop_pair:
            # Yarn worlds where wool was under-produced or crashed
            if t718.get("shed", {}).get("WOOL", 0) > 10:
                return "MARKET_TIMING"

    # 2. Shed Capacity: Item overflow in shed
    shed_items = sum(t718.get("shed", {}).values())
    if shed_items > 20:
        return "SHED_CAPACITY"

    # 3. Terminal Liquidation: Late game unsold inventory
    late_stock = sum(t718.get("shed", {}).get(k, 0) for k in ("MILK", "WOOL", "STRAWBERRY", "MELON"))
    if late_stock > 5:
        return "TERMINAL_LIQUIDATION"

    # 4. Animal selection vs Crop selection
    if t718.get("animals", {}).get("SHEEP", 0) > 8 and "YARN_STORE" not in shops:
        return "ANIMAL_SELECTION"

    # 5. Market timing: prices crashed before sale
    prices = t718.get("market_prices", {})
    if prices.get("WOOL", 200) < 100 or prices.get("MILK", 160) < 80:
        return "MARKET_TIMING"

    return "UNKNOWN"


def run_single_forensics_match(args: Tuple[str, str, int, int]) -> Optional[Dict[str, Any]]:
    opp_key, seed, seat_2945 = args
    opp_seat = 1 - seat_2945

    agent_2945 = load_elite_agent("thomastschinkel_2945")
    opp_agent = load_elite_agent(opp_key)

    sim = FastKagricultureSim(seed=seed)
    obs_list = sim.reset(seed=seed)

    checkpoints = {}
    cash_curve_2945 = []
    cash_curve_opp = []
    margin_curve = []

    for step in range(719):
        obs_2945 = obs_list[seat_2945]
        obs_opp = obs_list[opp_seat]

        if step in CHECKPOINTS:
            checkpoints[step] = extract_snapshot(obs_2945, seat_2945)

        act_2945 = agent_2945(obs_2945)
        act_opp = opp_agent.act(obs_opp) if hasattr(opp_agent, "act") else opp_agent(obs_opp)

        actions = [act_2945, act_opp] if seat_2945 == 0 else [act_opp, act_2945]
        obs_list, rewards, done, info = sim.step(actions)

        c_2945 = float(obs_list[seat_2945]["farms"][seat_2945]["money"])
        c_opp = float(obs_list[opp_seat]["farms"][opp_seat]["money"])
        cash_curve_2945.append(c_2945)
        cash_curve_opp.append(c_opp)
        margin_curve.append(c_2945 - c_opp)

    terminal_cash_2945 = cash_curve_2945[-1]
    terminal_cash_opp = cash_curve_opp[-1]
    final_margin = terminal_cash_2945 - terminal_cash_opp

    town = obs_list[0].get("town", {}) or {}
    unlocked_shops = list(town.get("unlocked_shops", []) or [])

    # If 2945 lost or had a tight game (margin <= 500)
    if final_margin < 0:
        record = {
            "seed": seed,
            "seat_2945": seat_2945,
            "opponent": opp_key,
            "terminal_cash_2945": terminal_cash_2945,
            "terminal_cash_opp": terminal_cash_opp,
            "margin": final_margin,
            "shops": unlocked_shops,
            "checkpoints": checkpoints,
            "cash_curve_sampled": cash_curve_2945[::24],
            "margin_curve_sampled": margin_curve[::24],
        }
        record["causal_classification"] = classify_loss_causality(record)
        return record
    return None


def main():
    opponents = ["V44", "dmitrii_lb2800", "tetsutani_pasture", "kaitofukami_v48_3009", "indarkarhana_top10"]
    tasks = [(opp, s, seat) for opp in opponents for s in SEEDS for seat in (0, 1)]
    print(f"Executing 2945 loss forensics search across {len(tasks)} matches ({len(SEEDS)} seeds x 2 seats x {len(opponents)} opponents)...")

    losses = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(run_single_forensics_match, t) for t in tasks]
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res is not None:
                losses.append(res)
                print(f"  [LOSS] Opp={res['opponent']:16s} Seed={res['seed']} Seat={res['seat_2945']} Margin={res['margin']:+7.1f} | Shops={res['shops'][:3]} | Cause={res['causal_classification']}")

    out_file = os.path.join(REPO_ROOT, "research", "v48", "loss_forensics", "2945_loss_corpus.jsonl")
    with open(out_file, "w", encoding="utf-8") as f:
        for l in losses:
            f.write(json.dumps(l) + "\n")

    print(f"\nLoss forensics complete! Captured {len(losses)} losses to {out_file}.")

    # Taxonomy summary
    taxonomy = defaultdict(int)
    for l in losses:
        taxonomy[l["causal_classification"]] += 1
    print("\n=== CAUSAL TAXONOMY BREAKDOWN ===")
    for k, v in sorted(taxonomy.items(), key=lambda x: -x[1]):
        print(f"  {k:25s}: {v:3d} losses ({v/len(losses)*100:.1f}%)" if losses else "  None")


if __name__ == "__main__":
    main()
