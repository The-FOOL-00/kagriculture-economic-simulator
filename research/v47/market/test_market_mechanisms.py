#!/usr/bin/env python3
"""Parallel counterfactual market mechanism evaluation for Kagriculture V47.

Isolates:
1. V44_BASELINE
2. V47_C1_IMPACT: Impact-slot reordering (from 3009)
3. V47_C2_DEMAND_IMPACT: Demand-aware impact reordering (from 3009)
4. V47_C3_RIVAL_STOCK: Rival-stock exposure reordering (from 2945 _OR2)
5. V47_C5_MARKET_COMBO: Full combined elite market layer

Evaluates under exact simulation against 2945 in parallel across 8 processes.
Calculates:
- Head-to-head win rate, margin, cash
- Paired leg-for-leg Delta vs V44 baseline on identical seeds & seats
- 95% Confidence Interval for causal Delta
"""

from __future__ import annotations
import concurrent.futures
import copy
import json
import math
import os
import sys
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from candidates.v44_economic_portfolio.main import V44CandidateController

# 32 Clean dev seeds strictly outside holdouts (64 paired legs per candidate)
SEEDS = [249800 + i for i in range(32)]
PROTECTED_HOLDOUTS = [(214200, 214249), (340090, 340199), (249695, 249734)]

for s in SEEDS:
    for start, end in PROTECTED_HOLDOUTS:
        assert not (start <= s <= end), f"CRITICAL: Protected holdout seed {s} accessed!"

# --- 1.32.7 Market Parameter Definition ---
PRICE_FLOOR = 1
MARKET_PARAMS = {
    "WHEAT": (25, 10000, 400, "sqrt", 0.8, "log", 0.2),
    "CARROT": (35, 10000, 450, "hinge", 1.0, "sqrt", 0.7),
    "TOMATO": (60, 10000, 200, "hinge", 0.4, "sqrt", 0.6),
    "STRAWBERRY": (120, 10000, 100, "sqrt", 0.7, "linear", 1.6),
    "MELON": (250, 10000, 300, "log", 0.2, "sq", 3.6),
    "EGG": (50, 10000, 332, "hinge", 0.4, "log", 0.2),
    "MILK": (160, 10000, 122, "sqrt", 0.6, "linear", 1.6),
    "WOOL": (200, 10000, 105, "log", 0.2, "sq", 3.2),
    "FERTILIZER": (100, 10000, 200, "linear", 0.4, "linear", 0.4),
}

SHOP_PRODUCTS = {
    "BAKERY": ("EGG", "WHEAT"),
    "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"),
    "YARN_STORE": ("WOOL",),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"),
    "PET_CAFE": ("CARROT",),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
}


def _shape(name: str, value: float, scale: float) -> float:
    value = max(0.0, float(value))
    if name == "linear":
        return value
    if name == "sq":
        return value * value
    if name == "sqrt":
        return math.sqrt(value)
    if name == "log":
        return math.log1p(value)
    if name == "hinge":
        if scale <= 0:
            return value
        norm = value / scale
        return norm + 8.0 * max(0.0, norm - 1.0) ** 2
    return value


def get_market_price(item: str, inventory: int) -> int:
    base, eq, scale, b_f, b_t, a_f, a_t = MARKET_PARAMS[item]
    if inventory < eq:
        amp = b_t * base / _shape(b_f, scale, scale)
        price = base + amp * _shape(b_f, eq - inventory, scale)
    else:
        amp = a_t * base / _shape(a_f, scale, scale)
        price = base - amp * _shape(a_f, inventory - eq, scale)
    return max(PRICE_FLOOR, int(round(price)))


def is_sell(order) -> bool:
    return isinstance(order, (list, tuple)) and len(order) >= 3 and order[0] == "SELL" and order[1] in MARKET_PARAMS


# --- Mechanism 1: Impact-Slot Reordering (from 3009) ---
def impact_score(obs, order) -> float:
    if not is_sell(order):
        return float("-inf")
    item = str(order[1])
    try:
        qty = max(0, int(order[2]))
    except (TypeError, ValueError):
        return 0.0
    mkt = obs.get("market", {}) or {}
    inv = int((mkt.get("inventory", {}) or {}).get(item, 10000))
    p_now = float((mkt.get("prices", {}) or {}).get(item, get_market_price(item, inv)))
    p_later = float(get_market_price(item, inv + qty))
    return float(qty) * max(0.0, p_now - p_later)


def apply_impact_slots(obs, action) -> dict:
    if not isinstance(action, dict):
        return action
    mkt = list(action.get("market") or [])
    sells = [(impact_score(obs, o), -idx, copy.deepcopy(o)) for idx, o in enumerate(mkt) if is_sell(o)]
    if len(sells) < 2:
        return action
    sells.sort(reverse=True)
    ranked = iter(s[2] for s in sells)
    new_mkt = [next(ranked) if is_sell(o) else o for o in mkt]
    res = dict(action)
    res["market"] = new_mkt
    return res


# --- Mechanism 2: Demand-Aware Impact Reordering (from 3009) ---
def demand_adjusted_impact_score(obs, order, alpha: float = 0.5) -> float:
    score = impact_score(obs, order)
    if score <= 0 or not is_sell(order):
        return score
    item = str(order[1])
    qty = max(0, int(order[2]))
    mkt = obs.get("market", {}) or {}
    inv = int((mkt.get("inventory", {}) or {}).get(item, 10000))
    town = obs.get("town", {}) or {}
    shops = town.get("unlocked_shops", []) or []
    demand = 1.0  # base
    for s in shops:
        prods = SHOP_PRODUCTS.get(s, ())
        if item in prods:
            demand += 6.0 * (2 if len(prods) == 1 else 1)
    post_inv = inv + qty
    excess = max(0.0, post_inv - 10000)
    recovery_days = excess / max(0.25, demand)
    urgency = min(1.0, recovery_days / 10.0)
    return score * (1.0 + alpha * urgency)


def apply_demand_impact_slots(obs, action, alpha: float = 0.5) -> dict:
    if not isinstance(action, dict):
        return action
    mkt = list(action.get("market") or [])
    sells = [(demand_adjusted_impact_score(obs, o, alpha), -idx, copy.deepcopy(o)) for idx, o in enumerate(mkt) if is_sell(o)]
    if len(sells) < 2:
        return action
    sells.sort(reverse=True)
    ranked = iter(s[2] for s in sells)
    new_mkt = [next(ranked) if is_sell(o) else o for o in mkt]
    res = dict(action)
    res["market"] = new_mkt
    return res


# --- Mechanism 3: Rival-Stock Exposure Reordering (_OR2 from 2945) ---
class RivalTracker:
    def __init__(self, seat: int):
        self.seat = seat
        self.rival_seat = 1 - seat
        self.rival_stock = {k: 0 for k in MARKET_PARAMS}
        self.prev_tiles = {}
        self.last_step = -1

    def update(self, obs):
        step = int(obs.get("step", 0) or 0)
        if step == 0 or step <= self.last_step:
            self.rival_stock = {k: 0 for k in MARKET_PARAMS}
            self.prev_tiles = {}
        self.last_step = step

        rival_farm = obs["farms"][self.rival_seat]
        curr_tiles = {}
        for y, row in enumerate(rival_farm["tiles"]):
            for x, t in enumerate(row):
                if isinstance(t, dict):
                    if t.get("kind") == "PLANT" and t.get("crop"):
                        curr_tiles[(x, y)] = ("P", t["crop"], int(t.get("yield_units", 0)))
                    elif t.get("animal"):
                        curr_tiles[(x, y)] = ("A", t["animal"], int(t.get("yield_units", 0)))

        if self.prev_tiles:
            for pos, (kind, item, prev_yield) in self.prev_tiles.items():
                if prev_yield <= 0:
                    continue
                curr = curr_tiles.get(pos)
                got = 0
                if curr is None:
                    got = prev_yield
                elif curr[2] < prev_yield:
                    got = prev_yield - curr[2]
                if got > 0:
                    prod = {"GOOSE": "EGG", "COW": "MILK", "SHEEP": "WOOL"}.get(item, item)
                    if prod in self.rival_stock:
                        self.rival_stock[prod] += got

        self.prev_tiles = curr_tiles

    def get_exposure(self, obs, item: str, qty: int) -> float:
        if qty <= 0 or item not in MARKET_PARAMS:
            return 0.0
        mkt = obs.get("market", {}) or {}
        inv = int((mkt.get("inventory", {}) or {}).get(item, 10000))
        batch = min(10, self.rival_stock.get(item, 0))
        if batch <= 0:
            return 0.0
        p_base = sum(get_market_price(item, inv + j) for j in range(qty))
        p_exposed = sum(get_market_price(item, inv + batch + j) for j in range(qty))
        return float(max(0, p_base - p_exposed))


def apply_rival_stock_reorder(obs, action, tracker: RivalTracker) -> dict:
    if not isinstance(action, dict):
        return action
    mkt = list(action.get("market") or [])
    sells = []
    for idx, o in enumerate(mkt):
        if is_sell(o):
            exp = tracker.get_exposure(obs, o[1], int(o[2]))
            sells.append((exp, -idx, copy.deepcopy(o)))
    if len(sells) < 2:
        return action
    if any(s[0] > 0 for s in sells):
        sells.sort(reverse=True)
        ranked = iter(s[2] for s in sells)
        new_mkt = [next(ranked) if is_sell(o) else o for o in mkt]
        res = dict(action)
        res["market"] = new_mkt
        return res
    return action


# --- Candidate Builders ---
def build_candidate_fn(cand_name: str):
    if cand_name == "V44_BASELINE":
        ctrl = V44CandidateController()
        return lambda obs: ctrl.act(obs)
    elif cand_name == "V47_C1_IMPACT":
        ctrl = V44CandidateController()
        return lambda obs: apply_impact_slots(obs, ctrl.act(obs))
    elif cand_name == "V47_C2_DEMAND_IMPACT":
        ctrl = V44CandidateController()
        return lambda obs: apply_demand_impact_slots(obs, ctrl.act(obs), alpha=0.5)
    elif cand_name == "V47_C3_RIVAL_STOCK":
        ctrl = V44CandidateController()
        tracker = [None]
        def _act(obs):
            seat = int(obs.get("player", 0) or 0)
            step = int(obs.get("step", 0) or 0)
            if tracker[0] is None or step == 0:
                tracker[0] = RivalTracker(seat)
            tracker[0].update(obs)
            return apply_rival_stock_reorder(obs, ctrl.act(obs), tracker[0])
        return _act
    elif cand_name == "V47_C5_MARKET_COMBO":
        ctrl = V44CandidateController()
        tracker = [None]
        def _act(obs):
            seat = int(obs.get("player", 0) or 0)
            step = int(obs.get("step", 0) or 0)
            if tracker[0] is None or step == 0:
                tracker[0] = RivalTracker(seat)
            tracker[0].update(obs)
            act = ctrl.act(obs)
            act = apply_rival_stock_reorder(obs, act, tracker[0])
            act = apply_demand_impact_slots(obs, act, alpha=0.5)
            return act
        return _act
    else:
        raise ValueError(f"Unknown candidate {cand_name}")


def load_raw_agent(agent_path: str):
    import importlib.util
    spec = importlib.util.spec_from_file_location("agent_raw", agent_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.agent


def run_leg_task(args: Tuple[str, str, int, int]) -> Dict[str, Any]:
    cand_name, opp_path, seed, seat = args
    opp_seat = 1 - seat

    cand_act = build_candidate_fn(cand_name)
    opp_act = load_raw_agent(opp_path)

    sim = FastKagricultureSim(seed=seed)
    obs_list = sim.reset(seed=seed)

    cas = 0
    for step in range(719):
        obs_c = obs_list[seat]
        obs_o = obs_list[opp_seat]
        try:
            act_c = cand_act(obs_c)
        except Exception:
            act_c = {"farmer": ["PASS"], "hands": [], "market": []}
            cas += 1
        try:
            act_o = opp_act(obs_o)
        except Exception:
            act_o = {"farmer": ["PASS"], "hands": [], "market": []}

        actions = [act_c, act_o] if seat == 0 else [act_o, act_c]
        obs_list, rewards, done, info = sim.step(actions)

    cash_c = float(obs_list[seat]["farms"][seat]["money"])
    cash_o = float(obs_list[opp_seat]["farms"][opp_seat]["money"])
    return {
        "cand": cand_name,
        "seed": seed,
        "seat": seat,
        "cash_c": cash_c,
        "cash_o": cash_o,
        "margin": cash_c - cash_o,
        "win": 1 if cash_c > cash_o else (0.5 if cash_c == cash_o else 0),
        "casualties": cas,
    }


def main():
    t2945_path = os.path.join(REPO_ROOT, "research", "v47", "elite_corpus", "agents", "thomastschinkel_2945", "main.py")

    candidates = [
        "V44_BASELINE",
        "V47_C1_IMPACT",
        "V47_C2_DEMAND_IMPACT",
        "V47_C3_RIVAL_STOCK",
        "V47_C5_MARKET_COMBO",
    ]

    print(f"Executing parallel counterfactual market evaluations across {len(SEEDS)} seeds x 2 seats = {len(SEEDS)*2} legs per candidate...")

    all_cand_results = {}
    base_results_map = {}

    with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
        for cand_name in candidates:
            tasks = [(cand_name, t2945_path, s, seat) for s in SEEDS for seat in (0, 1)]
            futures = [executor.submit(run_leg_task, t) for t in tasks]
            results = [f.result() for f in futures]
            all_cand_results[cand_name] = results

            # Aggregate stats
            n = len(results)
            wins = sum(r["win"] for r in results)
            win_rate = wins / n
            margins = [r["margin"] for r in results]
            cash_c = [r["cash_c"] for r in results]
            cash_o = [r["cash_o"] for r in results]
            cas = sum(r["casualties"] for r in results)

            mean_margin = float(np.mean(margins))
            median_margin = float(np.median(margins))
            p10_margin = float(np.percentile(margins, 10))
            mean_cash_c = float(np.mean(cash_c))
            mean_cash_o = float(np.mean(cash_o))

            if cand_name == "V44_BASELINE":
                base_results_map = {(r["seed"], r["seat"]): r for r in results}
                print(f"[{cand_name}] WR={win_rate*100:.1f}%, MeanMargin={mean_margin:+.1f}, Cash=${mean_cash_c:.0f}, OppCash=${mean_cash_o:.0f}, Cas={cas}")
            else:
                # Calculate paired deltas vs V44_BASELINE
                deltas = []
                flips_up = 0
                flips_down = 0
                for r in results:
                    base_r = base_results_map[(r["seed"], r["seat"])]
                    d = r["cash_c"] - base_r["cash_c"]
                    deltas.append(d)
                    if r["win"] > base_r["win"]:
                        flips_up += 1
                    elif r["win"] < base_r["win"]:
                        flips_down += 1

                mean_delta = float(np.mean(deltas))
                median_delta = float(np.median(deltas))
                ci95_low = mean_delta - 1.96 * float(np.std(deltas, ddof=1) / np.sqrt(n))
                ci95_high = mean_delta + 1.96 * float(np.std(deltas, ddof=1) / np.sqrt(n))

                print(f"[{cand_name}] WR={win_rate*100:.1f}%, Margin={mean_margin:+.1f}, MeanDelta={mean_delta:+.1f} (95% CI [{ci95_low:+.1f}, {ci95_high:+.1f}]), MedDelta={median_delta:+.1f}, Flips=(+{flips_up}/-{flips_down}), Cas={cas}")

    out_file = os.path.join(REPO_ROOT, "research", "v47", "market", "parallel_market_benchmark.json")
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w") as f:
        json.dump(all_cand_results, f, indent=2)

    print(f"\nCompleted! Saved to {out_file}.")


if __name__ == "__main__":
    main()
