# SPDX-License-Identifier: MIT
"""Kagriculture V34 A7 Decision Tracer.

Observationally instruments the protected A7 incumbent (candidates/v30_a7_standalone/main.py),
recording every decision step across development matches without altering behavior.
Generates: a7_decision_trace.jsonl
"""

from __future__ import annotations
import copy
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from kaggle_environments import make
from scripts.v32_common import load_agent
from candidates.v32_rlx2.opponents import load_league_opponent, LEAGUE_OPPONENTS

OUTPUT_TRACE_PATH = os.path.join(REPO_ROOT, "a7_decision_trace.jsonl")


def _get_shared_obs(env: Any, pos: int) -> Dict[str, Any]:
    obs = copy.deepcopy(env.steps[-1][pos]["observation"])
    for k in ("step", "market", "town", "day", "hour"):
        if k in env.steps[-1][0]["observation"] and k not in obs:
            obs[k] = env.steps[-1][0]["observation"][k]
    return obs


def _classify_phase(step: int) -> str:
    if step < 48:
        return "PHASE_0_OPENING_HIRE"
    elif step < 240:
        return "PHASE_1_EARLY_CROP_SCALING"
    elif step < 480:
        return "PHASE_2_MIDGAME_PRODUCTION"
    elif step < 680:
        return "PHASE_3_LATE_HARVEST_CONVERSION"
    else:
        return "PHASE_4_TERMINAL_LIQUIDATION"


def run_decision_trace(
    seeds: List[int],
    opponents: List[str],
    seats: Tuple[int, ...] = (0, 1),
    max_matches: int = 12,
    output_path: str = OUTPUT_TRACE_PATH,
) -> int:
    """Runs observational tracing on A7 across selected seed-opponent-seat matchups."""
    total_records = 0
    match_count = 0

    with open(output_path, "w", encoding="utf-8") as out_f:
        for seed in seeds:
            for opp_id in opponents:
                for seat in seats:
                    if match_count >= max_matches:
                        break

                    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
                    env.reset()

                    a7 = load_agent("E9_AST")
                    opp = load_league_opponent(opp_id)

                    cash_history: List[float] = []
                    price_history: List[Dict[str, float]] = []

                    step = 0
                    while not env.done:
                        obs_p = _get_shared_obs(env, seat)
                        obs_opp = _get_shared_obs(env, 1 - seat)

                        # Observational extraction BEFORE act
                        p_farm = (obs_p.get("farms", []) or [{}])[seat] if len(obs_p.get("farms", [])) > seat else {}
                        opp_farm = (obs_p.get("farms", []) or [{}])[1 - seat] if len(obs_p.get("farms", [])) > (1 - seat) else {}
                        p_private = obs_p.get("private", {}) or {}
                        mkt = obs_p.get("market", {}) or {}
                        prices = {k: float(v) for k, v in (mkt.get("prices", {}) or {}).items()}
                        inventory = {k: int(v) for k, v in (mkt.get("inventory", {}) or {}).items()}
                        town = obs_p.get("town", {}) or {}

                        current_cash = float(p_farm.get("money", 0.0) or 0.0)
                        cash_history.append(current_cash)
                        price_history.append(prices)

                        # Cash slope over last 4 steps
                        if len(cash_history) >= 5:
                            cash_slope = cash_history[-1] - cash_history[-5]
                        else:
                            cash_slope = 0.0

                        # Price movement over last 4 steps
                        recent_price_movement = {}
                        if len(price_history) >= 5:
                            for prod, pr in prices.items():
                                recent_price_movement[prod] = pr - price_history[-5].get(prod, pr)

                        # Crop state summary
                        tiles = p_farm.get("tiles", []) or []
                        planted_counts: Dict[str, int] = {}
                        unwatered = 0
                        ready_harvest = 0
                        weed_count = 0
                        for row in tiles:
                            for t in row:
                                if isinstance(t, dict):
                                    kind = t.get("kind")
                                    if kind == "PLANT":
                                        crop = t.get("crop", "UNKNOWN")
                                        planted_counts[crop] = planted_counts.get(crop, 0) + 1
                                        if not t.get("watered_today", False):
                                            unwatered += 1
                                        if int(t.get("yield_units", 0) or 0) > 0:
                                            ready_harvest += 1
                                    elif kind == "WEED":
                                        weed_count += 1

                        # Livestock state summary
                        shed = p_private.get("shed", {}) or {}
                        worker_positions = [p_farm.get("farmer", [0, 0])] + list(p_farm.get("hands", []) or [])

                        # Next A7 event projection
                        phase = _classify_phase(step)
                        terminal_distance = 719 - step

                        # Act bit-identically
                        act_p = a7.act(obs_p)
                        act_opp = opp(obs_opp)

                        # Event identification from intended action
                        has_market_order = bool(act_p.get("market"))
                        market_ops = [o[0] for o in (act_p.get("market") or []) if o]
                        if "SELL" in market_ops:
                            current_economic_event = "SELL_LOT"
                        elif "BUY_PRODUCT" in market_ops:
                            current_economic_event = "BUY_PRODUCT"
                        elif "BUY_SEED" in market_ops:
                            current_economic_event = "BUY_SEED"
                        elif "HIRE" in market_ops:
                            current_economic_event = "HIRE"
                        else:
                            current_economic_event = "NONE"

                        record = {
                            "match_id": f"seed_{seed}_opp_{opp_id}_seat_{seat}",
                            "seed": seed,
                            "opponent_id": opp_id,
                            "seat": seat,
                            "step": step,
                            "route_phase": phase,
                            "terminal_distance": terminal_distance,
                            "intended_action": {
                                "farmer": act_p.get("farmer", ["PASS"]),
                                "hands_count": len(act_p.get("hands", []) or []),
                                "market_orders": act_p.get("market", []),
                                "economic_event": current_economic_event,
                            },
                            "cash": current_cash,
                            "cash_slope_4": cash_slope,
                            "shed_inventory": shed,
                            "hand_inventories": p_private.get("inventories", []),
                            "crop_state": {
                                "planted_counts": planted_counts,
                                "unwatered_count": unwatered,
                                "ready_harvest_count": ready_harvest,
                                "weed_count": weed_count,
                            },
                            "worker_states": {
                                "active_workers": len(worker_positions),
                                "positions": worker_positions,
                            },
                            "land": {
                                "unlocked_quadrants": len(p_farm.get("unlocked_quadrants", []) or [1]),
                            },
                            "market_prices": prices,
                            "recent_price_movement": recent_price_movement,
                            "opponent_observable": {
                                "visible_hands": len(opp_farm.get("hands", []) or []),
                                "visible_quadrants": len(opp_farm.get("unlocked_quadrants", []) or [1]),
                                "visible_money": float(opp_farm.get("money", 0.0) or 0.0),
                            },
                            "shop_state": {
                                "unlocked_shops": town.get("unlocked_shops", []),
                            },
                        }

                        out_f.write(json.dumps(record) + "\n")
                        total_records += 1

                        if seat == 0:
                            env.step([act_p, act_opp])
                        else:
                            env.step([act_opp, act_p])
                        step += 1

                    match_count += 1
                    print(f"Traced match {match_count}/{max_matches}: Seed {seed}, vs {opp_id}, Seat {seat} -> {step} steps logged.")

    print(f"Total decision records written to {output_path}: {total_records}")
    return total_records


if __name__ == "__main__":
    # Run over representative development cohort
    dev_seeds = [249675, 249676, 249677]
    opps = ["E8_DMITRII", "E1_V22R1", "V54", "SYN_AGG"]
    run_decision_trace(dev_seeds, opps, seats=(0, 1), max_matches=10)
