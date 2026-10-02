import sys, os
sys.path.insert(0, os.path.abspath("."))
import json
import concurrent.futures
from collections import defaultdict
import numpy as np

from research.v40.env.fast_sim import FastKagricultureSim
from research.v47.elite_benchmark.run_elite_benchmark import load_agent as load_elite_agent
import candidates.v49_meta_fusion.main as v49_mod

FRESH_SEEDS = [250600 + i for i in range(32)]
ELITE_OPPONENTS = [
    "V44",
    "dmitrii_lb2800",
    "tetsutani_pasture",
    "kaitofukami_v48_3009",
    "indarkarhana_top10",
    "saiteja_mega_3000",
]
ADV_OPPONENTS = [
    "DAIRY_FLOOD",
    "WOOL_FLOOD",
    "TERMINAL_DUMPER",
]
ALL_OPPONENTS = ELITE_OPPONENTS + ADV_OPPONENTS

def make_adversary(strategy: str):
    def _adv(obs, cfg=None):
        step = int(obs.get("step", 0))
        seat = int(obs.get("player", 0))
        farm = obs["farms"][seat]
        shed = farm.get("shed", {}) or {}
        hands = farm.get("hands", []) or []
        mkt = []
        if strategy == "DAIRY_FLOOD":
            milk = shed.get("MILK", 0)
            if milk > 0: mkt.append(["SELL", "MILK", milk])
            if step < 240 and farm.get("money", 0) >= 400: mkt.append(["BUY_ANIMAL", "COW", 1])
        elif strategy == "WOOL_FLOOD":
            wool = shed.get("WOOL", 0)
            if wool > 0: mkt.append(["SELL", "WOOL", wool])
            if step < 240 and farm.get("money", 0) >= 500: mkt.append(["BUY_ANIMAL", "SHEEP", 1])
        elif strategy == "TERMINAL_DUMPER":
            if step >= 680:
                for item in ("MILK", "WOOL", "WHEAT", "CARROT", "EGG"):
                    qty = shed.get(item, 0)
                    if qty > 0 and len(mkt) < 10: mkt.append(["SELL", item, qty])
        return {"farmer": ["PASS"], "hands": [["PASS"] for _ in hands], "market": mkt[:10]}
    return _adv

def load_opp(opp_name: str):
    if opp_name in ADV_OPPONENTS: return make_adversary(opp_name)
    return load_elite_agent(opp_name)

def run_leg(task):
    seed, seat, opp_name = task
    opp_seat = 1 - seat
    sim = FastKagricultureSim(seed=seed)
    obs = sim.reset(seed=seed)
    opp = load_opp(opp_name)
    
    for _ in range(719):
        a49 = v49_mod.agent(obs[seat])
        aopp = opp.act(obs[opp_seat]) if hasattr(opp, "act") else opp(obs[opp_seat])
        obs, _, done, _ = sim.step([a49, aopp] if seat == 0 else [aopp, a49])
        if done: break
        
    c49 = float(obs[seat]["farms"][seat]["money"])
    copp = float(obs[opp_seat]["farms"][opp_seat]["money"])
    margin = c49 - copp
    return {
        "seed": seed,
        "seat": seat,
        "opp": opp_name,
        "cash_v49": c49,
        "cash_opp": copp,
        "margin": margin,
        "win": c49 > copp,
        "loss": c49 < copp,
        "tie": c49 == copp
    }

if __name__ == "__main__":
    print("Running all 576 legs for V49 to extract near-loss and near-tie boundaries...")
    tasks = [(s, seat, opp) for opp in ALL_OPPONENTS for s in FRESH_SEEDS for seat in (0, 1)]

    with concurrent.futures.ProcessPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(run_leg, tasks))

    print(f"Completed {len(results)} legs.")

    # Categorize
    losses = [r for r in results if r["loss"]]
    wins = [r for r in results if r["win"]]
    ties = [r for r in results if r["tie"]]

    print(f"Total Wins: {len(wins)}, Losses: {len(losses)}, Ties: {len(ties)}")

    # Near win buckets (0-25, 25-50, 50-100, 100-250, 250-500, 500-1000)
    buckets = {
        "0_to_25": [r for r in wins if 0 < r["margin"] <= 25],
        "25_to_50": [r for r in wins if 25 < r["margin"] <= 50],
        "50_to_100": [r for r in wins if 50 < r["margin"] <= 100],
        "100_to_250": [r for r in wins if 100 < r["margin"] <= 250],
        "250_to_500": [r for r in wins if 250 < r["margin"] <= 500],
        "500_to_1000": [r for r in wins if 500 < r["margin"] <= 1000],
    }

    near_ties = {
        "abs_le_100": [r for r in results if abs(r["margin"]) <= 100],
        "abs_le_250": [r for r in results if abs(r["margin"]) <= 250],
        "abs_le_500": [r for r in results if abs(r["margin"]) <= 500],
        "abs_le_1000": [r for r in results if abs(r["margin"]) <= 1000],
    }

    summary = {
        "total_legs": len(results),
        "wins": len(wins),
        "losses": len(losses),
        "ties": len(ties),
        "loss_legs": losses,
        "near_win_buckets": {k: len(v) for k, v in buckets.items()},
        "near_tie_buckets": {k: len(v) for k, v in near_ties.items()},
        "detailed_near_ties": near_ties["abs_le_500"],
        "detailed_near_wins_under_500": [r for r in wins if r["margin"] <= 500]
    }

    with open("research/v56/analysis/NEAR_TIE_BOUNDARY.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("\nSummary of Near-Tie & Near-Win Boundaries:")
    print(f"  Losses: {len(losses)}")
    for l in losses:
        print(f"    Seed {l['seed']} Seat {l['seat']} vs {l['opp']}: Margin = ${l['margin']:+.2f}")
    print("  Near Wins:")
    for k, v in buckets.items():
        print(f"    Bucket {k}: {len(v)} games")
    print("  Near Ties (abs margin):")
    for k, v in near_ties.items():
        print(f"    Bucket {k}: {len(v)} games")
