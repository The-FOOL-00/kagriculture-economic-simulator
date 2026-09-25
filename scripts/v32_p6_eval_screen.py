# SPDX-License-Identifier: MIT
"""V32 P6 Closed-Loop Screen Evaluation Harness.

Supports:
- Evaluation with or without semantic action masking (--mask 0/1)
- Tracking opening metrics (Step-0 Wash, Step-0 PASS, Step-1 NORTH, Step-1 Hires)
- Tracking Step-2 Farmer Opcode and Step-2 SOUTH rate
- Full 120-leg development screen: 10 seeds x 6 opponents x 2 seats
"""

import argparse
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

from v32_common import assert_frozen, check_seed_allowed, load_agent
from v32.p2.essentials import essentialize
from v32.p2.features import Normalizer, EpisodeFeatures, unit_ctx
from v32.p3 import codec as C
from v32.p3.models import P3Policy
from v32.p3.rollout import Predictor
from v32.p6.mask import compute_unit_op_mask, apply_mask_to_logits

_W = {}


class MaskedPredictor:
    def __init__(self, model, norm, apply_mask=True):
        self.model = model
        self.norm = norm
        self.apply_mask = apply_mask
        self.fb = EpisodeFeatures()
        self.prev_act = None

    def reset(self):
        self.fb.reset()
        self.prev_act = None

    def step(self, ess, deterministic=True):
        import torch
        feat = self.norm.transform(np.asarray([self.fb.update(ess, self.prev_act)]))[0]
        n_u = 1 + len(ess.get("hands", []) or [])
        assert n_u - 1 <= C.MAX_HANDS_CAP
        st = torch.tensor(np.asarray([feat.tolist()]), dtype=torch.float32)
        uc = torch.tensor(np.asarray([[unit_ctx(ess, j) for j in range(n_u)]]), dtype=torch.float32)
        vv = torch.ones(1, n_u, dtype=torch.bool)

        with torch.no_grad():
            out = self.model(st, uc, vv)
            u_ops = []
            for j in range(n_u):
                raw_logits = out["u_op"][0, j].numpy()
                if self.apply_mask:
                    mask = compute_unit_op_mask(ess, j, board_size=10)
                    masked_logits = apply_mask_to_logits(raw_logits, mask)
                    u_ops.append(int(np.argmax(masked_logits)))
                else:
                    u_ops.append(int(np.argmax(raw_logits)))

            u_args = out["u_arg"].argmax(-1)[0].tolist()
            u_qtys = out["u_qty"].argmax(-1)[0].tolist()
            m_ops = out["m_op"].argmax(-1)[0].tolist()
            m_items = out["m_item"].argmax(-1)[0].tolist()
            m_qtys = out["m_qty"].argmax(-1)[0].tolist()

        u = [(o, a, q) for o, a, q in zip(u_ops, u_args, u_qtys)]
        m = [(o, i, q) for o, i, q in zip(m_ops, m_items, m_qtys)]
        act = C.decode_action(u, m)
        self.prev_act = act
        return {"action": act, "farmer_op": C.U_OP[u_ops[0]]}


def _worker_init(ckpt_path, norm_json, use_mask):
    import torch as _t
    _t.set_num_threads(1)
    _t.set_num_interop_threads(1)
    _W["model"] = P3Policy(157, 12)
    d = np.load(ckpt_path, allow_pickle=True)
    _W["model"].load_state_dict({k: _t.tensor(v) for k, v in d.items() if k != "meta"})
    _W["model"].eval()
    norm = Normalizer.from_json(norm_json)
    _W["pred"] = MaskedPredictor(_W["model"], norm, apply_mask=bool(use_mask))
    _W["nonce"] = uuid.uuid4().hex


def _run_one(spec):
    from kaggle_environments import make
    check_seed_allowed(spec["seed"])
    ag = load_agent(spec["opp"])
    pred = _W["pred"]
    env = make("kaggriculture", configuration={"seed": spec["seed"]})
    pred.reset()
    steps = []

    def learner_act(obs, cfg=None):
        pr = pred.step(essentialize(obs, spec["seat"]), deterministic=spec["deterministic"])
        steps.append(pr)
        return pr["action"]

    def opp_act(obs, cfg=None):
        return ag.act(obs, cfg)

    agents = [learner_act, opp_act] if spec["seat"] == 0 else [opp_act, learner_act]
    t0 = time.time()
    env.run(agents)
    dur = time.time() - t0

    mine = float(env.steps[-1][spec["seat"]]["reward"])
    theirs = float(env.steps[-1][1 - spec["seat"]]["reward"])

    # Analyze opening actions
    a0 = steps[0]["action"] if len(steps) > 0 else {}
    m0 = a0.get("market") or []
    ops0 = [o[0] for o in m0 if isinstance(o, list) and o]
    wash0 = (any(o in ("BUY_SEED", "BUY_PRODUCT", "BUY_ANIMAL") for o in ops0) and "SELL" in ops0)
    pass0 = ((a0.get("farmer") or ["PASS"])[0] == "PASS")

    a1 = steps[1]["action"] if len(steps) > 1 else {}
    north1 = ((a1.get("farmer") or ["PASS"])[0] == "NORTH")
    hires1 = sum(1 for o in (a1.get("market") or []) if isinstance(o, list) and len(o) > 0 and o[0] == "HIRE")

    a2 = steps[2]["action"] if len(steps) > 2 else {}
    farmer2 = (a2.get("farmer") or ["PASS"])[0]
    south2 = (farmer2 == "SOUTH")

    return {
        "key": f"V32P6EV:{spec['tag']}:{spec['opp']}:{spec['seed']}:{spec['seat']}",
        "tag": spec["tag"],
        "seed": spec["seed"],
        "opp": spec["opp"],
        "seat": spec["seat"],
        "my_cash": mine,
        "opp_cash": theirs,
        "win": 1.0 if mine > theirs else (0.0 if mine < theirs else 0.5),
        "duration_sec": dur,
        "n_steps": len(steps),
        "step0_wash": wash0,
        "step0_pass": pass0,
        "step1_north": north1,
        "step1_hires": hires1,
        "step2_op": farmer2,
        "step2_south": south2,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--mask", type=int, default=1)
    ap.add_argument("--seeds", default="249675:249684")
    ap.add_argument("--opps", default="E0_V3,E1_V22R1,E2_A7,E3_V25P3,E6_W72,E7_W2015")
    ap.add_argument("--seats", default="0,1")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--deterministic", type=int, default=1)
    args = ap.parse_args()

    assert_frozen()
    lo, hi = [int(x) for x in args.seeds.split(":")]
    for s in range(lo, hi + 1):
        check_seed_allowed(s)

    specs = []
    for s in range(lo, hi + 1):
        for o in args.opps.split(","):
            for seat in [int(x) for x in args.seats.split(",")]:
                specs.append({
                    "tag": args.tag,
                    "seed": s,
                    "opp": o,
                    "seat": seat,
                    "deterministic": bool(args.deterministic),
                })

    norm = json.load(open(os.path.join(REPO_ROOT, "results", "v32_p2_norm.json")))
    print(f"V32 P6 Screen Eval {args.tag} (Mask={args.mask}): {len(specs)} legs -> {args.out}")

    done = set()
    if os.path.exists(args.out):
        with open(args.out) as f:
            for line in f:
                if line.strip():
                    try:
                        done.add(json.loads(line.strip())["key"])
                    except Exception:
                        pass

    todo = [s for s in specs if f"V32P6EV:{s['tag']}:{s['opp']}:{s['seed']}:{s['seat']}" not in done]
    print(f"Legs to run: {len(todo)} ({len(done)} already cached)")

    if todo:
        out_f = open(args.out, "a", buffering=1)
        with ProcessPoolExecutor(max_workers=args.workers, initializer=_worker_init,
                                 initargs=(args.ckpt, norm, args.mask)) as ex:
            futs = {ex.submit(_run_one, s): s for s in todo}
            n = 0
            for fut in as_completed(futs):
                res = fut.result()
                out_f.write(json.dumps(res) + "\n")
                n += 1
                if n % 10 == 0 or n == len(todo):
                    print(f"Evaluated {n}/{len(todo)} legs (last cash: ${res['my_cash']:,.2f}, S2={res['step2_op']})", flush=True)
        out_f.close()

    # Aggregate
    all_res = []
    with open(args.out) as f:
        for line in f:
            if line.strip():
                all_res.append(json.loads(line.strip()))

    cashes = [r["my_cash"] for r in all_res]
    wins = [r["win"] for r in all_res]
    washes = [r["step0_wash"] for r in all_res]
    passes = [r["step0_pass"] for r in all_res]
    norths = [r["step1_north"] for r in all_res]
    hires = [r["step1_hires"] for r in all_res]
    souths2 = [r["step2_south"] for r in all_res]

    print("\n" + "=" * 60)
    print(f"=== V32 P6 SCREEN REPORT: {args.tag} (Mask={args.mask}) ===")
    print("=" * 60)
    print(f"Total Legs Evaluated:    {len(all_res)}")
    print(f"Step-0 Wash Execution:   {sum(washes)}/{len(all_res)} ({np.mean(washes)*100:.1f}%)")
    print(f"Step-0 Farmer Pass:      {sum(passes)}/{len(all_res)} ({np.mean(passes)*100:.1f}%)")
    print(f"Step-1 Farmer North:     {sum(norths)}/{len(all_res)} ({np.mean(norths)*100:.1f}%)")
    print(f"Step-1 Mean Hires:       {np.mean(hires):.2f}")
    print(f"Step-2 Farmer SOUTH:     {sum(souths2)}/{len(all_res)} ({np.mean(souths2)*100:.1f}%)")
    print(f"Win Rate:                {np.mean(wins)*100:.1f}% ({sum(1 for w in wins if w == 1.0)} wins)")
    print(f"Terminal Cash Mean:      ${np.mean(cashes):,.2f}")
    print(f"Terminal Cash Median:    ${np.median(cashes):,.2f}")
    print(f"Terminal Cash Std:       ${np.std(cashes):,.2f}")
    print(f"Terminal Cash Min:       ${np.min(cashes):,.2f}")
    print(f"Terminal Cash Max:       ${np.max(cashes):,.2f}")
    print(f"Worst 5% Cash:           ${np.percentile(cashes, 5):,.2f}")
    print(f"Worst 1% Cash:           ${np.percentile(cashes, 1):,.2f}")
    print("=" * 60)


if __name__ == "__main__":
    main()
