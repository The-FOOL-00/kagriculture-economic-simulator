# SPDX-License-Identifier: MIT
"""V45 Market & Opponent Observability Dataset Collector.

Generates a large, clean, legally observable market history dataset across diverse
lineage agents (V44, V43, V42, V39, V35) and league opponents (E8_DMITRII, E2_A7, E0_V3, SYN_AGG).
Records 100% legal public-state and our-private variables at every step.
Strictly excludes all hidden opponent state (no opponent shed, no hidden seeds).
Outputs: research/v45/artifacts/opponent_market_history.jsonl
"""

from __future__ import annotations
import copy
import json
import os
import sys
import time
from typing import Any, Callable, Dict, List
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v45.governance import assert_seed_safe, assert_protected_artifacts
from research.v40.env.fast_sim import FastKagricultureSim
from candidates.v35_a7_opening.main import V35OpeningController
from candidates.v39_live_targeted.main import V39TargetedController
from candidates.v42_alpha_residual.main import V42CandidateController
from candidates.v43_compositional_alpha.main import V43CandidateController
from candidates.v44_economic_portfolio.main import V44CandidateController
from candidates.v32_rlx2.opponents import load_league_opponent

# 16 clean non-holdout seeds
DATASET_SEEDS = [
    249635, 249636, 249637, 249638,
    249645, 249646, 249647, 249648,
    249655, 249656, 249657, 249658,
    249685, 249686, 249687, 249688
]

OPPONENTS = ["E8_DMITRII", "E2_A7", "E0_V3", "SYN_AGG"]

LINEAGE_AGENTS = {
    "V44": lambda: V44CandidateController(),
    "V43": lambda: V43CandidateController(),
    "V42": lambda: V42CandidateController(),
    "V39": lambda: V39TargetedController(),
    "V35": lambda: V35OpeningController(),
}

COMMODITIES = ["CARROT", "EGG", "FERTILIZER", "MELON", "MILK", "STRAWBERRY", "TOMATO", "WHEAT", "WOOL"]

# Town shop definitions from engine
TOWN_SHOPS_DEF = {
    "BAKERY": ["WHEAT", "EGG"],
    "DAIRY": ["MILK"],
    "WOOL_MILL": ["WOOL"],
    "SALAD_BAR": ["TOMATO", "CARROT"],
    "SMOOTHIE_STAND": ["STRAWBERRY", "MELON"],
    "YARN_STORE": ["WOOL"],
    "PET_CAFE": ["CARROT"],
}
TOWN_CENTER_PRODUCTS = ["WHEAT", "TOMATO", "CARROT", "STRAWBERRY", "MELON", "MILK", "WOOL", "EGG"]


def _act(agent: Any, obs: Dict[str, Any]) -> Dict[str, Any]:
    if hasattr(agent, "act") and callable(getattr(agent, "act")):
        return agent.act(obs)
    return agent(obs)


def collect_market_dataset(num_games_target: int = 128):
    print("=" * 80)
    print("V45 PHASE 1: OBSERVABILITY & MARKET DATASET COLLECTION")
    print("=" * 80)
    
    assert_protected_artifacts()
    for s in DATASET_SEEDS:
        assert_seed_safe(s)
        
    opp_masters = {opp_id: load_league_opponent(opp_id) for opp_id in OPPONENTS}
    
    out_dir = os.path.join(REPO_ROOT, "research", "v45", "artifacts")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "opponent_market_history.jsonl")
    
    # We will construct game matchups
    # 16 seeds x 4 opponents x 2 seats = 128 complete games
    # We rotate lineage agents across seeds: V44 (seeds 0..3), V43 (seeds 4..7), V42 (seeds 8..11), V39/V35 (seeds 12..15)
    
    games_plan = []
    lineage_keys = list(LINEAGE_AGENTS.keys())
    for s_idx, seed in enumerate(DATASET_SEEDS):
        our_agent_name = lineage_keys[s_idx % len(lineage_keys)]
        for opp_id in OPPONENTS:
            for seat in [0, 1]:
                games_plan.append((seed, our_agent_name, opp_id, seat))
                
    games_plan = games_plan[:num_games_target]
    print(f"Scheduled {len(games_plan)} complete games for recording (target: {num_games_target})...")
    
    t0 = time.perf_counter()
    total_steps_recorded = 0
    
    # Open jsonl file
    with open(out_file, "w", encoding="utf-8") as f_out:
        for g_idx, (seed, our_agent_name, opp_id, seat) in enumerate(games_plan):
            sim = FastKagricultureSim(seed=seed)
            our_agent = LINEAGE_AGENTS[our_agent_name]()
            opp_agent = copy.deepcopy(opp_masters[opp_id])
            
            obs0, obs1 = sim.reset(seed=seed)
            our_obs = obs0 if seat == 0 else obs1
            opp_obs = obs1 if seat == 0 else obs0
            
            # State tracking buffers for velocity
            prev_prices = {}
            price_hist_4 = [] # rolling 4-step prices
            prev_inv = {}
            prev_opp_cash = None
            opp_cash_hist_4 = []
            
            while not sim.done:
                step = int(our_obs.get("step", 0) or 0)
                
                # 1. Capture current legal market observation
                mkt = our_obs.get("market", {}) or {}
                prices = {k: int(v) for k, v in (mkt.get("prices", {}) or {}).items()}
                inv = {k: int(v) for k, v in (mkt.get("inventory", {}) or {}).items()}
                town = our_obs.get("town", {}) or {}
                unlocked_shops = list(town.get("unlocked_shops", []) or [])
                
                # 2. Our financial & asset state
                our_farm = our_obs.get("farms", [{}, {}])[seat]
                our_cash = float(our_farm.get("money", 0.0) or 0.0)
                our_private = our_obs.get("private", {}) or {}
                our_shed = {k: int(v) for k, v in (our_private.get("shed", {}) or {}).items() if k in COMMODITIES}
                our_hands_count = len(our_farm.get("hands", []) or [])
                our_quads = len(our_farm.get("unlocked_quadrants", []) or [])
                
                # 3. Observable public opponent state
                opp_farm = our_obs.get("farms", [{}, {}])[1 - seat]
                opp_cash = float(opp_farm.get("money", 0.0) or 0.0)
                opp_hands_count = len(opp_farm.get("hands", []) or [])
                opp_quads = len(opp_farm.get("unlocked_quadrants", []) or [])
                
                # Count visible crops on opponent grid
                opp_tiles = opp_farm.get("tiles", [])
                opp_visible_crops = 0
                opp_visible_animals = 0
                for row in opp_tiles:
                    for tile in row:
                        if isinstance(tile, dict):
                            if "crop" in tile:
                                opp_visible_crops += 1
                            if "animal" in tile:
                                opp_visible_animals += 1
                                
                # 4. Trailing velocities (1-step and 4-step)
                price_vel_1 = {}
                price_vel_4 = {}
                observed_market_sales = {}
                
                if prev_prices:
                    for c in COMMODITIES:
                        price_vel_1[c] = prices.get(c, 0) - prev_prices.get(c, 0)
                        p4 = price_hist_4[0].get(c, prices.get(c, 0)) if price_hist_4 else prev_prices.get(c, 0)
                        price_vel_4[c] = prices.get(c, 0) - p4
                else:
                    for c in COMMODITIES:
                        price_vel_1[c] = 0
                        price_vel_4[c] = 0
                        
                # Update price history rolling window (up to 4 steps)
                price_hist_4.append(dict(prices))
                if len(price_hist_4) > 4:
                    price_hist_4.pop(0)
                prev_prices = dict(prices)
                
                # Opponent cash velocity
                opp_cash_vel_1 = 0.0 if prev_opp_cash is None else (opp_cash - prev_opp_cash)
                c4 = opp_cash_hist_4[0] if opp_cash_hist_4 else (prev_opp_cash if prev_opp_cash is not None else opp_cash)
                opp_cash_vel_4 = opp_cash - c4
                
                opp_cash_hist_4.append(opp_cash)
                if len(opp_cash_hist_4) > 4:
                    opp_cash_hist_4.pop(0)
                prev_opp_cash = opp_cash
                
                # Inferred market sales from delta inventory
                # At step % 4 == 0, shops consume. At step % 24 == 0, town center consumes.
                town_drain = {c: 0 for c in COMMODITIES}
                if step > 0 and step % 4 == 0:
                    for shop in unlocked_shops:
                        if shop in TOWN_SHOPS_DEF:
                            prods = TOWN_SHOPS_DEF[shop]
                            mult = 2 if len(prods) == 1 else 1
                            for p in prods:
                                town_drain[p] += mult
                if step > 0 and step % 24 == 0:
                    for p in TOWN_CENTER_PRODUCTS:
                        town_drain[p] += 1
                        
                if prev_inv:
                    for c in COMMODITIES:
                        # net change in inventory = Inflow - Outflow = Total_Sales - Town_Drain
                        # => Inferred_Total_Sales = (I_t - I_{t-1}) + Town_Drain
                        delta_inv = inv.get(c, 0) - prev_inv.get(c, 0)
                        inferred_total_sales = max(0, delta_inv + town_drain[c])
                        observed_market_sales[c] = inferred_total_sales
                else:
                    for c in COMMODITIES:
                        observed_market_sales[c] = 0
                prev_inv = dict(inv)
                
                # 5. Extract our own market actions taken
                act_our = _act(our_agent, our_obs)
                act_opp = opp_agent(opp_obs)
                
                our_market_orders = act_our.get("market", []) if isinstance(act_our, dict) else []
                our_sales = {}
                for o in our_market_orders:
                    if len(o) >= 3 and o[0] == "SELL":
                        our_sales[o[1]] = our_sales.get(o[1], 0) + int(o[2])
                        
                # Assemble record
                record = {
                    "game_id": g_idx,
                    "seed": seed,
                    "seat": seat,
                    "step": step,
                    "our_agent": our_agent_name,
                    "opp_id": opp_id,
                    "prices": prices,
                    "inventory": inv,
                    "unlocked_shops": unlocked_shops,
                    "our_cash": our_cash,
                    "our_shed": our_shed,
                    "our_hands": our_hands_count,
                    "our_quads": our_quads,
                    "opp_cash": opp_cash,
                    "opp_hands": opp_hands_count,
                    "opp_quads": opp_quads,
                    "opp_crops": opp_visible_crops,
                    "opp_animals": opp_visible_animals,
                    "price_vel_1": price_vel_1,
                    "price_vel_4": price_vel_4,
                    "opp_cash_vel_1": round(opp_cash_vel_1, 2),
                    "opp_cash_vel_4": round(opp_cash_vel_4, 2),
                    "observed_market_sales": observed_market_sales,
                    "our_sales": our_sales,
                }
                
                f_out.write(json.dumps(record) + "\n")
                total_steps_recorded += 1
                
                # Step simulation
                actions = [act_our, act_opp] if seat == 0 else [act_opp, act_our]
                [obs0, obs1], _, _, _ = sim.step(actions)
                our_obs = obs0 if seat == 0 else obs1
                opp_obs = obs1 if seat == 0 else obs0
                
            if (g_idx + 1) % 16 == 0 or (g_idx + 1) == len(games_plan):
                elapsed = time.perf_counter() - t0
                print(f"  Processed {g_idx + 1}/{len(games_plan)} games ({total_steps_recorded} steps recorded, {elapsed:.1f}s)...")
                
    dur = time.perf_counter() - t0
    file_size_mb = os.path.getsize(out_file) / (1024 * 1024)
    print(f"\nPhase 1 Dataset Collection Complete!")
    print(f"Total Games: {len(games_plan)} | Total Steps: {total_steps_recorded}")
    print(f"Dataset File: {out_file} ({file_size_mb:.2f} MB)")
    print(f"Duration: {dur:.1f}s (Speed: {total_steps_recorded / dur:.1f} steps/s)")
    return out_file, total_steps_recorded


if __name__ == "__main__":
    collect_market_dataset()
