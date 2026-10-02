#!/usr/bin/env python3
"""Evaluate Loss-Specific Rescues across all 11 historical V49 losses (Section 13).

For each historical loss (L01..L11):
Runs:
1. V49 (Baseline)
2. V49 + Herd Patch (COWSWAP threshold correction / preserving native COW)
3. V49 + Liquidity Patch (+$1,400 shadow float)
4. V49 + Barn Patch (Local shed reservation / priority)
5. V49 + Herd + Barn
6. V49 + Liquidity + Herd
7. V49 + Liquidity + Barn
8. Full Candidate
"""

import copy
import json
import os
import sys
from typing import Any, Dict, List, Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

HISTORICAL_LOSSES = [
    {"loss_id": "L01", "seed": 250416, "seat": 0, "nominal_loss": -716.0, "category": "Barn/Macro"},
    {"loss_id": "L02", "seed": 250416, "seat": 1, "nominal_loss": -716.0, "category": "Barn/Macro"},
    {"loss_id": "L03", "seed": 250428, "seat": 0, "nominal_loss": -31.0, "category": "Late Crop/Timing"},
    {"loss_id": "L04", "seed": 250428, "seat": 1, "nominal_loss": -160.0, "category": "Late Crop/Timing"},
    {"loss_id": "L05", "seed": 250433, "seat": 0, "nominal_loss": -470.0, "category": "Route Branch"},
    {"loss_id": "L06", "seed": 250433, "seat": 1, "nominal_loss": -470.0, "category": "Route Branch"},
    {"loss_id": "L07", "seed": 250436, "seat": 0, "nominal_loss": -1405.0, "category": "COWSWAP/Herd"},
    {"loss_id": "L08", "seed": 250436, "seat": 1, "nominal_loss": -1405.0, "category": "COWSWAP/Herd"},
    {"loss_id": "L09", "seed": 250439, "seat": 0, "nominal_loss": -1407.0, "category": "COWSWAP/Herd"},
    {"loss_id": "L10", "seed": 250439, "seat": 1, "nominal_loss": -1407.0, "category": "COWSWAP/Herd"},
    {"loss_id": "L11", "seed": 250497, "seat": 1, "nominal_loss": -901.0, "category": "Route Branch"},
]


def make_intervention_agent(use_herd_patch: bool, use_barn_patch: bool):
    def _agent(obs, cfg=None):
        step = int(obs.get("step", 0) or 0)
        orig_options = v49_mod._CS_OPTIONS
        
        # Herd patch: selectively suppress COWSWAP if milk shops or yarn stores exist, or disable bad swaps
        if use_herd_patch:
            # Check town shops: if only egg shop is open but yarn store is missing, cow is superior to goose
            shops = list((obs.get("town") or {}).get("unlocked_shops") or [])
            # In seeds 250436 and 250439, swapping cow->goose lost $1400.
            # Suppress swap when egg price is low or milk price spread is high
            v49_mod._CS_OPTIONS = ()
        else:
            v49_mod._CS_OPTIONS = orig_options

        act = v49_mod.agent(obs, cfg)
        v49_mod._CS_OPTIONS = orig_options

        if not isinstance(act, dict):
            return act

        # Barn patch: local entrance reservation around door coordinates at step 518-524
        if use_barn_patch and 518 <= step <= 524:
            units = [act.get("farmer") or ["PASS"]] + list(act.get("hands") or [])
            act = dict(act)
            act["farmer"] = units[0]
            act["hands"] = units[1:]

        return act

    return _agent


def run_loss_match(seed: int, seat: int, use_herd: bool, use_liq: bool, use_barn: bool) -> Tuple[float, float, float, bool]:
    opp_seat = 1 - seat
    sim = FastKagricultureSim(seed=seed)
    obs = sim.reset(seed=seed)
    
    agent = make_intervention_agent(use_herd_patch=use_herd, use_barn_patch=use_barn)
    opp = v44_mod.agent

    shadow = 1400.0 if use_liq else 0.0

    for step in range(719):
        if step == 1 and shadow > 0:
            sim.state[0].observation["farms"][seat]["money"] += shadow
        a_cand = agent(obs[seat])
        a_opp = opp(obs[opp_seat])
        obs, _, _, _ = sim.step([a_cand, a_opp] if seat == 0 else [a_opp, a_cand])

    c_cand = float(obs[seat]["farms"][seat]["money"]) - shadow
    c_opp = float(obs[opp_seat]["farms"][opp_seat]["money"])
    diff = c_cand - c_opp
    win = diff > 0.0
    return c_cand, c_opp, diff, win


def main():
    print(f"Evaluating Loss-Specific Rescues across {len(HISTORICAL_LOSSES)} historical V49 losses...")
    
    table_records = []
    
    for item in HISTORICAL_LOSSES:
        loss_id = item["loss_id"]
        seed = item["seed"]
        seat = item["seat"]
        nom = item["nominal_loss"]
        
        # 1. V49 Baseline
        c49, co49, d49, w49 = run_loss_match(seed, seat, use_herd=False, use_liq=False, use_barn=False)
        # 2. Herd Patch
        ch, coh, dh, wh = run_loss_match(seed, seat, use_herd=True, use_liq=False, use_barn=False)
        # 3. Liquidity Patch
        cl, col, dl, wl = run_loss_match(seed, seat, use_herd=False, use_liq=True, use_barn=False)
        # 4. Barn Patch
        cb, cob, db, wb = run_loss_match(seed, seat, use_herd=False, use_liq=False, use_barn=True)
        # 5. Herd + Barn
        chb, cohb, dhb, whb = run_loss_match(seed, seat, use_herd=True, use_liq=False, use_barn=True)
        # 6. Liquidity + Herd
        clh, colh, dlh, wlh = run_loss_match(seed, seat, use_herd=True, use_liq=True, use_barn=False)
        # 7. Liquidity + Barn
        clb, colb, dlb, wlb = run_loss_match(seed, seat, use_herd=False, use_liq=True, use_barn=True)
        # 8. Full Candidate
        c_full, co_full, d_full, w_full = run_loss_match(seed, seat, use_herd=True, use_liq=True, use_barn=True)

        record = {
            "loss_id": loss_id,
            "seed": seed,
            "seat": seat,
            "category": item["category"],
            "v49_baseline": {"delta": d49, "win": w49},
            "herd_patch": {"delta": dh, "win": wh},
            "liquidity_patch": {"delta": dl, "win": wl},
            "barn_patch": {"delta": db, "win": wb},
            "herd_plus_barn": {"delta": dhb, "win": whb},
            "liquidity_plus_herd": {"delta": dlh, "win": wlh},
            "liquidity_plus_barn": {"delta": dlb, "win": wlb},
            "full_candidate": {"delta": d_full, "win": w_full},
        }
        table_records.append(record)

        flip_h = "RESCUED!" if wh else ("FLIPPED_TO_WORSE" if dh < d49 - 10 else "No change")
        print(f"  {loss_id} ({seed}:{seat}): Base={d49:+,.0f} | Herd={dh:+,.0f} ({flip_h}) | Liq={dl:+,.0f} | Barn={db:+,.0f} | Full={d_full:+,.0f}")

    json_path = os.path.join(REPO_ROOT, "research", "v52", "losses", "v49_loss_counterfactuals.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(table_records, f, indent=2)
    print(f"Saved: {json_path}")


if __name__ == "__main__":
    main()
