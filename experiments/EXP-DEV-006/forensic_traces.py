# SPDX-License-Identifier: MIT
"""EXP-DEV-006 post-hoc forensic tracer (consumed seeds ONLY: 248002/248007/248009/248029).

Replays the 4 analytically decisive fresh-cohort seeds (2 wins, 2 guard-saves)
x 2 arms x 2 seats = 16 games on the validated port, capturing money
trajectories every 12 steps. No new seeds, no treatment change, no resampling.
Output: forensic_traces.json
"""
import os
import sys
import json
import importlib.util

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PORT_DIR = os.path.join(BASE_DIR, "experiments", "EXP-DEV-006_HORIZON_KILLTEST", "port")
sys.path.insert(0, PORT_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

import kagsim_py as kagsim
from dev_005_confirmed_shop_scheduler import Dev005ConfirmedShopScheduler
from dev_006_horizon_guard_scheduler import Dev006HorizonGuardScheduler

BASELINE_PATH = os.path.join(BASE_DIR, "candidates", "compiled_v54_plus_residual.py")
EXP_DIR = os.path.abspath(os.path.dirname(__file__))

KEY_SEEDS = (248002, 248007, 248009, 248029)
ARMS = {"DEV005": Dev005ConfirmedShopScheduler, "DEV006": Dev006HorizonGuardScheduler}


def load_baseline(name: str):
    spec = importlib.util.spec_from_file_location(name, BASELINE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def trace_game(seed: int, cand_cls, cand_seat: int):
    assert seed in KEY_SEEDS, f"forensics restricted to key seeds, got {seed}"
    g = kagsim.Game(seed)
    cand = cand_cls(seat=cand_seat, seed=seed)
    base = load_baseline(f"ftrace_{cand_cls.__name__}_s{seed}_c{cand_seat}")
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
        "cand_money_traj": [snap[s][cand_seat] for s in sorted(snap)],
        "base_money_traj": [snap[s][1 - cand_seat] for s in sorted(snap)],
        "cand_reward": float(g.reward(cand_seat)),
        "base_reward": float(g.reward(1 - cand_seat)),
        "final_money": [round(float(of0["farms"][0]["money"]), 1),
                        round(float(of1["farms"][1]["money"]), 1)],
    }


def main():
    out = {}
    for seed in KEY_SEEDS:
        out[str(seed)] = {}
        for arm, cls in ARMS.items():
            for seat in (0, 1):
                out[str(seed)][f"{arm}_seat{seat}"] = trace_game(seed, cls, seat)
                print(f"traced seed {seed} {arm} seat{seat}", flush=True)
    with open(os.path.join(EXP_DIR, "forensic_traces.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print("saved forensic_traces.json")


if __name__ == "__main__":
    main()
