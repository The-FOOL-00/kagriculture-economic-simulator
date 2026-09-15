# SPDX-License-Identifier: MIT
"""EXP-DEV-006 QUALIFICATION post-hoc forensic tracer (consumed qual seeds ONLY).

Replays analytically decisive Qualification seeds (every non-tie + every guard-fired seed)
x 2 arms x 2 seats on the validated port, capturing money trajectories every 12 steps plus
terminal inventory/liquidity snapshots. No new seeds, no treatment change, no resampling.
KEY_SEEDS is filled AFTER all 50 Qualification seeds complete, from the frozen results.
Output: QUALIFICATION_FORENSIC_TRACES.json
"""
import os
import sys
import json
import importlib.util

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
PORT_DIR = os.path.join(BASE_DIR, "experiments", "EXP-DEV-006_HORIZON_KILLTEST", "port")
sys.path.insert(0, PORT_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

import kagsim_py as kagsim
from dev_005_confirmed_shop_scheduler import Dev005ConfirmedShopScheduler
from dev_006_horizon_guard_scheduler import Dev006HorizonGuardScheduler

BASELINE_PATH = os.path.join(BASE_DIR, "candidates", "compiled_v54_plus_residual.py")
EXP_DIR = os.path.abspath(os.path.dirname(__file__))

# Filled post-execution from QUALIFICATION_PAIRED_DELTAS.csv (non-tie + guard-fired seeds only).
# Qualification result: 3 non-tie seeds (50059/50069/50091, all wins), 0 guard-fired seeds.
KEY_SEEDS = (50059, 50069, 50091)

ARMS = {"DEV005": Dev005ConfirmedShopScheduler, "DEV006": Dev006HorizonGuardScheduler}


def load_baseline(name: str):
    spec = importlib.util.spec_from_file_location(name, BASELINE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def farm_snapshot(farm: dict) -> dict:
    out = {}
    for k in ("money", "workers", "cows", "sheep", "chickens", "geese",
              "wheat", "corn", "carrot", "melon", "strawberry",
              "feed", "fertilizer", "manure", "milk", "eggs", "wool",
              "yarn", "cheese", "smoothie", "shop_level"):
        if k in farm:
            v = farm[k]
            out[k] = round(float(v), 2) if isinstance(v, (int, float)) else str(v)[:120]
    return out


def trace_game(seed: int, cand_cls, cand_seat: int):
    assert seed in KEY_SEEDS, f"forensics restricted to key qual seeds, got {seed}"
    assert 50050 <= seed <= 50099, f"seed {seed} outside Qualification cohort"
    g = kagsim.Game(seed)
    cand = cand_cls(seat=cand_seat, seed=seed)
    base = load_baseline(f"qftrace_{cand_cls.__name__}_s{seed}_c{cand_seat}")
    snap = {}
    step = 0
    while not g.done:
        o0 = g.observe(0)
        o1 = g.observe(1)
        if step % 12 == 0:
            snap[step] = [round(float(o0["farms"][0]["money"]), 1),
                          round(float(o1["farms"][1]["money"]), 1)]
        if cand_seat == 0:
            g.step(cand.act(o0), base.agent(o1))
        else:
            g.step(base.agent(o0), cand.act(o1))
        step += 1
    of0 = g.observe(0)
    of1 = g.observe(1)
    return {
        "snap_steps": sorted(snap),
        "cand_money_traj": [snap[s][cand_seat] for s in sorted(snap)],
        "base_money_traj": [snap[s][1 - cand_seat] for s in sorted(snap)],
        "cand_reward": float(g.reward(cand_seat)),
        "base_reward": float(g.reward(1 - cand_seat)),
        "terminal_farm_cand": farm_snapshot(of0["farms"][cand_seat] if cand_seat == 0 else of1["farms"][cand_seat]),
        "terminal_farm_base": farm_snapshot(of1["farms"][1 - cand_seat] if cand_seat == 0 else of0["farms"][1 - cand_seat]),
        "active_plan": getattr(cand, "active_plan", None),
    }


def main():
    assert len(KEY_SEEDS) > 0, "KEY_SEEDS must be filled post-execution before tracing"
    out = {}
    for seed in KEY_SEEDS:
        out[str(seed)] = {}
        for arm, cls in ARMS.items():
            for seat in (0, 1):
                out[str(seed)][f"{arm}_seat{seat}"] = trace_game(seed, cls, seat)
                print(f"traced seed {seed} {arm} seat{seat}", flush=True)
    with open(os.path.join(EXP_DIR, "QUALIFICATION_FORENSIC_TRACES.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print("saved QUALIFICATION_FORENSIC_TRACES.json")


if __name__ == "__main__":
    main()
