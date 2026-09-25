# SPDX-License-Identifier: MIT
"""V37: Build clean staging directory for V35 final submission bundle.

Embeds verified A7 standalone bytes verbatim into a self-contained main.py.
Applies verified V35 opening intervention (25/25 wheat wash at step 0).
Pure Python stdlib, zero external imports, zero filesystem lookups.
"""

import hashlib
import os
import shutil

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
A7_PATH = os.path.join(REPO_ROOT, "candidates", "v30_a7_standalone", "main.py")
V35_PATH = os.path.join(REPO_ROOT, "candidates", "v35_a7_opening", "main.py")
STAGING_DIR = os.path.join(REPO_ROOT, "submission_final_v35")

A7_EXPECTED_SHA = "51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f"
V35_EXPECTED_SHA = "1959021bdb1aeff720732aec866f5c9f3c9fa0b259ee0ab25982bda367593249"


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


STAGING_TEMPLATE = '''# SPDX-License-Identifier: MIT
"""Kagriculture V35 Opening Controller (Competition Submission).

Architecture:
1. Evaluates intended A7 action via embedded A7 standalone engine (sha256: {a7_sha}).
2. At step 0, executes optimized opening capital allocation (25/25 wheat wash),
   preserving ~$125 in critical working capital to prevent order bouncing and early purchase delay.
3. At steps 1..718, delegates 100% bit-identically to A7 (zero downstream drift, D(t) -> 0).
4. Strict fail-closed fallback to A7 / safe pass on any unexpected condition.
Stdlib only, zero external packages, zero filesystem lookups.
"""

from __future__ import annotations
import copy
from typing import Any, Dict, List, Optional

_A7_SRC = {a7_src!r}
_A7_NS = {{"__name__": "v35_a7_inner"}}
exec(compile(_A7_SRC.decode("utf-8"), "v35_a7_inner.py", "exec"), _A7_NS)
_A7_AGENT = _A7_NS["agent"]
del _A7_SRC

_WASH25 = [["BUY_PRODUCT", "WHEAT", 25], ["SELL", "WHEAT", 25]]
_SAFE = {{"farmer": ["PASS"], "hands": [], "market": []}}


class V35OpeningController:
    """Production competition controller with fail-closed A7 safety."""

    def __init__(self, wash_buy: int = 25, wash_sell: int = 25, enable_optimization: bool = True):
        self.wash_buy = wash_buy
        self.wash_sell = wash_sell
        self.enable_optimization = enable_optimization
        self.interventions_count = 0

    def reset(self):
        self.interventions_count = 0

    def __call__(self, observation: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.act(observation, configuration)

    def act(self, observation: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # 1. Base A7 action
        try:
            base_action = _A7_AGENT(observation, configuration)
            if not isinstance(base_action, dict):
                base_action = dict(_SAFE)
        except Exception:
            return dict(_SAFE)

        if not self.enable_optimization:
            return base_action

        # 2. Step 0 Opening Optimization
        try:
            step = int(observation.get("step", 0) or 0)
            if step == 0:
                act = copy.deepcopy(base_action)
                if self.wash_buy == 0 and self.wash_sell == 0:
                    act["market"] = []
                else:
                    act["market"] = [
                        ["BUY_PRODUCT", "WHEAT", self.wash_buy],
                        ["SELL", "WHEAT", self.wash_sell]
                    ]
                self.interventions_count += 1
                return act

            # Steps 1..718: 100% bit-identical A7
            return base_action

        except Exception:
            # Fail-closed: always execute A7 on error
            return base_action


_CONTROLLER = V35OpeningController()


def agent(observation: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Kaggle-compliant submission agent function."""
    global _CONTROLLER
    try:
        step = int(observation.get("step", 0) or 0)
    except Exception:
        step = -1
    if step <= 0:
        _CONTROLLER.reset()
    try:
        out = _CONTROLLER.act(observation, configuration)
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


def build():
    # 1. Verify frozen inputs
    a7_sha = sha256_file(A7_PATH)
    assert a7_sha == A7_EXPECTED_SHA, f"A7 drift: {a7_sha}"
    v35_sha = sha256_file(V35_PATH)
    assert v35_sha == V35_EXPECTED_SHA, f"V35 drift: {v35_sha}"
    print(f"Verified A7: {a7_sha}")
    print(f"Verified V35 dev: {v35_sha}")

    # 2. Create clean staging directory
    if os.path.exists(STAGING_DIR):
        shutil.rmtree(STAGING_DIR)
    os.makedirs(STAGING_DIR, exist_ok=True)

    # 3. Read A7 source bytes
    with open(A7_PATH, "rb") as f:
        a7_bytes = f.read()

    # 4. Format staging main.py
    staged_src = STAGING_TEMPLATE.format(a7_sha=a7_sha, a7_src=a7_bytes)
    out_file = os.path.join(STAGING_DIR, "main.py")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(staged_src)

    out_size = os.path.getsize(out_file)
    out_sha = sha256_file(out_file)
    print(f"Wrote {out_file}: {out_size} bytes, SHA-256: {out_sha}")


if __name__ == "__main__":
    build()
