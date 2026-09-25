# SPDX-License-Identifier: MIT
"""V32 P7 first-24-step paired trace (Section 31).

Policy (masked ckpt) vs live E2_A7 replay, same seed/opp/seat, full episodes
via env.run. Records per step 0..24: farmer action, position, money, inv0,
shed, hand count, phase. Writes JSON + prints the side-by-side table.
"""

import argparse
import copy
import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

import numpy as np
import torch
from kaggle_environments import make

from v32_common import assert_frozen, check_seed_allowed, load_agent
from v32.p2.essentials import essentialize
from v32.p2.features import Normalizer
from v32.p3.models import P3Policy
import v32_p6_eval_screen as P6E
from v32.p7.phase import phase_name


def run(ckpt, seed, opp_id, seat, use_teacher):
    norm = Normalizer.from_json(json.load(
        open(os.path.join(REPO_ROOT, "results", "v32_p2_norm.json"))))
    model = None
    if not use_teacher:
        model = P3Policy(157, 12)
        d = np.load(ckpt, allow_pickle=True)
        model.load_state_dict({k: torch.tensor(v) for k, v in d.items()
                               if k != "meta"})
        model.eval()
    pred = P6E.MaskedPredictor(model, norm, apply_mask=True) \
        if model is not None else None
    teacher = load_agent("E2_A7")
    opp = load_agent(opp_id)
    if pred is not None:
        pred.reset()
    recs = []

    def me(obs, cfg=None):
        ess = essentialize(obs, seat)
        a = teacher.act(obs, cfg) if use_teacher else \
            pred.step(ess, deterministic=True)["action"]
        recs.append({"step": int(ess.get("step", 0)),
                     "farmer_act": a.get("farmer"),
                     "farmer_pos": ess["farmer"],
                     "money": ess["money"],
                     "hands": len(ess.get("hands", []) or []),
                     "shed": {k: v for k, v in (ess.get("shed", {}) or {}).items() if v},
                     "inv0": (ess.get("inv", []) or [{}])[0],
                     "phase": phase_name(ess)})
        return copy.deepcopy(a)

    def oppa(obs, cfg=None):
        return opp.act(obs, cfg)

    env = make("kaggriculture", configuration={"seed": seed})
    env.run([me, oppa] if seat == 0 else [oppa, me])
    return {"cash": float(env.steps[-1][seat]["reward"]), "recs": recs[:25]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=249675)
    ap.add_argument("--opp", default="E0_V3")
    ap.add_argument("--seat", type=int, default=0)
    args = ap.parse_args()
    assert_frozen()
    check_seed_allowed(args.seed)
    t = run(args.ckpt, args.seed, args.opp, args.seat, True)
    p = run(args.ckpt, args.seed, args.opp, args.seat, False)
    with open(args.out, "w") as f:
        json.dump({"tag": args.tag, "seed": args.seed, "opp": args.opp,
                   "seat": args.seat, "teacher": t, "policy": p}, f)
    print(f"teacher_cash=${t['cash']:,.0f} policy_cash=${p['cash']:,.0f}")
    print(f"{'st':<3} {'teacher':<18} {'policy':<18} {'tpos':<7} {'ppos':<7} "
          f"{'t$':<7} {'p$':<7} {'tph':<9} {'pph':<9} m")
    for tr, pr in zip(t["recs"], p["recs"]):
        m = "==" if tr["farmer_act"] == pr["farmer_act"] and \
            tr["farmer_pos"] == pr["farmer_pos"] else "!="
        print(f"{tr['step']:<3} {str(tr['farmer_act']):<18} "
              f"{str(pr['farmer_act']):<18} {str(tr['farmer_pos']):<7} "
              f"{str(pr['farmer_pos']):<7} {tr['money']:<7.0f} "
              f"{pr['money']:<7.0f} {tr['phase']:<9} {pr['phase']:<9} {m}")


if __name__ == "__main__":
    main()
