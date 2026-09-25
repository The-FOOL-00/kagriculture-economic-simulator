# SPDX-License-Identifier: MIT
"""V30: live-meta gauntlet harness (exploratory).

Generic head-to-head + self-play runner over hermetic agent loaders:
  V3    = frozen V3 tarball (submission_Vj_kc_v3.tar.gz), V3BackboneAdapter
  A7    = V27AblationAdapter("V27-ABL-A7") frozen bytes
  file  = exec-isolated main.py agent callable (meta agents)
  pkg   = file + sys.path injection (agents with helper packages)

Usage:
  v30_gauntlet.py --bouts "V3:P3090,A7:P3090,P3090:P3090" --seeds 249570:249577
                  --out results/v30_explore.jsonl [--mode pool|serial] [--workers 9]

Governance: REFUSES protected 340090..340199, 214200..214249, retired
340300..340349, and consumed V29 slice 340050..340050+39. Default exploration
cohort is 249570+ (V30_EXPLORATION; confirmation slice reserved separately).
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
from aec.backbone.v3_adapter import V3BackboneAdapter  # noqa: E402
from kaggle_environments import make  # noqa: E402

RESULTS = os.path.join(REPO_ROOT, "results")
ENGINE_VERSION = "1.32.7"

AGENTS = {
    "V3": {"kind": "v3"},
    "A7": {"kind": "a7"},
    "P3090": {"kind": "file",
              "path": "external_repos/lixingtao123-Kaggriculture/public_3090/output/main.py"},
    "P3000": {"kind": "file",
              "path": "external_repos/lixingtao123-Kaggriculture/opponents/public_3000/main.py"},
    "NIGHT": {"kind": "file",
              "path": "external_repos/lixingtao123-Kaggriculture/opponents/night_harvest/main.py"},
    "P2900": {"kind": "file",
              "path": "external_repos/lixingtao123-Kaggriculture/public_2900/main.py"},
    "OKAMI": {"kind": "file",
              "path": "external_repos/okami001-Kaggriculture/main.py"},
    "DMITRII": {"kind": "file",
              "path": "extracted_agents/dmitrii_lb2800/main.py"},
    "V66": {"kind": "pkg",
            "path": "external_repos/kaggriculture-v66-agent/main.py",
            "syspath": "external_repos/kaggriculture-v66-agent"},
    "L2530": {"kind": "file",
              "path": "external_repos/lixingtao123-Kaggriculture/public_2530_current/output/main.py"},
    "ANDREY11": {"kind": "file",
              "path": "external_repos/lixingtao123-Kaggriculture/public_andrey_v11/output/main.py"},
    "MELON2736": {"kind": "file",
              "path": "external_repos/lixingtao123-Kaggriculture/public_2736_melon/output/main.py"},
    "SOIL2843": {"kind": "file",
              "path": "external_repos/lixingtao123-Kaggriculture/public_2843_soil_v16/output/main.py"},
    "PASS": {"kind": "pass"},
    "V22R1": {"kind": "tarball", "path": "submission_aec_v22r1.tar.gz"},
    "AST": {"kind": "file", "path": "candidates/v30_a7_standalone/main.py"},
}

# Governance: never touch.
REFUSED = [(340090, 340199), (214200, 214249), (340300, 340349),
           (340050, 340050 + 39)]

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
    spec = AGENTS[agent_id]
    kind = spec["kind"]
    if kind == "v3":
        return V3BackboneAdapter()
    if kind == "pass":
        return PassiveAgent()
    if kind == "a7":
        a7 = V27AblationAdapter(variant="V27-ABL-A7")
        assert a7.call_v3_at_step0 is True and a7.open_units == 30
        assert a7.dispatch is False and a7.rewrite_step0_wash is True
        return a7
    if kind == "tarball":
        import tarfile
        path = os.path.join(REPO_ROOT, spec["path"])
        with tarfile.open(path, "r:gz") as tar:
            m = tar.extractfile("main.py")
            code = m.read().decode("utf-8")
        ns = {"__name__": "v30_iso_%s_%s" % (agent_id, uuid.uuid4().hex[:8])}
        exec(compile(code, path + "/main.py", "exec"), ns)
        fn = ns.get("agent")
        if not callable(fn):
            raise RuntimeError("no agent callable in %s" % path)
        return FileAgent(fn)
    if kind in ("file", "pkg"):
        if kind == "pkg" and spec.get("syspath"):
            p = os.path.join(REPO_ROOT, spec["syspath"])
            if p not in sys.path:
                sys.path.insert(0, p)
        path = os.path.join(REPO_ROOT, spec["path"])
        with open(path) as f:
            code = f.read()
        ns = {"__name__": "v30_iso_%s_%s" % (agent_id, uuid.uuid4().hex[:8])}
        exec(compile(code, path, "exec"), ns)
        fn = ns.get("agent")
        if not callable(fn):
            raise RuntimeError("no agent callable in %s" % path)
        return FileAgent(fn)
    raise ValueError(kind)


class FileAgent:
    def __init__(self, fn):
        self._fn = fn
        self._twoarg = True

    def act(self, obs, cfg=None):
        if self._twoarg:
            try:
                return copy.deepcopy(self._fn(obs, cfg))
            except TypeError:
                self._twoarg = False
        return copy.deepcopy(self._fn(obs))


class PassiveAgent:
    def act(self, obs, cfg=None):
        farm = (obs.get("farms") or [{}])[int(obs.get("player", 0) or 0)]
        n = len(farm.get("hands", []) or [])
        return {"farmer": ["PASS"], "hands": [["PASS"] for _ in range(n)],
                "market": []}


def farm_keys_probe(env):
    farm = env.steps[0][0]["observation"]["farms"][0]
    out = {}
    for k, v in farm.items():
        if isinstance(v, list):
            out[k] = "list[%d]" % len(v)
        elif isinstance(v, dict):
            out[k] = "dict{%s}" % ",".join(sorted(v.keys())[:12])
        else:
            out[k] = repr(v)[:40]
    return out


def telemetry(env):
    n = len(env.steps)
    money = [[], []]
    struct = [[], []]
    macro = [{}, {}]
    for s in (0, 1):
        mc = {"mkt": Counter(), "unit": Counter(), "plant": Counter()}
        macro[s] = mc
    for i in range(n):
        for s in (0, 1):
            step = env.steps[i][s]
            farm = step["observation"]["farms"][s]
            money[s].append(farm.get("money", 0.0))
            act = step.get("action") or {}
            for o in (act.get("market") or []):
                if o:
                    macro[s]["mkt"][(o[0], o[1] if len(o) > 1 else "")] += 1
            for u in ([act.get("farmer")] + list(act.get("hands") or [])):
                if u:
                    macro[s]["unit"][u[0]] += 1
                    if u[0] == "PLANT" and len(u) > 1:
                        macro[s]["plant"][u[1]] += 1
            if i % 12 == 0:
                tiles = farm.get("tiles", []) or []
                plant = past = weed = 0
                for row in tiles:
                    for t in row:
                        if isinstance(t, dict):
                            k = t.get("kind")
                            if k == "PLANT":
                                plant += 1
                            elif k == "PASTURE":
                                past += 1
                            elif k == "WEED":
                                weed += 1
                animals = farm.get("animals", None)
                if isinstance(animals, list):
                    nanim = len(animals)
                elif isinstance(animals, dict):
                    nanim = sum(len(v) if isinstance(v, list) else 1
                                for v in animals.values())
                else:
                    nanim = -1
                struct[s].append({
                    "step": i,
                    "hands": len(farm.get("hands", []) or []),
                    "plant_tiles": plant, "pasture": past, "weed": weed,
                    "quads": len(farm.get("unlocked_quadrants", []) or []),
                    "animals": nanim,
                    "money": farm.get("money", 0.0),
                })
    # daily money (end of each day)
    daily = [[], []]
    for s in (0, 1):
        for d in range(30):
            idx = min((d + 1) * 24 - 1, n - 1)
            daily[s].append(money[s][idx])
    mout = []
    for s in (0, 1):
        mout.append({kk: [["|".join(map(str, k)), v]
                         for k, v in sorted(macro[s][kk].items())]
                     for kk in ("mkt", "unit", "plant")})
    return {"daily_money": daily, "struct12": struct, "macro": mout,
            "n_steps": n}


def run_one(spec):
    seed = spec["seed"]
    check_seed_allowed(seed)
    left_id, right_id = spec["left"], spec["right"]
    left, right = load_agent(left_id), load_agent(right_id)
    a = lambda o, c=None: left.act(o, c)  # noqa: E731
    b = lambda o, c=None: right.act(o, c)  # noqa: E731
    env = make("kaggriculture", configuration={"seed": seed})
    t0 = time.time()
    env.run([a, b])
    dur = time.time() - t0
    r0 = env.steps[-1][0]["reward"]
    r1 = env.steps[-1][1]["reward"]
    delta = r0 - r1
    tel = telemetry(env)
    acts0 = [s[0].get("action") for s in env.steps]
    digest = hashlib.sha256(json.dumps(acts0, sort_keys=True).encode()).hexdigest()
    return {"key": "V30:%s:%s:%d" % (left_id, right_id, seed),
            "seed": seed, "left": left_id, "right": right_id,
            "seat0_reward": r0, "seat1_reward": r1, "delta": delta,
            "winner": ("LEFT" if delta > 0 else ("RIGHT" if delta < 0 else "TIE")),
            "action_digest": digest, "duration_sec": dur,
            "engine_version": ENGINE_VERSION,
            "pid": os.getpid(), "worker_nonce": WORKER_NONCE,
            "mode": spec.get("mode", "pool"), "timestamp": time.time(),
            "telemetry": tel}


def parse_bouts(s):
    out = []
    for b in s.split(","):
        l, r = b.split(":")
        out.append((l.strip(), r.strip()))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--bouts", required=True)
    ap.add_argument("--seeds", default="249570:249577")
    ap.add_argument("--out", default="v30_explore.jsonl")
    ap.add_argument("--mode", default="pool", choices=["pool", "serial"])
    ap.add_argument("--workers", type=int, default=9)
    ap.add_argument("--probe", action="store_true",
                    help="dump farm obs keys from first match and exit")
    a = ap.parse_args(argv)
    lo, hi = [int(x) for x in a.seeds.split(":")]
    seeds = list(range(lo, hi + 1))
    for s in seeds:
        check_seed_allowed(s)
    bouts = parse_bouts(a.bouts)
    for l, r in bouts:
        assert l in AGENTS and r in AGENTS, (l, r)
    specs = [{"seed": s, "left": l, "right": r, "mode": a.mode}
             for (l, r) in bouts for s in seeds]
    out_path = os.path.join(RESULTS, a.out) if not os.path.isabs(a.out) else a.out
    if a.probe:
        # single match in-process for obs probe
        left, right = load_agent(bouts[0][0]), load_agent(bouts[0][1])
        env = make("kaggriculture", configuration={"seed": seeds[0]})
        env.run([lambda o, c=None: left.act(o, c),
                 lambda o, c=None: right.act(o, c)])
        print(json.dumps(farm_keys_probe(env), indent=1))
        print("steps:", len(env.steps))
        print("rewards:", env.steps[-1][0]["reward"], env.steps[-1][1]["reward"])
        return
    done = {}
    if os.path.exists(out_path):
        with open(out_path) as f:
            for line in f:
                try:
                    r = json.loads(line)
                    done[r["key"]] = r
                except Exception:
                    pass
    todo = [s for s in specs
            if "V30:%s:%s:%d" % (s["left"], s["right"], s["seed"]) not in done]
    print("bouts=%s seeds=%d todo=%d/%d out=%s" % (
        bouts, len(seeds), len(todo), len(specs), out_path), flush=True)
    f = open(out_path, "a")
    try:
        if a.mode == "serial":
            for s in todo:
                r = run_one(s)
                f.write(json.dumps(r) + "\n")
                f.flush()
                print(r["key"], r["seat0_reward"], r["seat1_reward"],
                      "%.1fs" % r["duration_sec"], flush=True)
        else:
            with ProcessPoolExecutor(max_workers=a.workers,
                                     max_tasks_per_child=1,
                                     initializer=_worker_init) as ex:
                futs = {ex.submit(run_one, s): s for s in todo}
                for fut in as_completed(futs):
                    r = fut.result()
                    f.write(json.dumps(r) + "\n")
                    f.flush()
                    print(r["key"], r["seat0_reward"], r["seat1_reward"],
                          "%.1fs" % r["duration_sec"], flush=True)
    finally:
        f.close()


if __name__ == "__main__":
    main()
