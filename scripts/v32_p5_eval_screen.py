# SPDX-License-Identifier: MIT
"""V32 P5 Closed-Loop Screen Evaluation Harness:
Evaluates a candidate checkpoint across the 120-leg development screen:
- 10 seeds: 249675 to 249684
- 6 opponents: E0_V3, E1_V22R1, E2_A7, E3_V25P3, E6_W72, E7_W2015
- 2 seats: 0, 1
Total: 120 legs.

Logs per leg:
- seed, opp, seat, my_cash, opp_cash, win
- step 0 market wash
- step 0 farmer pass
- step 1 farmer north
- step 1 hires
- terminal cash statistics
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

from v32_common import assert_frozen, check_seed_allowed, expert_digest, load_agent
from v32.p2.essentials import essentialize
from v32.p2.features import Normalizer
from v32.p3 import codec as C
from v32.p3.models import P3Policy
from v32.p3.rollout import Predictor

_W = {}

def _worker_init(ckpt_path, norm_json):
    import torch as _t
    _t.set_num_threads(1)
    _t.set_num_interop_threads(1)
    _W["model"] = P3Policy(157, 12)
    d = np.load(ckpt_path, allow_pickle=True)
    _W["model"].load_state_dict({k: _t.tensor(v) for k, v in d.items() if k != "meta"})
    _W["model"].eval()
    _W["pred"] = Predictor(_W["model"], Normalizer.from_json(norm_json))
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
    
    return {
        "key": f"V32P5EV:{spec['tag']}:{spec['opp']}:{spec['seed']}:{spec['seat']}",
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
                    "deterministic": bool(args.deterministic)
                })

    norm = json.load(open(os.path.join(REPO_ROOT, "results", "v32_p2_norm.json")))
    print(f"V32 P5 Screen Eval {args.tag}: {len(specs)} legs -> {args.out}")

    done = set()
    if os.path.exists(args.out):
        with open(args.out) as f:
            for line in f:
                if line.strip():
                    try:
                        done.add(json.loads(line.strip())["key"])
                    except Exception:
                        pass
                        
    todo = [s for s in specs if f"V32P5EV:{s['tag']}:{s['opp']}:{s['seed']}:{s['seat']}" not in done]
    print(f"Legs to run: {len(todo)} ({len(done)} already cached)")

    if todo:
        out_f = open(args.out, "a", buffering=1)
        with ProcessPoolExecutor(max_workers=args.workers, initializer=_worker_init, initargs=(args.ckpt, norm)) as ex:
            futs = {ex.submit(_run_one, s): s for s in todo}
            n = 0
            for fut in as_completed(futs):
                res = fut.result()
                out_f.write(json.dumps(res) + "\n")
                n += 1
                if n % 10 == 0 or n == len(todo):
                    print(f"Evaluated {n}/{len(todo)} legs (last cash: ${res['my_cash']:,.2f})", flush=True)
        out_f.close()

    # Aggregate and print full statistics
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

    print("\n" + "=" * 60)
    print(f"=== V32 P5 CLOSED-LOOP SCREEN REPORT: {args.tag} ===")
    print("=" * 60)
    print(f"Total Legs Evaluated: {len(all_res)}")
    print(f"Step-0 Wash Execution:   {sum(washes)}/{len(all_res)} ({np.mean(washes)*100:.1f}%)")
    print(f"Step-0 Farmer Pass:      {sum(passes)}/{len(all_res)} ({np.mean(passes)*100:.1f}%)")
    print(f"Step-1 Farmer North:     {sum(norths)}/{len(all_res)} ({np.mean(norths)*100:.1f}%)")
    print(f"Step-1 Mean Hires:       {np.mean(hires):.2f}")
    print(f"Win Rate:                {np.mean(wins)*100:.1f}% ({sum(1 for w in wins if w == 1.0)} wins, {sum(1 for w in wins if w == 0.5)} ties)")
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
