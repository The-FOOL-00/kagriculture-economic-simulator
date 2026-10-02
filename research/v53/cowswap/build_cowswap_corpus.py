#!/usr/bin/env python3
"""Build COWSWAP Activation Corpus and Counterfactual Regime Table (V53 Section 5).

Instruments all COWSWAP activations across discovery seeds, historical loss seeds,
and sample validation seeds, running same-world full-terminal counterfactuals
(with vs without COWSWAP) to classify each activation as GOOD, BAD, or NEUTRAL.
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

HISTORICAL_LOSS_SEEDS = [250416, 250428, 250433, 250436, 250439, 250497]
DISCOVERY_SEEDS = [250400 + i for i in range(28)]
ALL_CORPUS_SEEDS = sorted(list(set(HISTORICAL_LOSS_SEEDS + DISCOVERY_SEEDS)))


def run_cowswap_match(seed: int, seat: int, allow_cowswap: bool) -> Tuple[float, float, Dict[str, Any]]:
    opp_seat = 1 - seat
    sim = FastKagricultureSim(seed=seed)
    obs = sim.reset(seed=seed)
    
    opp = v44_mod.agent
    orig_options = v49_mod._CS_OPTIONS
    
    recorded_state = {}

    for step in range(719):
        # Apply cowswap permission
        if not allow_cowswap:
            v49_mod._CS_OPTIONS = ()
        else:
            v49_mod._CS_OPTIONS = orig_options

        a_cand = v49_mod.agent(obs[seat])
        v49_mod._CS_OPTIONS = orig_options
        a_opp = opp(obs[opp_seat])

        # Record observable state at step 150 (the primary buy step)
        if step == 150 and allow_cowswap:
            farm = obs[seat]["farms"][seat]
            mkt = obs[seat]["market"]
            town = obs[seat].get("town", {})
            shops = list(town.get("unlocked_shops") or [])
            
            cows_count = sum(1 for row in farm["tiles"] for t in row if isinstance(t, dict) and t.get("animal") == "COW")
            geese_count = sum(1 for row in farm["tiles"] for t in row if isinstance(t, dict) and t.get("animal") == "GOOSE")
            coops_count = sum(1 for row in farm["tiles"] for t in row if isinstance(t, dict) and t.get("kind") == "COOP")
            pastures_count = sum(1 for row in farm["tiles"] for t in row if isinstance(t, dict) and t.get("kind") == "PASTURE")

            recorded_state = {
                "seed": seed,
                "seat": seat,
                "step": step,
                "money": float(farm.get("money", 0)),
                "unlocked_shops": shops,
                "shop_count": len(shops),
                "has_milk_shop": any(s in ("PIZZA_SHOP", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP") for s in shops),
                "has_egg_shop": any(s in ("BAKERY", "BRUNCH_SPOT") for s in shops),
                "has_yarn_store": ("YARN_STORE" in shops),
                "milk_price": float((mkt.get("prices") or {}).get("MILK", 0)),
                "egg_price": float((mkt.get("prices") or {}).get("EGG", 0)),
                "milk_inventory": int((mkt.get("inventory") or {}).get("MILK", 0)),
                "egg_inventory": int((mkt.get("inventory") or {}).get("EGG", 0)),
                "current_cows": cows_count,
                "current_geese": geese_count,
                "coops": coops_count,
                "pastures": pastures_count,
                "market_orders": a_cand.get("market") or [],
                "swapped_to_goose": any(len(o) >= 3 and o[0] == "BUY_ANIMAL" and o[1] == "GOOSE" for o in (a_cand.get("market") or [])),
            }

        obs, _, _, _ = sim.step([a_cand, a_opp] if seat == 0 else [a_opp, a_cand])

    cash_cand = float(obs[seat]["farms"][seat]["money"])
    cash_opp = float(obs[opp_seat]["farms"][opp_seat]["money"])
    return cash_cand, cash_opp, recorded_state


def main():
    print(f"Building COWSWAP Activation Corpus across {len(ALL_CORPUS_SEEDS)} seeds x 2 seats...")
    corpus = []
    
    for s in ALL_CORPUS_SEEDS:
        for seat in (0, 1):
            # 1. Run with native COWSWAP
            cash_with, cash_opp_with, state = run_cowswap_match(s, seat, allow_cowswap=True)
            
            # Check if COWSWAP actually triggered at step 150
            if state.get("swapped_to_goose"):
                # 2. Run without COWSWAP (counterfactual baseline)
                cash_without, cash_opp_without, _ = run_cowswap_match(s, seat, allow_cowswap=False)
                
                delta = cash_with - cash_without
                opp_delta = cash_with - cash_opp_with
                won_with = cash_with > cash_opp_with
                won_without = cash_without > cash_opp_without
                
                if delta > 50.0:
                    classification = "GOOD_COWSWAP"
                elif delta < -50.0:
                    classification = "BAD_COWSWAP"
                else:
                    classification = "NEUTRAL_COWSWAP"

                entry = {
                    "seed": s,
                    "seat": seat,
                    "state": state,
                    "cash_with_cowswap": cash_with,
                    "cash_without_cowswap": cash_without,
                    "cowswap_net_delta": delta,
                    "won_with_cowswap": won_with,
                    "won_without_cowswap": won_without,
                    "terminal_margin_vs_v44": opp_delta,
                    "classification": classification,
                }
                corpus.append(entry)
                print(f"  Seed {s}:{seat} -> {classification} (Delta={delta:+,.0f}, With=${cash_with:,.0f}, W/O=${cash_without:,.0f}) | Shops: {state['unlocked_shops']}")

    out_json = os.path.join(REPO_ROOT, "research", "v53", "cowswap", "cowswap_activation_corpus.json")
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(corpus, f, indent=2)
    print(f"\nSaved {len(corpus)} activation records to {out_json}")


if __name__ == "__main__":
    main()
