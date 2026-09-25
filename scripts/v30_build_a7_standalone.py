# SPDX-License-Identifier: MIT
"""V30: build A7-standalone submission source from frozen V3 bytes.

A7 (V27-ABL-A7) exists only as a lab adapter: call V3, and at step 0 ONLY,
if V3's market is exactly [BUY_PRODUCT WHEAT 50, SELL WHEAT 50], resize to
[.. 30, .. 30]. This builder emits a self-contained main.py that embeds the
frozen V3 source verbatim and applies the identical rewrite at the same
layer as V3's own wrappers (planner output, pre-return).

Inputs (read-only, verified by SHA256, never modified):
  submission_Vj_kc_v3.tar.gz  (V3_SHA)
  aec/backbone/v27_ablation_adapters.py (A7_FILE_SHA, for the exact rule)

Output: candidates/v30_a7_standalone/main.py (+ build manifest)

Equivalence is verified behaviorally (dollar-identical rewards + action
digests vs the adapter), not by inspection.
"""

import hashlib
import os
import tarfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

V3_SHA = "845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943"
A7_FILE_SHA = "18d2c8ea2cf826b0bef71c96988dba0c93d7dbcc73936a0c99f07cb0539e7ae9"

OUT_DIR = os.path.join(REPO_ROOT, "candidates", "v30_a7_standalone")

TEMPLATE = '''# V30 A7-standalone submission.
# Base: frozen V3 (submission_Vj_kc_v3.tar.gz, sha256 {v3sha}) embedded
# VERBATIM below as _V3_SRC (V3's own header/attribution preserved inside).
# A7 change (from frozen aec/backbone/v27_ablation_adapters.py {a7sha}):
# at game step 0 ONLY, if V3's market action is exactly
# [["BUY_PRODUCT","WHEAT",50],["SELL","WHEAT",50]], resize to 30/30.
# All other steps/shapes: bit-identical to V3. No AEC, no network, stdlib only.

_V3_SRC = {v3src!r}
_V3_NS = {{"__name__": "v30_a7_v3_inner"}}
exec(compile(_V3_SRC.decode("utf-8"), "v30_a7_v3_inner.py", "exec"), _V3_NS)
_V3_AGENT = _V3_NS["agent"]
del _V3_SRC

_WASH50 = [["BUY_PRODUCT", "WHEAT", 50], ["SELL", "WHEAT", 50]]
_WASH30 = [["BUY_PRODUCT", "WHEAT", 30], ["SELL", "WHEAT", 30]]


def _inner(observation, configuration=None):
    action = _V3_AGENT(observation, configuration)
    if not isinstance(action, dict):
        action = {{"farmer": ["PASS"], "hands": [], "market": []}}
    try:
        step = int(observation.get("step", 0) or 0)
    except Exception:
        step = -1
    if step == 0 and action.get("market") == _WASH50:
        action = dict(action)
        action["market"] = [list(o) for o in _WASH30]
    return action


_SAFE = {{"farmer": ["PASS"], "hands": [], "market": []}}


def agent(observation, configuration=None):
    try:
        out = _inner(observation, configuration)
        if not isinstance(out, dict):
            return dict(_SAFE)
        out.setdefault("farmer", ["PASS"])
        out.setdefault("hands", [])
        out.setdefault("market", [])
        if not isinstance(out["hands"], list):
            out["hands"] = []
        if not isinstance(out["market"], list):
            out["market"] = []
        out["market"] = out["market"][:10]
        return out
    except Exception:
        return dict(_SAFE)
'''


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    v3_path = os.path.join(REPO_ROOT, "submission_Vj_kc_v3.tar.gz")
    a7_path = os.path.join(REPO_ROOT, "aec", "backbone",
                           "v27_ablation_adapters.py")
    assert sha256_file(v3_path) == V3_SHA, "V3 tarball drift"
    assert sha256_file(a7_path) == A7_FILE_SHA, "A7 adapter drift"
    with tarfile.open(v3_path, "r:gz") as tar:
        v3_code = tar.extractfile("main.py").read()
    os.makedirs(OUT_DIR, exist_ok=True)
    src = TEMPLATE.format(v3sha=V3_SHA, a7sha=A7_FILE_SHA, v3src=v3_code)
    out_path = os.path.join(OUT_DIR, "main.py")
    with open(out_path, "w") as f:
        f.write(src)
    print("wrote %s (%d bytes, sha256 %s)" % (
        out_path, len(src), sha256_file(out_path)))


if __name__ == "__main__":
    main()
