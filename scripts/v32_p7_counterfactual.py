# SPDX-License-Identifier: MIT
"""V32 P7 causal counterfactual (Section 33).

For the first new divergence step D under the P7 policy (default 3):
  A: policy trajectory (free run).
  B: live-teacher FULL joint action forced at step D only, policy thereafter.
  C: live-teacher FULL joint actions forced for steps 0..H, policy thereafter.

Forcing uses LIVE E2_A7 queries on the current observation (never a tape
import, never recorded literals). All states are simulator-generated full
episodes via env.run. Default cohort: seeds 249675-249677 x E0_V3 x seats 0,1
(6 legs x 3 branches), mirroring the P6 counterfactual scale.
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


def run_branch(ckpt, seed, opp_id, seat, mode, div_step, horizon):
    norm = Normalizer.from_json(json.load(
        open(os.path.join(REPO_ROOT, "results", "v32_p2_norm.json"))))
    model = P3Policy(157, 12)
    d = np.load(ckpt, allow_pickle=True)
    model.load_state_dict({k: torch.tensor(v) for k, v in d.items()
                           if k != "meta"})
    model.eval()
    pred = P6E.MaskedPredictor(model, norm, apply_mask=True)
    teacher = load_agent("E2_A7")
    opp = load_agent(opp_id)
    pred.reset()
    trace = []

    def learner_act(obs, cfg=None):
        t = int(obs.get("step", 0))
        force = (mode == "B" and t == div_step) or \
                (mode == "C" and t <= horizon)
        if force:
            a = copy.deepcopy(teacher.act(obs, cfg))
            # keep predictor recurrence honest: feed the EXECUTED action
            ess = essentialize(obs, seat)
            pred.fb.update(ess, pred.prev_act)
            pred.prev_act = a
        else:
            a = pred.step(essentialize(obs, seat),
                          deterministic=True)["action"]
        ess = essentialize(obs, seat)
        trace.append({"step": t, "farmer_pos": ess["farmer"],
                      "money": ess["money"], "forced": force,
                      "farmer": a.get("farmer"),
                      "hands": copy.deepcopy(a.get("hands") or [])[:2],
                      "market": copy.deepcopy(a.get("market") or [])[:2]})
        return a

    def opp_act(obs, cfg=None):
        return opp.act(obs, cfg)

    env = make("kaggriculture", configuration={"seed": seed})
    agents = [learner_act, opp_act] if seat == 0 else [opp_act, learner_act]
    env.run(agents)
    cash = float(env.steps[-1][seat]["reward"])
    return {"cash": cash, "trace": trace[:13]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--div_step", type=int, default=3)
    ap.add_argument("--horizon", type=int, default=4)
    ap.add_argument("--seeds", default="249675:249677")
    ap.add_argument("--opp", default="E0_V3")
    ap.add_argument("--seats", default="0,1")
    args = ap.parse_args()
    assert_frozen()
    lo, hi = [int(x) for x in args.seeds.split(":")]
    for s in range(lo, hi + 1):
        check_seed_allowed(s)
    out = []
    for s in range(lo, hi + 1):
        for seat in [int(x) for x in args.seats.split(",")]:
            row = {"seed": s, "seat": seat, "opp": args.opp,
                   "div_step": args.div_step, "horizon": args.horizon}
            for mode in ("A", "B", "C"):
                r = run_branch(args.ckpt, s, args.opp, seat, mode,
                               args.div_step, args.horizon)
                row[mode] = r
                print(f"seed={s} seat={seat} {mode}: cash=${r['cash']:,.0f} "
                      f"forced={[t['step'] for t in r['trace'] if t['forced']]}",
                      flush=True)
            out.append(row)
    with open(args.out, "w") as f:
        json.dump({"tag": args.tag, "rows": out}, f)
    print(f"wrote {args.out}", flush=True)


if __name__ == "__main__":
    main()
