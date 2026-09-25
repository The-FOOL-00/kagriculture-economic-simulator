# SPDX-License-Identifier: MIT
"""V32 R1 router labels: full-episode + continuation grids with prefix capture.

Usage:
  v32_router_labels.py --out FILE --mode full|cont --seeds LO:HI
      [--seat0 CLASS,CLASS...] [--seat1 OPP,OPP...] [--mirror] [--workers N]

- full: seat0=CLASS (full episode) vs seat1=OPP. Records 24-step prefix
  (encoded obs at t=0,1,4,8,12,16,20,24 + wheat/cash track) for Regime B.
- cont: seat0=V3 opens steps 0..23, fresh CLASS continues from step 24
  vs seat1=OPP. Prefix recorded pre-handoff (router decision point).
- --mirror: also run the swapped-seat leg (key suffix :MIR) for the
  seat-symmetry verification sample.
- Single-seat default (P1-F11: non-V22R1 mirrors symmetric 416/416).
- Quarantine + frozen digests enforced; per-leg digests recorded.
- Checkpointed/resumable by key. V22R1 never in these grids (eval-only).
"""

import argparse
import hashlib
import json
import os
import sys
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, as_completed

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from v32_common import (ENGINE_VERSION, assert_frozen,  # noqa: E402
                        check_seed_allowed, expert_digest, load_agent,
                        telemetry)
from v32_encoder import ENCODER_VERSION, encode_obs  # noqa: E402

PREFIX_STEPS = (0, 1, 4, 8, 12, 16, 20, 24)
OPEN_STEPS = 24
WORKER_NONCE = None


def _worker_init():
    global WORKER_NONCE
    WORKER_NONCE = uuid.uuid4().hex


class PrefixRecorder:
    """Wraps seat-0 agent; captures prefix frames + wheat/cash track."""

    def __init__(self, agent):
        self.agent = agent
        self.frames = {}
        self.wheat = {}
        self.cash = {}
        self.inv_wheat = {}

    def act(self, obs, cfg=None):
        step = int(obs.get("step", -1))
        if step in PREFIX_STEPS:
            try:
                self.frames[step] = encode_obs(obs, 0)
            except Exception as e:  # noqa: BLE001 - loud degradation
                print("ENCODE-FAIL step=%s: %r" % (step, e), flush=True)
                self.frames[step] = None
            mkt = obs.get("market", {}) or {}
            self.wheat[step] = (mkt.get("prices", {}) or {}).get("WHEAT")
            self.inv_wheat[step] = (mkt.get("inventory", {}) or {}).get("WHEAT")
            farms = obs.get("farms", []) or []
            self.cash[step] = [((farms[0] or {}).get("money") if len(farms) > 0 else None),
                              ((farms[1] or {}).get("money") if len(farms) > 1 else None)]
        return self.agent.act(obs, cfg)


class HandoffAgent:
    """V3 opens steps 0..23, then a FRESH continuation expert takes over."""

    def __init__(self, opener, cont_id):
        self.opener = opener
        self.cont_id = cont_id
        self.cont = None
        self.switched_at = None

    def act(self, obs, cfg=None):
        step = int(obs.get("step", -1))
        if step < OPEN_STEPS:
            return self.opener.act(obs, cfg)
        if self.cont is None:
            self.cont = load_agent(self.cont_id)
            self.switched_at = step
        return self.cont.act(obs, cfg)


def run_one(spec):
    from kaggle_environments import make
    seed = spec["seed"]
    check_seed_allowed(seed)
    cls, opp = spec["cls"], spec["opp"]
    mirror = spec.get("mirror", False)
    mode = spec["mode"]
    if mode == "full":
        me = PrefixRecorder(load_agent(cls))
        you = load_agent(opp)
        agents = [me, you] if not mirror else [you, me]
        # NOTE: PrefixRecorder encodes with player=0; in mirror legs our
        # class is seat 1, so prefix frames are opponent-perspective and
        # flagged non-canonical (symmetry check only, never trained on).
        opener_digest = None
    else:
        assert not mirror, "cont mirror not supported"
        opener = load_agent("E0_V3")
        me = PrefixRecorder(HandoffAgent(opener, cls))
        you = load_agent(opp)
        agents = [me, you]
        opener_digest = expert_digest("E0_V3")
    a = lambda o, c=None: agents[0].act(o, c)  # noqa: E731
    b = lambda o, c=None: agents[1].act(o, c)  # noqa: E731
    env = make("kaggriculture", configuration={"seed": seed})
    t0 = time.time()
    env.run([a, b])
    dur = time.time() - t0
    r0 = env.steps[-1][0]["reward"]
    r1 = env.steps[-1][1]["reward"]
    acts = [[s[0].get("action"), s[1].get("action")] for s in env.steps]
    digest = hashlib.sha256(json.dumps(acts, sort_keys=True).encode()).hexdigest()
    tel = telemetry(env)
    money_digest = hashlib.sha256(json.dumps(tel["money"]).encode()).hexdigest()
    my_cash, opp_cash = (r0, r1) if not mirror else (r1, r0)
    return {
        "key": "V32R1%s:%s:%s:%d%s" % (
            "FULL" if mode == "full" else "CONT", cls, opp, seed,
            ":MIR" if mirror else ""),
        "mode": mode, "seed": seed, "cls": cls, "opp": opp,
        "mirror": mirror, "my_cash": my_cash, "opp_cash": opp_cash,
        "margin": my_cash - opp_cash,
        "win": 1.0 if my_cash > opp_cash else (0.0 if my_cash < opp_cash else 0.5),
        "action_digest": digest, "money_digest": money_digest,
        "engine_version": ENGINE_VERSION, "encoder": ENCODER_VERSION,
        "cls_digest": expert_digest(cls), "opp_digest": expert_digest(opp),
        "opener_digest": opener_digest,
        "pid": __import__("os").getpid(), "worker_nonce": WORKER_NONCE,
        "duration_sec": dur,
        "prefix": {"frames": {str(k): v for k, v in me.frames.items()},
                   "wheat": {str(k): v for k, v in me.wheat.items()},
                   "inv_wheat": {str(k): v for k, v in me.inv_wheat.items()},
                   "cash": {str(k): v for k, v in me.cash.items()},
                   "canonical": not mirror},
        "telemetry": tel,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--mode", required=True, choices=["full", "cont"])
    ap.add_argument("--seeds", required=True)
    ap.add_argument("--seat0", default="E0_V3,E2_A7,E3_V25P3,E6_W72,E7_W2015")
    ap.add_argument("--seat1", default="E0_V3,E2_A7,E3_V25P3,E6_W72,E7_W2015,E8_DMITRII")
    ap.add_argument("--pairs", default=None,
                    help="comma-separated CLS:OPP allowlist (overrides product)")
    ap.add_argument("--mirror", action="store_true")
    ap.add_argument("--workers", type=int, default=10)
    args = ap.parse_args()
    assert_frozen()
    lo, hi = [int(x) for x in args.seeds.split(":")]
    for s in range(lo, hi + 1):
        check_seed_allowed(s)
    clss = args.seat0.split(",")
    opps = args.seat1.split(",")
    assert "E1_V22R1" not in clss and "E1_V22R1" not in opps, "V22R1 eval-only"
    allow = None
    if args.pairs:
        allow = set(args.pairs.split(","))
    specs = []
    for s in range(lo, hi + 1):
        for c in clss:
            for o in opps:
                if allow is not None and "%s:%s" % (c, o) not in allow:
                    continue
                specs.append({"mode": args.mode, "seed": s, "cls": c, "opp": o})
                if args.mirror:
                    specs.append({"mode": args.mode, "seed": s, "cls": c,
                                  "opp": o, "mirror": True})
    tag = "V32R1FULL" if args.mode == "full" else "V32R1CONT"
    print("V32 R1 labels: %d legs mode=%s seeds %d..%d -> %s"
          % (len(specs), args.mode, lo, hi, args.out), flush=True)
    done = set()
    if os.path.exists(args.out):
        with open(args.out) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        done.add(json.loads(line)["key"])
                    except (KeyError, ValueError):
                        pass
    todo = [s for s in specs
            if "%s:%s:%s:%d%s" % (tag, s["cls"], s["opp"], s["seed"],
                                  ":MIR" if s.get("mirror") else "") not in done]
    print("V32 R1 labels: %d already done, %d to run" % (len(done), len(todo)),
          flush=True)
    if not todo:
        return
    out = open(args.out, "a", buffering=1)
    with ProcessPoolExecutor(max_workers=args.workers,
                             initializer=_worker_init,
                             max_tasks_per_child=1) as ex:
        futs = {ex.submit(run_one, s): s for s in todo}
        n = 0
        for fut in as_completed(futs):
            rec = fut.result()
            out.write(json.dumps(rec) + "\n")
            n += 1
            if n % 25 == 0:
                print("V32 R1 labels: %d/%d" % (n, len(todo)), flush=True)
    out.close()
    print("V32 R1 labels: complete %d legs" % len(todo), flush=True)


if __name__ == "__main__":
    main()
