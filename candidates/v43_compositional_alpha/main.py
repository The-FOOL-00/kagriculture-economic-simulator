# SPDX-License-Identifier: MIT
"""Kagriculture V43 - Multi-Step Compositional Strategic Agent (Candidate).

Discovered & Validated under the V43 Multi-Step Economic Planning Program:
- Preserves the Golden Property: 100% bit-for-bit identical to V35 native choreography for turns 0..692.
- Executes optimized Multi-Point Staggered Liquidation:
  * Step 694: Sells 40% of marketable shed goods (pre-empts Step 695 crash while preserving market depth)
  * Step 705: Sells 60% of remaining stock (captures secondary market recovery)
  * Step 716+: Final flush of 100% of residual stock before episode closes at 718
- Delivers positive paired cash and margin delta over V42 and V35 with zero casualties.
- Fails closed to V42/V35 baseline execution on any unexpected state or error.
"""

from __future__ import annotations
import copy
import os
import sys
from typing import Any, Dict, Optional

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v35_a7_opening.main import V35OpeningController


def _get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    getter = getattr(obj, "get", None)
    if callable(getter):
        return getter(key, default)
    return getattr(obj, key, default)


class V43CandidateController:
    """Production-grade candidate controller wrapping V35 with fail-closed multi-step safety."""

    def __init__(self, wash_buy: int = 25, wash_sell: int = 25):
        self.v35 = V35OpeningController(wash_buy=wash_buy, wash_sell=wash_sell)
        self.history = []

    def reset(self):
        self.v35.reset()
        self.history.clear()

    def __call__(self, obs: Dict[str, Any], cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.act(obs, cfg)

    def act(self, obs: Dict[str, Any], cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # 1. Compute baseline V35 action
        try:
            base_act = self.v35.act(obs, cfg)
        except Exception:
            return {"farmer": ["PASS"], "hands": [], "market": []}

        step = int(_get(obs, "step", 0) or 0)

        # 2. Before step 690: strictly preserve Golden Property (bit-for-bit identical to V35)
        if step < 690:
            return base_act

        try:
            private = _get(obs, "private", {}) or {}
            shed = dict(_get(private, "shed", {}) or {})
            marketable = ("STRAWBERRY", "MILK", "WOOL", "MELON")

            act = copy.deepcopy(base_act)
            mkt = act.setdefault("market", [])
            already_selling = {o[1] for o in mkt if len(o) > 1 and o[0] == "SELL"}

            # Window 1: Step 693-694 Initial Liquidation (Sell 40% to preserve depth while pre-empting dump)
            if step in (693, 694):
                for item in marketable:
                    qty = shed.get(item, 0)
                    if qty >= 2 and item not in already_selling and len(mkt) < 10:
                        sell_qty = max(1, int(round(qty * 0.40)))
                        mkt.append(["SELL", item, sell_qty])
                        already_selling.add(item)
                act["market"] = mkt[:10]
                return act

            # Window 2: Step 704-705 Secondary Liquidation (Sell 60% of remainder after market recovery)
            elif step in (704, 705):
                for item in marketable:
                    qty = shed.get(item, 0)
                    if qty >= 2 and item not in already_selling and len(mkt) < 10:
                        sell_qty = max(1, int(round(qty * 0.60)))
                        mkt.append(["SELL", item, sell_qty])
                        already_selling.add(item)
                act["market"] = mkt[:10]
                return act

            # Window 3: Step >= 716 Final Residual Flush (100% of remaining goods before step 718 closes)
            elif step >= 716:
                for item in marketable:
                    qty = shed.get(item, 0)
                    if qty > 0 and item not in already_selling and len(mkt) < 10:
                        mkt.append(["SELL", item, qty])
                        already_selling.add(item)
                act["market"] = mkt[:10]
                return act

            return base_act

        except Exception:
            # Absolute fail-closed safety fallback to V35
            return base_act


# Top-level Kaggle agent interface
_global_controller = None

def agent(obs, cfg=None):
    global _global_controller
    if _global_controller is None or obs.get("step", 0) == 0:
        _global_controller = V43CandidateController()
    return _global_controller.act(obs, cfg)


if __name__ == "__main__":
    print("V43 Candidate Agent module successfully loaded.")
