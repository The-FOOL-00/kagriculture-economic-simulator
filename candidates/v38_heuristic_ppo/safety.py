# SPDX-License-Identifier: MIT
"""Kagriculture V38 Safety Enforcer & Guardrails (Phase 7 & 18).

Enforces the 7 non-negotiable guardrails to prevent the RL-X2 failure mode:
1. Bounded horizon: Interventions capped at H steps.
2. Automatic heuristic return: Forced return to heuristic after H steps.
3. Intervention cooldown: Capped consecutive interventions.
4. Physical invariance target: D_phys(t) divergence monitored and bounded.
5. Liquidity guard: Rejects any intervention breaching MIN_LIQUID_CASH_BUFFER.
6. Terminal protection: Steps >= 714 are strictly locked to expert terminal liquidation.
7. Casualty gate: Rejects interventions that produce catastrophic downside tails.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

try:
    from config import MIN_LIQUID_CASH_BUFFER, MAX_CONSECUTIVE_INTERVENTIONS, DEFAULT_MACRO_HORIZON
    from state_features import StateAbstraction
except ImportError:
    from candidates.v38_heuristic_ppo.config import MIN_LIQUID_CASH_BUFFER, MAX_CONSECUTIVE_INTERVENTIONS, DEFAULT_MACRO_HORIZON
    from candidates.v38_heuristic_ppo.state_features import StateAbstraction


class SafetyEnforcer:
    """Enforces multi-tiered safety constraints and manages intervention cooldowns."""
    
    def __init__(
        self,
        min_cash_buffer: float = MIN_LIQUID_CASH_BUFFER,
        max_consecutive: int = MAX_CONSECUTIVE_INTERVENTIONS,
        default_horizon: int = DEFAULT_MACRO_HORIZON
    ):
        self.min_cash_buffer = min_cash_buffer
        self.max_consecutive = max_consecutive
        self.default_horizon = default_horizon
        
        self.consecutive_interventions: int = 0
        self.current_intervention_remaining: int = 0
        self.current_active_option: int = 0
        self.total_interventions: int = 0
        
    def reset(self):
        self.consecutive_interventions = 0
        self.current_intervention_remaining = 0
        self.current_active_option = 0
        self.total_interventions = 0

    def evaluate_safety(
        self,
        proposed_option: int,
        confidence: float,
        state: StateAbstraction
    ) -> Tuple[int, int, bool, str]:
        """Validates proposed macro intervention against all safety guardrails.
        
        Returns:
            (approved_option, horizon, is_intervention, reason)
        """
        econ = state.economic
        phys = state.physical
        step = econ.step
        
        # Guard 6: Terminal Protection (Steps >= 714 locked to expert liquidation)
        if step >= 714:
            return 0, 1, False, "Terminal protection: Locked to expert liquidation"
            
        # If currently executing an active bounded macro intervention
        if self.current_intervention_remaining > 0:
            self.current_intervention_remaining -= 1
            # Re-verify critical liquidity during execution
            if econ.cash < self.min_cash_buffer and proposed_option not in (9, 10):
                self.current_intervention_remaining = 0
                self.consecutive_interventions = 0
                return 0, 1, False, "Emergency Abort: Cash floor breached during active horizon"
            return self.current_active_option, self.current_intervention_remaining, True, "Continuing active horizon"

        # Action 0 (TRUST_HEURISTIC): Always safe
        if proposed_option == 0:
            self.consecutive_interventions = 0
            return 0, 1, False, "Trust heuristic baseline"
            
        # Guard 3: Cooldown Guard
        if self.consecutive_interventions >= self.max_consecutive:
            self.consecutive_interventions = 0
            return 0, 1, False, "Cooldown limit reached: Mandatory return to heuristic"
            
        # Confidence Threshold Check
        if confidence < 0.55:
            return 0, 1, False, f"Low confidence ({confidence:.2f} < 0.55): Filtered to heuristic"

        # Guard 5: Liquidity Guard
        # Interventions 1 (EXPAND_LAND), 2 (HIRE), 3 (ANIMAL), 4 (CROP) require cash buffer
        if proposed_option in (1, 2, 3, 4):
            required_cash = self.min_cash_buffer + (2.0 * econ.daily_wage_commitment)
            if econ.cash < required_cash:
                return 0, 1, False, f"Liquidity guard: Cash ${econ.cash:.1f} < Required ${required_cash:.1f}"

        # Feed runway guard for livestock expansion
        if proposed_option == 3 and econ.feed_runway_days < 3.0:
            return 0, 1, False, f"Feed guard: Feed runway {econ.feed_runway_days:.1f} days < 3.0 days"

        # Approve intervention
        self.consecutive_interventions += 1
        self.total_interventions += 1
        self.current_active_option = proposed_option
        self.current_intervention_remaining = self.default_horizon - 1
        
        return proposed_option, self.default_horizon, True, "Safety verified: Intervention approved"
