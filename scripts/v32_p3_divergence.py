# SPDX-License-Identifier: MIT
"""V32 P3 first-divergence forensics: BC actions vs all 4 teachers, same states.

For each leg: roll out the BC policy; at every step query the 4 frozen
teachers on the learner's exact observation; record per-teacher first
divergence (step, BC action, teacher action, differing slots/params) and the
terminal cash. Quarantine enforced. No training.

Writes results/v32_p3_divergence.jsonl.
"""

import argparse
import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

TEACHERS = ["E0_V3", "E2_A7", "E6_W72", "E7_W2015"]


def _lite(act):
    return {"farmer": (act or {}).get("farmer"),
            "hands": (act or {}).get("hands"),
            "market": (act or {}).get("market")}


def _diff_slots(bc, ex):
    """Coarse slot-level diff classification (§22 taxonomy support)."""
    diffs = []
    if (bc.get("farmer") or ["PASS"]) != (ex.get("farmer") or ["PASS"]):
        b, e = (bc.get("farmer") or ["PASS"]), (ex.get("farmer") or ["PASS"])
        b0, e0 = (b[0] if b else None), (e[0] if e else None)
        diffs.append("farmer-op:%s-vs-%s" % (b0, e0) if b0 != e0
                     else "farmer-param")
    bh, eh = bc.get("hands") or [], ex.get("hands") or []
    for j in range(max(len(bh), len(eh))):
        b, e = (bh[j] if j < len(bh) else ["PASS"]), \
               (eh[j] if j < len(eh) else ["PASS"])
        if (b or ["PASS"]) != (e or ["PASS"]):
            b0 = b[0] if b else None
            e0 = e[0] if e else None
            diffs.append("hand%d-op:%s-vs-%s" % (j, b0, e0) if b0 != e0
                         else "hand%d-param" % j)
    bm, em = bc.get("market") or [], ex.get("market") or []
    for s in range(max(len(bm), len(em))):
        b, e = (bm[s] if s < len(bm) else []), (em[s] if s < len(em) else [])
        if (b or []) != (e or []):
            b0 = b[0] if b else "NOOP"
            e0 = e[0] if e else "NOOP"
            diffs.append("mkt%d-op:%s-vs-%s" % (s, b0, e0) if b0 != e0
                         else "mkt%d-param" % s)
    return diffs


def run_leg(ckpt, seed, opp, seat, teachers, deterministic=True):
    import numpy as np
    import torch
    from kaggle_environments import make
    from v32_common import check_seed_allowed, load_agent
    from v32.p2.essentials import essentialize
    from v32.p2.features import Normalizer
    from v32.p3.models import P3Policy
    from v32.p3.rollout import Predictor
    check_seed_allowed(seed)
    try:
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass  # parallel work already started; single-process anyway
    norm = Normalizer.from_json(json.load(open(os.path.join(
        REPO_ROOT, "results", "v32_p2_norm.json"))))
    model = P3Policy(157, 12)
    d = np.load(os.path.join(REPO_ROOT, ckpt), allow_pickle=True)
    model.load_state_dict({k: torch.tensor(v) for k, v in d.items()
                           if k != "meta"})
    model.eval()
    pred = Predictor(model, norm)
    pred.reset()
    tach = {t: load_agent(t) for t in teachers}
    opp_ag = load_agent(opp)
    div = {t: None for t in teachers}
    nov = None  # first step BC differs from ALL teachers
    cash = []
    n_steps = [0]

    def learner_act(obs, cfg=None):
        nonlocal nov
        pr = pred.step(essentialize(obs, seat), deterministic=deterministic)
        bc = _lite(pr["action"])
        ex_acts = {}
        for t, ag in tach.items():
            try:
                ex_acts[t] = _lite(ag.act(obs, cfg))
            except Exception as e:  # noqa: BLE001 (frozen experts vary)
                ex_acts[t] = {"error": str(e)[:100]}
        for t in teachers:
            if div[t] is None and ex_acts[t] != bc:
                div[t] = {"step": n_steps[0], "bc": bc, "expert": ex_acts[t],
                          "slots": _diff_slots(bc, ex_acts[t])}
        if nov is None and all(ex_acts[t] != bc for t in teachers):
            nov = {"step": n_steps[0], "bc": bc,
                   "experts": ex_acts}
        n_steps[0] += 1
        return pr["action"]

    def opp_act(obs, cfg=None):
        return opp_ag.act(obs, cfg)

    env = make("kaggriculture", configuration={"seed": seed})
    agents = [learner_act, opp_act] if seat == 0 else [opp_act, learner_act]
    env.run(agents)
    for st in env.steps:
        f = st[seat]["observation"]["farms"][seat]
        cash.append(round(float(f["money"]), 1))
    return {"seed": seed, "opp": opp, "seat": seat,
            "my_cash": float(env.steps[-1][seat]["reward"]),
            "opp_cash": float(env.steps[-1][1 - seat]["reward"]),
            "n_steps": n_steps[0], "first_div": div, "first_novel": nov,
            "cash": cash}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--out", default="results/v32_p3_divergence.jsonl")
    ap.add_argument("--seeds", required=True)
    ap.add_argument("--opp", required=True)
    ap.add_argument("--seats", default="0")
    ap.add_argument("--teachers", default=",".join(TEACHERS))
    args = ap.parse_args()
    from v32_common import assert_frozen, check_seed_allowed
    assert_frozen()
    lo, hi = [int(x) for x in args.seeds.split(":")]
    for s in range(lo, hi + 1):
        check_seed_allowed(s)
    teachers = args.teachers.split(",")
    out = open(os.path.join(REPO_ROOT, args.out), "a", buffering=1)
    for s in range(lo, hi + 1):
        for seat in [int(x) for x in args.seats.split(",")]:
            rec = run_leg(args.ckpt, s, args.opp, seat, teachers)
            out.write(json.dumps(rec) + "\n")
            fd = {t: (v["step"] if v else None)
                  for t, v in rec["first_div"].items()}
            print("seed=%d seat=%d cash=%.0f vs %.0f div=%s novel=%s"
                  % (s, seat, rec["my_cash"], rec["opp_cash"], fd,
                     rec["first_novel"]["step"] if rec["first_novel"] else None),
                  flush=True)
    out.close()


if __name__ == "__main__":
    main()
