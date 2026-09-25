# SPDX-License-Identifier: MIT
"""V32 shared harness: expert registry, quarantine, digests, telemetry.

All V32 match execution goes through this module so quarantine and digest
rules are identical across EXP-1..9, probes, and tests.
"""

import copy
import hashlib
import json
import os
import sys
import uuid

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

ENGINE_VERSION = "1.32.7"

# Frozen digests (V32_BASELINE_FREEZE.md).
DIGESTS = {
    "v3_tarball": "845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943",
    "v22r1_tarball": "6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5",
    "a7_standalone": "51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f",
    "v25_p3_unified": "13292582c8cc796bc11ccebff9684fbec45cfb97d936fb9e85e4e9bb4dbea179",
    "dmitrii": "495bfa4825c9e58638e804aeeb62a9537826f6d4d869222815e1bbeefd84d3dc",
    "v27_ablation_adapters": "18d2c8ea2cf826b0bef71c96988dba0c93d7dbcc73936a0c99f07cb0539e7ae9",
    "v25_p3_adapter": "ce8169e95e86bd338b32dada48ba3fa0216bdeea4cebdd34a0264fe18a9f5195",
    "v3_adapter": "a0a9fd2c2ce1abe2de7e871e7fd9deec647df9863179c19cf1b94fc5ed2e3135",
    "interface": "1a1c5ec7cbc097c13d60eeed98ed98749f11cad7456c368366513dc7eeda4091",
    "utils": "53f9277406162cf1789d5dceb944f147ead85d65d52647350533a1c1c7684404",
    "config": "14c3a22c0141b770efe43244afe77f7ed27064e0256bdb9f8b40750e3b2eabae",
    "v31r2_wash_adapter": "08e9832a1351bbf4cdd9e8483a247af719a01f70471434bd6e581acae15c9402",
}

PATHS = {
    "v3_tarball": "submission_Vj_kc_v3.tar.gz",
    "v22r1_tarball": "submission_aec_v22r1.tar.gz",
    "a7_standalone": "candidates/v30_a7_standalone/main.py",
    "v25_p3_unified": "candidates/v25_p3_unified.py",
    "dmitrii": "extracted_agents/dmitrii_lb2800/main.py",
    "v27_ablation_adapters": "aec/backbone/v27_ablation_adapters.py",
    "v25_p3_adapter": "aec/backbone/v25_p3_adapter.py",
    "v3_adapter": "aec/backbone/v3_adapter.py",
    "interface": "aec/backbone/interface.py",
    "utils": "aec/backbone/utils.py",
    "config": "aec/config.py",
    "v31r2_wash_adapter": "aec/backbone/v31r2_wash_adapter.py",
}

# V32 cohorts.
V32_TRAIN = (249635, 249674)
V32_DEV = (249675, 249694)
V32_CONFIRM = (249695, 249734)
V32_EXP1 = (249635, 249640)

# Seeds V32 must never execute (protected holdouts + all consumed ranges).
REFUSED = [
    (214200, 214249),   # GATE0 virgin holdout
    (340000, 340049),   # EXP-AEC-001 consumed
    (340050, 340050 + 39),   # V29 consumed (V30 arithmetic-literal convention)
    (340090, 340199),   # protected remainder
    (340200, 340249),   # EXP-AEC-002 consumed
    (340250, 340299),   # EXP-AEC-003 consumed
    (340300, 340349),   # EXP-AEC-004 retired
]

# Expert registry: id -> loader spec. Manifest: V32_EXPERT_POPULATION.json.
EXPERTS = {
    "E0_V3": {"kind": "v3"},
    "E1_V22R1": {"kind": "tarball", "path": "submission_aec_v22r1.tar.gz"},
    "E2_A7": {"kind": "a7", "variant": "V27-ABL-A7"},
    "E3_V25P3": {"kind": "v25p3"},
    "E4_A1": {"kind": "a7", "variant": "V27-ABL-A1"},
    "E5_A2": {"kind": "a7", "variant": "V27-ABL-A2"},
    "E6_W72": {"kind": "wash", "wash": "W72"},
    "E7_W2015": {"kind": "wash", "wash": "W2015"},
    "E8_DMITRII": {"kind": "file", "path": "extracted_agents/dmitrii_lb2800/main.py"},
    "E9_AST": {"kind": "file", "path": "candidates/v30_a7_standalone/main.py"},
    "E10_PASS": {"kind": "pass"},
}

CORE_RR = ["E0_V3", "E1_V22R1", "E2_A7", "E3_V25P3", "E4_A1",
           "E5_A2", "E6_W72", "E7_W2015", "E8_DMITRII"]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def assert_frozen():
    """Refuse to run if any frozen V32 dependency differs."""
    for key, rel in PATHS.items():
        got = sha256_file(os.path.join(REPO_ROOT, rel))
        assert got == DIGESTS[key], "V32 drift: %s (%s != %s)" % (rel, got[:12], DIGESTS[key][:12])
    import kaggle_environments
    assert kaggle_environments.__version__ == ENGINE_VERSION, kaggle_environments.__version__


def check_seed_allowed(seed, allow_confirm=False):
    """Governance refusal. V32 executes ONLY its own 249635+ line.

    allow_confirm=True is required for V32-CONFIRM and must only be passed by
    a pre-registered promotion test.
    """
    for lo, hi in REFUSED:
        if lo <= seed <= hi:
            raise RuntimeError("V32 GOVERNANCE REFUSAL: seed %d in refused %d..%d"
                               % (seed, lo, hi))
    if seed < V32_TRAIN[0]:
        raise RuntimeError("V32 GOVERNANCE REFUSAL: seed %d below V32 line (consumed history)" % seed)
    if V32_CONFIRM[0] <= seed <= V32_CONFIRM[1] and not allow_confirm:
        raise RuntimeError("V32 GOVERNANCE REFUSAL: seed %d is V32-CONFIRM (single-touch)" % seed)
    if seed > V32_CONFIRM[1]:
        raise RuntimeError("V32 GOVERNANCE REFUSAL: seed %d beyond registered V32 range" % seed)


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
        return {"farmer": ["PASS"], "hands": [["PASS"] for _ in range(n)], "market": []}


def load_agent(expert_id):
    """Construct a fresh expert. No shared state across matches."""
    from aec.backbone.v27_ablation_adapters import V27AblationAdapter
    from aec.backbone.v25_p3_adapter import V25P3BackboneAdapter
    from aec.backbone.v3_adapter import V3BackboneAdapter
    from aec.backbone.v31r2_wash_adapter import V31R2WashAdapter

    spec = EXPERTS[expert_id]
    kind = spec["kind"]
    if kind == "v3":
        return V3BackboneAdapter()
    if kind == "v25p3":
        return V25P3BackboneAdapter()
    if kind == "a7":
        a = V27AblationAdapter(variant=spec["variant"])
        if spec["variant"] == "V27-ABL-A7":
            assert a.call_v3_at_step0 is True and a.open_units == 30
            assert a.dispatch is False and a.rewrite_step0_wash is True
        return a
    if kind == "wash":
        return V31R2WashAdapter(wash=spec["wash"])
    if kind == "pass":
        return PassiveAgent()
    if kind in ("file", "tarball"):
        import tarfile
        path = os.path.join(REPO_ROOT, spec["path"])
        if kind == "tarball":
            with tarfile.open(path, "r:gz") as tar:
                m = tar.extractfile("main.py")
                code = m.read().decode("utf-8")
        else:
            with open(path) as f:
                code = f.read()
        ns = {"__name__": "v32_iso_%s_%s" % (expert_id, uuid.uuid4().hex[:8])}
        exec(compile(code, spec["path"], "exec"), ns)
        fn = ns.get("agent")
        if not callable(fn):
            raise RuntimeError("no agent callable in %s" % path)
        return FileAgent(fn)
    raise ValueError(kind)


def expert_digest(expert_id):
    """Frozen digest resolving this expert (per-match record)."""
    spec = EXPERTS[expert_id]
    kind = spec["kind"]
    if kind == "v3":
        return DIGESTS["v3_tarball"]
    if kind == "v25p3":
        return DIGESTS["v25_p3_adapter"] + ":" + DIGESTS["v25_p3_unified"]
    if kind == "a7":
        return DIGESTS["v27_ablation_adapters"] + ":" + spec["variant"]
    if kind == "wash":
        return DIGESTS["v31r2_wash_adapter"] + ":" + spec["wash"]
    if kind == "tarball":
        return DIGESTS["v22r1_tarball"]
    if kind == "file":
        if expert_id == "E8_DMITRII":
            return DIGESTS["dmitrii"]
        return DIGESTS["a7_standalone"]
    return "harness:PassiveAgent"


def telemetry(env):
    """Per-seat telemetry: money curve, market/unit/plant counters, step-0 wash."""
    from collections import Counter
    n = len(env.steps)
    money = [[], []]
    struct = [[], []]
    mkt = [Counter(), Counter()]
    unit = [Counter(), Counter()]
    plant = [Counter(), Counter()]
    sell_qty = [Counter(), Counter()]
    step0_market = [None, None]
    for i in range(n):
        for s in (0, 1):
            step = env.steps[i][s]
            farm = step["observation"]["farms"][s]
            money[s].append(farm.get("money", 0.0))
            act = step.get("action") or {}
            if i == 0:
                step0_market[s] = act.get("market") or []
            for o in (act.get("market") or []):
                if o:
                    mkt[s][(o[0], o[1] if len(o) > 1 else "")] += 1
                    if o[0] == "SELL" and len(o) > 2:
                        try:
                            sell_qty[s][o[1]] += int(o[2])
                        except (TypeError, ValueError):
                            pass
            units = [act.get("farmer")] + list(act.get("hands") or [])
            for u in units:
                if u:
                    unit[s][u[0]] += 1
                    if u[0] == "PLANT" and len(u) > 1:
                        plant[s][u[1]] += 1
            if i % 12 == 0:
                tiles = farm.get("tiles", []) or []
                pl = pa = wd = 0
                for row in tiles:
                    for t in row:
                        if isinstance(t, dict):
                            k = t.get("kind")
                            if k == "PLANT":
                                pl += 1
                            elif k == "PASTURE":
                                pa += 1
                            elif k == "WEED":
                                wd += 1
                struct[s].append([len(farm.get("hands", []) or []), pl, pa, wd,
                                  len(farm.get("unlocked_quadrants", []) or [])])
    hired = [mkt[s].get(("HIRE", ""), 0) for s in (0, 1)]
    fert = [unit[s].get("FERTILIZE", 0) for s in (0, 1)]
    collect = [unit[s].get("COLLECT_FERTILIZER", 0) for s in (0, 1)]
    # Wash capture: the engine logs the step-0 decision at steps[1] (verified
    # 2026-09-22: A7=[BUY30,SELL30], V3=[BUY50,SELL50] at index 1, empty at 0).
    first_wash = [None, None]
    for i in range(1, min(5, n)):
        for s in (0, 1):
            if first_wash[s] is None:
                m = (env.steps[i][s].get("action") or {}).get("market") or []
                if m:
                    first_wash[s] = m
    return {
        "money": money, "struct12": struct,
        "mkt": [{"/".join(k): v for k, v in mkt[s].items()} for s in (0, 1)],
        "unit": [dict(unit[s]) for s in (0, 1)],
        "plant": [dict(plant[s]) for s in (0, 1)],
        "sell_qty": [dict(sell_qty[s]) for s in (0, 1)],
        "hires": hired, "fertilize": fert, "collect": collect,
        "n_steps": n,
        "step0_market": step0_market,
        "first_wash": first_wash,
    }
