# SPDX-License-Identifier: MIT
"""V33 Public Meta Replication Module.

Replication and empirical evaluation of public meta-strategy principles:
1. v27 Midgame Meta Reset (sparse evaluation at checkpoint boundaries)
2. v25 Fast Routes / Sparse Route Switching
3. Strict-Future Evaluation Protocol
"""

from __future__ import annotations
import copy
from typing import Any, Callable, Dict, List, Optional, Tuple


class PublicMetaReplication:
    """Evaluates public meta-reset mechanisms in an isolated, leak-free test harness."""

    def __init__(
        self,
        base_route: Callable,
        candidate_routes: Dict[str, Callable],
        reset_steps: Tuple[int, ...] = (48, 144, 288),
        confidence_threshold: float = 3000.0,
    ):
        self.base_route = base_route
        self.candidate_routes = candidate_routes
        self.reset_steps = reset_steps
        self.confidence_threshold = confidence_threshold
        self.active_route_id = "R0_A7"
        self.active_agent = base_route
        self.switches_performed = 0

    def reset(self):
        self.active_route_id = "R0_A7"
        self.active_agent = self.base_route
        self.switches_performed = 0

    def step(self, obs: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        step = int(obs.get("step", 0) or 0)

        # Midgame Meta Reset Checkpoint
        if step in self.reset_steps and self.switches_performed == 0:
            selected_route = self._evaluate_meta_reset(obs)
            if selected_route != self.active_route_id:
                self.active_route_id = selected_route
                self.active_agent = self.candidate_routes.get(selected_route, self.base_route)
                self.switches_performed += 1

        try:
            return self.active_agent(obs, configuration)
        except Exception:
            # Fallback to base route if switched agent fails
            return self.base_route(obs, configuration)

    def _evaluate_meta_reset(self, obs: Dict[str, Any]) -> str:
        """Evaluates whether observable signals justify a meta reset.
        Uses ONLY causal, observable features available at step t.
        """
        # Feature extraction from observable history
        mkt = obs.get("market", {}) or {}
        prices = mkt.get("prices", {}) or {}
        inv = mkt.get("inventory", {}) or {}

        wheat_price = float(prices.get("WHEAT", 25) or 25)
        carrot_price = float(prices.get("CARROT", 35) or 35)
        wheat_inv = int(inv.get("WHEAT", 10000) or 10000)

        # High crop market saturation signature (opponent flooding bakery/crop market)
        if wheat_price <= 18 and wheat_inv > 11000 and "R2_DMITRII" in self.candidate_routes:
            return "R2_DMITRII"

        return "R0_A7"
