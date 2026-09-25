# SPDX-License-Identifier: MIT
"""Kagriculture V32 P10 Main Agent Entrypoint.

Orchestrates the P10 residual override architecture on top of the frozen A7 incumbent.
Architecture:
    Observation -> A7 Base Action -> Regime Detector -> (If Opportunity: Counterfactual Gate) -> Final Action
"""

from __future__ import annotations
import copy
from typing import Any, Dict, Optional

try:
    from config import P10Config
    from incumbent import A7Incumbent
    from telemetry import P10TelemetryLogger, ResidualDecision
except ImportError:
    from candidates.v32_p10.config import P10Config
    from candidates.v32_p10.incumbent import A7Incumbent
    from candidates.v32_p10.telemetry import P10TelemetryLogger, ResidualDecision


class P10Agent:
    def __init__(self, config: Optional[P10Config] = None):
        self.config = config or P10Config()
        self.incumbent = A7Incumbent()
        self.telemetry = P10TelemetryLogger()
        self.prev_observation: Optional[Dict[str, Any]] = None

    def __call__(self, observation: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        step = int(observation.get("step", 0) or 0)
        
        # 1. Base Incumbent (A7) Action
        base_action = self.incumbent.act(observation, configuration)
        
        # Safety invariant: If residual is permanently disabled, return A7 action directly
        if not self.config.residual_enabled:
            decision = ResidualDecision(
                step=step,
                active=False,
                trigger_id="NONE",
                trigger_reason="RESIDUAL_DISABLED",
                base_action=base_action,
                candidate_action=base_action,
                fallback_action=base_action
            )
            self.telemetry.record_decision(decision)
            self.prev_observation = observation
            return base_action

        # 2. Residual Execution Branch (Phase 2+ integration)
        # Residuals are evaluated and gated conservatively
        action = base_action
        try:
            # Placeholder for registered residuals when enabled
            decision = ResidualDecision(
                step=step,
                active=False,
                trigger_id="NONE",
                trigger_reason="NO_OPPORTUNITY",
                base_action=base_action,
                candidate_action=base_action,
                fallback_action=base_action
            )
            self.telemetry.record_decision(decision)
        except Exception:
            # Invariant fallback to A7 on any error
            self.telemetry.total_fallbacks += 1
            action = base_action
            
        self.prev_observation = observation
        return action


_default_agent = P10Agent(config=P10Config(residual_enabled=False))


def agent(observation: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Default Kaggle submission entrypoint for P10."""
    return _default_agent(observation, configuration)


def make_p10_agent(config: Optional[P10Config] = None):
    """Factory creating an isolated P10 agent instance."""
    inst = P10Agent(config=config)
    def _act(obs, cfg=None):
        return inst(obs, cfg)
    return _act, inst
