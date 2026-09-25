# SPDX-License-Identifier: MIT
"""V32 P7 closed-loop screen: learner full episode + paired teacher reference.

Per leg (seed, opp, seat):
  1. Learner full episode via env.run (MaskedPredictor, same inference path as
     scripts/v32_p6_eval_screen.py) recording opening actions 0..8, hires,
     terminal cash, win.
  2. Paired E2_A7 reference: 25-step truncated rollout (v32.p7.rollout,
     proven env.run-equivalent) with the teacher in the learner seat vs the
     same opponent/seed.
  3. Prefix metrics: prefix-exact-match (farmer + full, H=4/8), first
     action/state/economic divergence, state-distance trajectory, opening-macro
     survival against canonical milestones (V32_P7_PREFIX_DATASET.md).

Teacher reference uses recorded-canonical macro only as milestone definitions;
divergence compares against the LIVE replayed teacher trace (same seed/opp).
"""

import argparse
import copy
import json
import os
import sys
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from v32_common import assert_frozen, check_seed_allowed, load_agent  # noqa: E402
from v32.p2.essentials import essentialize  # noqa: E402
from v32.p2.features import Normalizer  # noqa: E402
from v32.p3.models import P3Policy  # noqa: E402
from v32.p7.metrics import (first_divergence, hire_count,  # noqa: E402
                            opening_macro_survival, prefix_exact_match,
                            wash_order_correct, wash_shape)
from v32.p7.state import state_distance  # noqa: E402
import v32_p6_eval_screen as P6E  # noqa: E402
from v32.p7.rollout import truncated_rollout  # noqa: E402

_W = {}


def _milestones():
    return [
        {"step": 0, "name": "wash_complete",
         "check": lambda e, a: wash_shape(a.get("market"))},
        {"step": 0, "name": "farmer_pass@0",
         "check": lambda e, a: (a.get("farmer") or ["?"]) == ["PASS"]},
        {"step": 1, "name": "north@1",
         "check": lambda e, a: (a.get("farmer") or ["?"]) == ["NORTH"]},
        {"step": 1, "name": "hires5@1",
         "check": lambda e, a: hire_count(a.get("market")) == 5},
        {"step": 2, "name": "south@2",
         "check": lambda e, a: (a.get("farmer") or ["?"]) == ["SOUTH"]},
        {"step": 2, "name": "shed_stocked@2",
         "check": lambda e, a: ((e.get("shed", {}) or {}).get("COW", 0) >= 2
                                and (e.get("shed", {}) or {}).get("SHEEP", 0) >= 2)},
        {"step": 3, "name": "pickup_sheep@3",
         "check": lambda e, a: (a.get("farmer") or ["?"])[:2] == ["PICKUP", "SHEEP"]},
        {"step": 3, "name": "farmer_at_shed@3",
         "check": lambda e, a: list((e.get("farmer") or [])[:2]) == [4, 4]},
        {"step": 4, "name": "pickup_wheat@4",
         "check": lambda e, a: (a.get("farmer") or ["?"])[:2] == ["PICKUP", "WHEAT"]},
        {"step": 5, "name": "north@5",
         "check": lambda e, a: (a.get("farmer") or ["?"]) == ["NORTH"]},
        {"step": 6, "name": "west@6",
         "check": lambda e, a: (a.get("farmer") or ["?"]) == ["WEST"]},
        {"step": 7, "name": "build_pasture@7",
         "check": lambda e, a: (a.get("farmer") or ["?"]) == ["BUILD_PASTURE"]},
        {"step": 8, "name": "place_sheep@8",
         "check": lambda e, a: (a.get("farmer") or ["?"])[:2] == ["PLACE", "SHEEP"]},
    ]


MILESTONES = _milestones()


def _worker_init(ckpt_path, norm_json):
    import torch as _t
    _t.set_num_threads(1)
    _t.set_num_interop_threads(1)
    _W["model"] = P3Policy(157, 12)
    d = np.load(ckpt_path, allow_pickle=True)
    _W["model"].load_state_dict({k: _t.tensor(v) for k, v in d.items()
                                 if k != "meta"})
    _W["model"].eval()
    _W["pred"] = P6E.MaskedPredictor(_W["model"], Normalizer.from_json(norm_json),
                                     apply_mask=True)
    _W["nonce"] = uuid.uuid4().hex


def _run_one(spec):
    from kaggle_environments import make
    check_seed_allowed(spec["seed"])
    ag = load_agent(spec["opp"])
    pred = _W["pred"]
    make_fn = lambda s: make("kaggriculture", configuration={"seed": s})  # noqa: E731

    # 1. learner full episode
    env = make_fn(spec["seed"])
    pred.reset()
    steps = []

    def learner_act(obs, cfg=None):
        ess = essentialize(obs, spec["seat"])
        pr = pred.step(ess, deterministic=True)
        steps.append({"step": int(ess.get("step", 0)),
                      "ess": copy.deepcopy(ess),
                      "action": copy.deepcopy(pr["action"])})
        return pr["action"]

    def opp_act(obs, cfg=None):
        return ag.act(obs, cfg)

    agents = [learner_act, opp_act] if spec["seat"] == 0 else [opp_act, learner_act]
    t0 = time.time()
    env.run(agents)
    dur = time.time() - t0
    mine = float(env.steps[-1][spec["seat"]]["reward"])
    theirs = float(env.steps[-1][1 - spec["seat"]]["reward"])

    # 2. paired teacher reference (25 steps, teacher in learner seat)
    teacher = load_agent("E2_A7")
    oppc = load_agent(spec["opp"])
    tagents = [teacher, oppc] if spec["seat"] == 0 else [oppc, teacher]
    ttr, _ = truncated_rollout(make_fn, spec["seed"], tagents, 24,
                               trace_seat=spec["seat"], ess_fn=essentialize)
    teacher_trace = [{"step": r["step"], "ess": r["ess"],
                      "action": r["actions"][spec["seat"]]} for r in ttr]

    # 3. metrics
    p_acts = [s["action"] for s in steps]
    t_acts = [s["action"] for s in teacher_trace]
    div = first_divergence(teacher_trace, steps)
    sd = [state_distance(teacher_trace[t]["ess"], steps[t]["ess"])["total"]
          for t in range(min(9, len(steps), len(teacher_trace)))]
    macro = opening_macro_survival(
        [{"step": s["step"], "ess": s["ess"], "action": s["action"]}
         for s in steps[:9]], MILESTONES)

    a0 = p_acts[0] if p_acts else {}
    a1 = p_acts[1] if len(p_acts) > 1 else {}
    a2 = p_acts[2] if len(p_acts) > 2 else {}
    a3 = p_acts[3] if len(p_acts) > 3 else {}
    f = lambda a: (a.get("farmer") or ["PASS"])  # noqa: E731
    ops = [f(a)[0] if isinstance(f(a), list) and f(a) else "?" for a in p_acts[:9]]
    return {
        "key": f"V32P7EV:{spec['tag']}:{spec['opp']}:{spec['seed']}:{spec['seat']}",
        "tag": spec["tag"], "seed": spec["seed"], "opp": spec["opp"],
        "seat": spec["seat"], "my_cash": mine, "opp_cash": theirs,
        "win": 1.0 if mine > theirs else (0.0 if mine < theirs else 0.5),
        "duration_sec": dur, "n_steps": len(steps),
        "step0_wash": wash_shape(a0.get("market")),
        "step0_wash_order": wash_order_correct(a0.get("market")),
        "step0_pass": f(a0) == ["PASS"],
        "step1_north": f(a1) == ["NORTH"],
        "step1_hires": hire_count(a1.get("market")),
        "step2_op": f(a2)[0] if f(a2) else "?",
        "step2_south": f(a2) == ["SOUTH"],
        "step3_op": f(a3),
        "step3_pickup_sheep": f(a3)[:2] == ["PICKUP", "SHEEP"],
        "farmer_ops_0_8": ops,
        "pem4_farmer": prefix_exact_match(t_acts, p_acts, 4, "farmer"),
        "pem4_full": prefix_exact_match(t_acts, p_acts, 4, "full"),
        "pem8_farmer": prefix_exact_match(t_acts, p_acts, 8, "farmer"),
        "pem8_full": prefix_exact_match(t_acts, p_acts, 8, "full"),
        "t_act_farmer": div["t_act_farmer"], "t_act_full": div["t_act_full"],
        "t_state": div["t_state"], "t_pos": div["t_pos"],
        "t_econ": div["t_econ"],
        "state_dist_0_8": sd,
        "macro_passed": macro["passed"],
        "macro_reached": macro["reached"],
        "macro_failed_at": macro["failed_at"],
    }


def summarize(all_res):
    cashes = [r["my_cash"] for r in all_res]
    wins = [r["win"] for r in all_res]
    taf = [r["t_act_farmer"] if r["t_act_farmer"] is not None else 999
           for r in all_res]
    tst = [r["t_state"] if r["t_state"] is not None else 999 for r in all_res]
    tps = [r["t_pos"] if r["t_pos"] is not None else 999 for r in all_res]
    tec = [r["t_econ"] if r["t_econ"] is not None else 999 for r in all_res]
    return {
        "n": len(all_res),
        "wash": float(np.mean([r["step0_wash"] for r in all_res])),
        "wash_order": float(np.mean([r["step0_wash_order"] for r in all_res])),
        "pass": float(np.mean([r["step0_pass"] for r in all_res])),
        "north": float(np.mean([r["step1_north"] for r in all_res])),
        "hires_mean": float(np.mean([r["step1_hires"] for r in all_res])),
        "south": float(np.mean([r["step2_south"] for r in all_res])),
        "pickup3": float(np.mean([r["step3_pickup_sheep"] for r in all_res])),
        "pem4_farmer": float(np.mean([r["pem4_farmer"] for r in all_res])),
        "pem4_full": float(np.mean([r["pem4_full"] for r in all_res])),
        "pem8_farmer": float(np.mean([r["pem8_farmer"] for r in all_res])),
        "pem8_full": float(np.mean([r["pem8_full"] for r in all_res])),
        "t_act_med": float(np.median(taf)),
        "t_state_med": float(np.median(tst)),
        "t_pos_med": float(np.median(tps)),
        "t_econ_med": float(np.median(tec)),
        "macro_pass": float(np.mean([r["macro_passed"] for r in all_res])),
        "cash_mean": float(np.mean(cashes)),
        "cash_med": float(np.median(cashes)),
        "cash_std": float(np.std(cashes)),
        "cash_min": float(np.min(cashes)),
        "cash_max": float(np.max(cashes)),
        "win_rate": float(np.mean(wins)),
        "wins": int(sum(1 for w in wins if w == 1.0)),
        "worst5": float(np.percentile(cashes, 5)),
        "worst1": float(np.percentile(cashes, 1)),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seeds", default="249675:249684")
    ap.add_argument("--opps", default="E0_V3,E1_V22R1,E2_A7,E3_V25P3,E6_W72,E7_W2015")
    ap.add_argument("--seats", default="0,1")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()

    assert_frozen()
    lo, hi = [int(x) for x in args.seeds.split(":")]
    for s in range(lo, hi + 1):
        check_seed_allowed(s)

    specs = [{"tag": args.tag, "seed": s, "opp": o, "seat": seat}
             for s in range(lo, hi + 1) for o in args.opps.split(",")
             for seat in [int(x) for x in args.seats.split(",")]]

    norm = json.load(open(os.path.join(REPO_ROOT, "results", "v32_p2_norm.json")))
    print(f"V32 P7 Screen {args.tag}: {len(specs)} legs -> {args.out}", flush=True)

    done = set()
    if os.path.exists(args.out):
        with open(args.out) as f:
            for line in f:
                if line.strip():
                    try:
                        done.add(json.loads(line.strip())["key"])
                    except Exception:
                        pass
    todo = [s for s in specs
            if f"V32P7EV:{s['tag']}:{s['opp']}:{s['seed']}:{s['seat']}" not in done]
    print(f"Legs to run: {len(todo)} ({len(done)} cached)", flush=True)

    if todo:
        out_f = open(args.out, "a", buffering=1)
        with ProcessPoolExecutor(max_workers=args.workers,
                                 initializer=_worker_init,
                                 initargs=(args.ckpt, norm)) as ex:
            futs = {ex.submit(_run_one, s): s for s in todo}
            n = 0
            for fut in as_completed(futs):
                res = fut.result()
                out_f.write(json.dumps(res) + "\n")
                n += 1
                if n % 10 == 0 or n == len(todo):
                    print(f"  {n}/{len(todo)} cash=${res['my_cash']:,.0f} "
                          f"S3={res['step3_op']} div={res['t_act_farmer']}",
                          flush=True)
        out_f.close()

    all_res = [json.loads(line) for line in open(args.out) if line.strip()]
    s = summarize(all_res)
    print("=" * 64)
    print(f"=== V32 P7 SCREEN: {args.tag} (n={s['n']}) ===")
    for k in ("wash", "wash_order", "pass", "north", "south", "pickup3",
              "pem4_farmer", "pem4_full", "pem8_farmer", "pem8_full",
              "macro_pass"):
        print(f"{k:12s} {s[k]*100:6.1f}%")
    print(f"hires_mean   {s['hires_mean']:.2f}")
    print(f"t_act_med    {s['t_act_med']:.0f}  t_state_med {s['t_state_med']:.0f} "
          f"t_pos_med {s['t_pos_med']:.0f} t_econ_med {s['t_econ_med']:.0f}")
    print(f"cash mean ${s['cash_mean']:,.2f} med ${s['cash_med']:,.2f} "
          f"std ${s['cash_std']:,.2f} min ${s['cash_min']:,.2f} "
          f"max ${s['cash_max']:,.2f}")
    print(f"wins {s['wins']} ({s['win_rate']*100:.1f}%) "
          f"worst5 ${s['worst5']:,.2f} worst1 ${s['worst1']:,.2f}")
    print("=" * 64)


if __name__ == "__main__":
    main()
