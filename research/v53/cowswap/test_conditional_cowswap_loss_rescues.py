#!/usr/bin/env python3
"""Evaluate Surgical Conditional COWSWAP Policies C1-C6 on Historical Losses (V53 Section 6 & 7).

Tests:
- C0: V49 Baseline (unmodified)
- C_off: Global COWSWAP Suppression
- C1: Disable when egg shop exists AND no milk shop exists
- C2: Disable when egg price < milk price / 2.5
- C3: Disable when town has no milk shop and egg price < 150
- C4: Disable when egg shop exists, no milk shop, and yarn store is absent
- C5: Disable only when planned cow is replaced by coop construction
- C6: Composite causal gate: egg shop exists AND no milk shop AND planned cow purchase replaced AND milk price >= egg price * 1.5
"""

import copy
import json
import os
import sys
import time
from typing import Any, Dict, List, Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

HISTORICAL_LOSSES = [
    {"loss_id": "L01", "seed": 250416, "seat": 0, "nominal_loss": -716.0},
    {"loss_id": "L02", "seed": 250416, "seat": 1, "nominal_loss": -716.0},
    {"loss_id": "L03", "seed": 250428, "seat": 0, "nominal_loss": -31.0},
    {"loss_id": "L04", "seed": 250428, "seat": 1, "nominal_loss": -160.0},
    {"loss_id": "L05", "seed": 250433, "seat": 0, "nominal_loss": -470.0},
    {"loss_id": "L06", "seed": 250433, "seat": 1, "nominal_loss": -470.0},
    {"loss_id": "L07", "seed": 250436, "seat": 0, "nominal_loss": -1405.0},
    {"loss_id": "L08", "seed": 250436, "seat": 1, "nominal_loss": -1405.0},
    {"loss_id": "L09", "seed": 250439, "seat": 0, "nominal_loss": -1407.0},
    {"loss_id": "L10", "seed": 250439, "seat": 1, "nominal_loss": -1407.0},
    {"loss_id": "L11", "seed": 250497, "seat": 1, "nominal_loss": -901.0},
]


def should_suppress_cowswap(policy: str, obs: Dict[str, Any]) -> bool:
    if policy == "C0":
        return False
    if policy == "C_off":
        return True

    town = obs.get("town") or {}
    shops = list(town.get("unlocked_shops") or [])
    mkt = obs.get("market") or {}
    prices = mkt.get("prices") or {}
    egg_price = float(prices.get("EGG", 50.0))
    milk_price = float(prices.get("MILK", 160.0))

    has_egg_shop = any(s in ("BAKERY", "BRUNCH_SPOT") for s in shops)
    has_milk_shop = any(s in ("PIZZA_SHOP", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP") for s in shops)
    has_yarn = "YARN_STORE" in shops

    if policy == "C1":
        # Disable when egg shop exists AND no milk shop exists
        return has_egg_shop and not has_milk_shop

    elif policy == "C2":
        # Disable when egg price < milk price / 2.5
        return (egg_price < milk_price / 2.5)

    elif policy == "C3":
        # Disable when no milk shop and egg price < 150
        return (not has_milk_shop) and (egg_price < 150.0)

    elif policy == "C4":
        # Disable when egg shop exists, no milk shop, and yarn absent
        return has_egg_shop and (not has_milk_shop) and (not has_yarn)

    elif policy == "C5":
        # Disable when planned cow is replaced by coop construction
        # In Route 0 at step 150, cows are planned for pasture tiles. If no coop exists, coop is built.
        seat = int(obs["player"])
        farm = obs["farms"][seat]
        coop_count = sum(1 for row in farm["tiles"] for t in row if isinstance(t, dict) and t.get("kind") == "COOP")
        return coop_count == 0 and has_egg_shop and not has_milk_shop

    elif policy == "C6":
        # Composite causal gate:
        # Egg demand exists, no milk demand support, milk opportunity exceeds egg opportunity, and egg price is not super-premium
        return has_egg_shop and (not has_milk_shop) and (milk_price >= egg_price * 1.5) and (egg_price < 220.0)

    return False


def make_policy_agent(policy: str):
    def _agent(obs, cfg=None):
        orig_options = v49_mod._CS_OPTIONS
        suppress = should_suppress_cowswap(policy, obs)
        if suppress:
            v49_mod._CS_OPTIONS = ()
        else:
            v49_mod._CS_OPTIONS = orig_options

        act = v49_mod.agent(obs, cfg)
        v49_mod._CS_OPTIONS = orig_options
        return act

    return _agent


def run_loss_match(seed: int, seat: int, policy: str) -> Tuple[float, float, float, bool]:
    opp_seat = 1 - seat
    sim = FastKagricultureSim(seed=seed)
    obs = sim.reset(seed=seed)
    
    agent = make_policy_agent(policy)
    opp = v44_mod.agent

    for step in range(719):
        a_cand = agent(obs[seat])
        a_opp = opp(obs[opp_seat])
        obs, _, _, _ = sim.step([a_cand, a_opp] if seat == 0 else [a_opp, a_cand])

    c_cand = float(obs[seat]["farms"][seat]["money"])
    c_opp = float(obs[opp_seat]["farms"][opp_seat]["money"])
    diff = c_cand - c_opp
    win = diff > 0.0
    return c_cand, c_opp, diff, win


def main():
    print("=" * 80)
    print("V53 SECTION 7: CONDITIONAL COWSWAP POLICIES C1-C6 ON 11 HISTORICAL LOSSES")
    print("=" * 80)

    policies = ["C0", "C_off", "C1", "C2", "C3", "C4", "C5", "C6"]
    results = []

    for item in HISTORICAL_LOSSES:
        lid = item["loss_id"]
        s = item["seed"]
        seat = item["seat"]
        nom = item["nominal_loss"]
        
        row = {"loss_id": lid, "seed": s, "seat": seat, "nominal": nom, "policies": {}}
        print(f"\n{lid} (Seed {s}:{seat}, Base={nom:+.0f}):")

        for p in policies:
            c, co, diff, win = run_loss_match(s, seat, p)
            status = "RESCUED" if win else ("WORSE" if diff < nom - 50 else ("BETTER" if diff > nom + 50 else "SAME"))
            row["policies"][p] = {
                "cash": c,
                "cash_opp": co,
                "delta": diff,
                "win": win,
                "status": status,
            }
            print(f"  {p:6s}: Delta={diff:+8.0f} ({status:7s}) | P0=${c:,.0f} vs P1=${co:,.0f}")

        results.append(row)

    out_file = os.path.join(REPO_ROOT, "research", "v53", "cowswap", "cowswap_loss_counterfactuals.json")
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved loss counterfactual results to {out_file}")


if __name__ == "__main__":
    main()
