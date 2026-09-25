# SPDX-License-Identifier: MIT
"""Kagriculture V35 Opening Controller (Competition Candidate).

Architecture:
1. Evaluates intended A7 action via protected A7 standalone engine.
2. At step 0, executes optimized opening capital allocation (25/25 wheat wash),
   preserving ~$125 in critical working capital to prevent order bouncing and early purchase delay.
3. At steps 1..718, delegates 100% bit-identically to A7 (zero downstream drift, D(t) -> 0).
4. Strict fail-closed fallback to A7 on any unexpected condition.
"""

from __future__ import annotations
import copy
import os
import sys
from typing import Any, Dict, List, Optional

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.v32_common import load_agent


class V35OpeningController:
    """Production competition controller with fail-closed A7 safety."""

    def __init__(self, wash_buy: int = 25, wash_sell: int = 25, enable_optimization: bool = True):
        self.wash_buy = wash_buy
        self.wash_sell = wash_sell
        self.enable_optimization = enable_optimization
        self.a7_agent = load_agent("E9_AST")
        self.interventions_count = 0

    def reset(self):
        self.a7_agent = load_agent("E9_AST")
        self.interventions_count = 0

    def __call__(self, observation: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.act(observation, configuration)

    def act(self, observation: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # 1. Base A7 action
        try:
            base_action = self.a7_agent.act(observation, configuration)
        except Exception:
            return {"farmer": ["PASS"], "hands": [], "market": []}

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
    return _CONTROLLER.act(observation, configuration)
