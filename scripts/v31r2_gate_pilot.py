# SPDX-License-Identifier: MIT
"""V31R2 E1: GATE pilot — GATE vs A7 / V3 / GATE / V22R1 on virgin seeds.

Usage:
  v31r2_gate_pilot.py --bouts "GATE:A7,A7:GATE" --seeds 249591:249600
                      --out results/v31r2_gate_pilot.jsonl [--workers 9]

Governance: REFUSES protected 340090..340199, 214200..214249, retired
340300..340349, consumed 340050..340050+39 and earlier 249xxx cohorts.
E1 virgin slice: 249591..249600 (+249601..249604 reserved for V22R1 legs).
"""

import argparse
import copy
import hashlib
import json
import os
import sys
import time
import uuid
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

from aec.backbone.v27_ablation_adapters import V27AblationAdapter  # noqa: E402
from aec.backbone.v31r2_gate_adapter import V31R2GateAdapter  # noqa: E402
from aec.backbone.v31r2_split_adapter import V31R2SplitAdapter  # noqa: E402
from aec.backbone.v31r2_wash_adapter import V31R2WashAdapter  # noqa: E402
from aec.backbone.v3_adapter import V3BackboneAdapter  # noqa: E402
from kaggle_environments import make  # noqa: E402

ENGINE_VERSION = "1.32.7"
REFUSED = [(340090, 340199), (214200, 214249), (340300, 340349),
           (340050, 340050 + 39)] + [(s, s) for s in range(249500, 249605)]
WORKER_NONCE = None


def _worker_init():
    global WORKER_NONCE
    WORKER_NONCE = uuid.uuid4().hex


def check_seed_allowed(seed):
    for lo, hi in REFUSED:
        if lo <= seed <= hi:
            raise RuntimeError("GOVERNANCE REFUSAL: seed %d in refused %d..%d"
                               % (seed, lo, hi))


def load_agent(agent_id):
    if agent_id == "V3":
        return V3BackboneAdapter()
    if agent_id == "A7":
        a7 = V27AblationAdapter(variant="V27-ABL-A7")
        assert a7.call_v3_at_step0 is True and a7.open_units == 30
        assert a7.dispatch is False and a7.rewrite_step0_wash is True
        return a7
    if agent_id == "GATE":
        return V31R2GateAdapter(gate_frac=0.5)
    if agent_id == "SPLIT":
        return V31R2SplitAdapter(cap=10)
    if agent_id in ("W72", "W2015", "W10", "W5"):
        return V31R2WashAdapter(wash=agent_id)
    if agent_id in ("W72S", "W2015S", "W10S", "W5S"):
        return V31R2WashAdapter(wash=agent_id[:-1], split_cap=10)
    if agent_id == "V22R1":
        import tarfile
        path = os.path.join(REPO_ROOT, "submission_aec_v22r1.tar.gz")
        with tarfile.open(path, "r:gz") as tar:
            code = tar.extractfile("main.py").read().decode("utf-8")
        ns = {"__name__": "v31r2_iso_%s" % uuid.uuid4().hex[:8]}
        exec(compile(code, path + "/main.py", "exec"), ns)
        fn = ns.get("agent")
        if not callable(fn):
            raise RuntimeError("no agent callable in V22R1 tarball")

        class FileAgent:
            def __init__(self):
                self._twoarg = True

            def act(self, obs, cfg=None):
                if self._twoarg:
                    try:
                        return copy.deepcopy(fn(obs, cfg))
                    except TypeError:
                        self._twoarg = False
                return copy.deepcopy(fn(obs))

        return FileAgent()
    raise ValueError(agent_id)


def telemetry(env):
    n = len(env.steps)
    out = {"sell_qty": [{}, {}], "sell_orders": [0, 0],
           "daily_money": [[], []], "n_steps": n}
    for s in (0, 1):
        q = Counter()
        no = 0
        for i in range(n):
            act = env.steps[i][s].get("action") or {}
            for o in (act.get("market") or []):
                if o and o[0] == "SELL" and len(o) >= 3:
                    q[o[1]] += o[2]
                    no += 1
        out["sell_qty"][s] = dict(q)
        out["sell_orders"][s] = no
        for d in range(30):
            idx = min((d + 1) * 24 - 1, n - 1)
            out["daily_money"][s].append(
                env.steps[idx][s]["observation"]["farms"][s].get("money", 0.0))
    return out


def run_one(spec):
    seed = spec["seed"]
    check_seed_allowed(seed)
    left_id, right_id = spec["left"], spec["right"]
    left, right = load_agent(left_id), load_agent(right_id)
    env = make("kaggriculture", configuration={"seed": seed})
    t0 = time.time()
    env.run([lambda o, c=None: left.act(o, c),
             lambda o, c=None: right.act(o, c)])
    dur = time.time() - t0
    r0 = env.steps[-1][0]["reward"]
    r1 = env.steps[-1][1]["reward"]
    tel = telemetry(env)
    acts0 = [s[0].get("action") for s in env.steps]
    digest = hashlib.sha256(json.dumps(acts0, sort_keys=True).encode()).hexdigest()[:16]
    gate = {}
    for tag, ag in (("left", left), ("right", right)):
        if isinstance(ag, V31R2GateAdapter):
            gate[tag] = {"drops": ag.gate_drops, "keeps": ag.gate_keeps}
    return {"key": "V31R2:%s:%s:%d" % (left_id, right_id, seed),
            "seed": seed, "left": left_id, "right": right_id,
            "seat0_reward": r0, "seat1_reward": r1, "delta": r0 - r1,
            "winner": ("LEFT" if r0 > r1 else ("RIGHT" if r1 > r0 else "TIE")),
            "action_digest": digest, "duration_sec": dur,
            "engine_version": ENGINE_VERSION, "pid": os.getpid(),
            "worker_nonce": WORKER_NONCE, "telemetry": tel, "gate": gate}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--bouts", required=True)
    ap.add_argument("--seeds", default="249591:249600")
    ap.add_argument("--out", default="results/v31r2_gate_pilot.jsonl")
    ap.add_argument("--workers", type=int, default=9)
    a = ap.parse_args(argv)
    lo, hi = [int(x) for x in a.seeds.split(":")]
    seeds = list(range(lo, hi + 1))
    for s in seeds:
        check_seed_allowed(s)
    bouts = [tuple(b.split(":")) for b in a.bouts.split(",")]
    specs = [{"seed": s, "left": l, "right": r} for (l, r) in bouts for s in seeds]
    done = set()
    if os.path.exists(a.out):
        with open(a.out) as f:
            for line in f:
                try:
                    done.add(json.loads(line)["key"])
                except Exception:
                    pass
    todo = [s for s in specs
            if "V31R2:%s:%s:%d" % (s["left"], s["right"], s["seed"]) not in done]
    print("bouts=%s seeds=%d todo=%d/%d out=%s" % (
        bouts, len(seeds), len(todo), len(specs), a.out), flush=True)
    f = open(a.out, "a")
    with ProcessPoolExecutor(max_workers=a.workers, max_tasks_per_child=1,
                             initializer=_worker_init) as ex:
        futs = {ex.submit(run_one, s): s for s in todo}
        for fut in as_completed(futs):
            r = fut.result()
            f.write(json.dumps(r) + "\n")
            f.flush()
            print(r["key"], "%.0f" % r["seat0_reward"], "%.0f" % r["seat1_reward"],
                  r["winner"], "%.1fs" % r["duration_sec"], flush=True)


if __name__ == "__main__":
    main()
