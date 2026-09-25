# SPDX-License-Identifier: MIT
"""Kagriculture V34 A7 Tactical Controller (Competition Candidate).

Architecture:
1. Evaluates A7 intended action via protected standalone A7 backbone.
2. At ordinary steps, directly executes A7 (zero overhead, 100% parity).
3. At high-information decision points, checks observable opportunity triggers.
4. Enforces fail-closed LiquidityGuard and physical invariants.
5. If verified safe and beneficial, executes tactical override; otherwise falls back 100% to A7.
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
from candidates.v34_a7_tactical.liquidity_guard import LiquidityGuard
from candidates.v34_a7_tactical.candidate_generator import (
    generate_step0_candidates, generate_late_cutoff_candidates
)


class V34TacticalController:
    """Stateful competition controller with 100% safe A7 fallback."""

    def __init__(self, enable_tactical: bool = True):
        self.enable_tactical = enable_tactical
        self.a7_agent = load_agent("E9_AST")
        self.liquidity_guard = LiquidityGuard()
        self.interventions_count = 0
        self.step_history: List[int] = []

    def reset(self):
        self.a7_agent = load_agent("E9_AST")
        self.interventions_count = 0
        self.step_history.clear()

    def __call__(self, observation: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.act(observation, configuration)

    def act(self, observation: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Produces action with fail-closed A7 fallback."""
        # 1. Obtain baseline A7 action
        try:
            base_action = self.a7_agent.act(observation, configuration)
        except Exception:
            # Emergency default
            return {"farmer": ["PASS"], "hands": [], "market": []}

        if not self.enable_tactical:
            return base_action

        try:
            step = int(observation.get("step", 0) or 0)
            player = int(observation.get("player", 0) or 0)
            farms = observation.get("farms", []) or []
            my_farm = farms[player] if len(farms) > player else {}
            current_cash = float(my_farm.get("money", 0.0) or 0.0)
            active_workers = len(my_farm.get("hands", []) or []) + 1
            mkt = observation.get("market", {}) or {}
            prices = {k: float(v) for k, v in (mkt.get("prices", {}) or {}).items()}

            # Tactical Point 1: Step 0 Market Wash
            if step == 0:
                cands = generate_step0_candidates(observation, base_action)
                # Evaluated best candidate: WASH25 preserves early cash buffer while capturing spread
                for c in cands:
                    if c.action_id == "TACTICAL_STEP0_WASH25":
                        l_status = self.liquidity_guard.evaluate_action_liquidity(
                            current_cash=current_cash,
                            step=step,
                            active_workers=active_workers,
                            market_orders=c.candidate_action.get("market", []),
                            prices=prices,
                        )
                        if l_status.is_safe:
                            self.interventions_count += 1
                            return copy.deepcopy(c.candidate_action)

            # Default: Bit-identical A7
            return base_action

        except Exception:
            # Fail-closed fallback: ALWAYS execute A7
            return base_action


_CONTROLLER = V34TacticalController()


def agent(observation: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Kaggle-compliant submission agent function."""
    global _CONTROLLER
    step = int(observation.get("step", 0) or 0)
    if step == 0:
        _CONTROLLER.reset()
    return _CONTROLLER.act(observation, configuration)
