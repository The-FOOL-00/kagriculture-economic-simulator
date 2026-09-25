# SPDX-License-Identifier: MIT
"""Kagriculture V39 Live-Targeted Controller (Research Candidate).

Architecture:
1. Production baseline: 100% frozen V35 reference engine.
2. Step 0: Preserves V35's 25/25 wheat wash opening.
3. Steps 1..692: 100% bit-identical V35 execution.
4. Steps 693..694 (Day 28 Liquidation Guard):
   Detects unliquidated high-value perishable inventory in the farm shed
   (STRAWBERRY, MILK, WOOL) that V35's static route tape omits, and emits
   preemptive market sell orders before opponent dumps crash market prices.
5. Steps 695..719: 100% bit-identical V35 execution.
6. Fail-closed safety: Any exception falls back immediately to base V35 action.
"""

from __future__ import annotations
import copy
import os
import sys
from typing import Any, Dict, List, Optional

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v35_a7_opening.main import V35OpeningController


class V39TargetedController:
    """Production candidate wrapper with V35 baseline and targeted endgame liquidation."""

    def __init__(self, enable_liquidation_guard: bool = True):
        self.v35_controller = V35OpeningController()
        self.enable_liquidation_guard = enable_liquidation_guard
        self.interventions_count = 0

    def reset(self):
        self.v35_controller.reset()
        self.interventions_count = 0

    def __call__(self, observation: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.act(observation, configuration)

    def act(self, observation: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # 1. Base V35 action (fail-closed baseline)
        try:
            v35_action = self.v35_controller.act(observation, configuration)
        except Exception:
            return {"farmer": ["PASS"], "hands": [], "market": []}

        if not self.enable_liquidation_guard:
            return v35_action

        # 2. Targeted Endgame Liquidation Guard (Steps 693-694)
        try:
            step = int(observation.get("step", 0) or 0)
            if step in (693, 694):
                shed = observation.get("private", {}).get("shed", {})
                if not shed:
                    return v35_action

                act = copy.deepcopy(v35_action)
                mkt = act.setdefault("market", [])
                already_selling = {o[1] for o in mkt if len(o) > 1 and o[0] == "SELL"}

                # Items to flush before opponent dumps crash market prices
                flush_targets = ("STRAWBERRY", "MILK", "WOOL")
                modified = False
                for item in flush_targets:
                    qty = shed.get(item, 0)
                    if qty > 0 and item not in already_selling and len(mkt) < 10:
                        mkt.append(["SELL", item, qty])
                        modified = True

                if modified:
                    self.interventions_count += 1
                return act

            return v35_action

        except Exception:
            # Strict fail-closed fallback to base V35 action
            return v35_action


_CONTROLLER = V39TargetedController()


def agent(observation: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Kaggle-compliant submission agent function."""
    global _CONTROLLER
    try:
        step = int(observation.get("step", 0) or 0)
    except Exception:
        step = -1
    if step <= 0:
        _CONTROLLER.reset()
    return _CONTROLLER.act(observation, configuration)
