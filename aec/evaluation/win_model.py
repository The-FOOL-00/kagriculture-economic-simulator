# SPDX-License-Identifier: MIT
"""Lexicographic Win and Margin Evaluation Model (§14, §23, Correction 0.2, Correction 0.5)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from aec.counterfactual.simulator import SimulationOutcome
from aec.ir.economic_state import EconomicState
from aec.patches.patch import CoupledPatch


class LeadState(str, Enum):
    """Extension point for lead-aware endgame control (§28, Correction 0.5)."""
    AHEAD = "AHEAD"     # Net margin > +$1,000
    CLOSE = "CLOSE"     # Net margin in [-$1,000, +$1,000]
    BEHIND = "BEHIND"   # Net margin < -$1,000


@dataclass
class EvaluationResult:
    """Strategic evaluation output for a candidate patch."""
    patch_id: str
    expected_p_win: float
    terminal_margin_delta: float
    our_money_delta: float
    opponent_money_delta: float
    lead_state: LeadState
    temporary_sacrifice_accepted: bool
    is_superior: bool
    rationale: str

    def to_dict(self):
        return {
            "patch_id": self.patch_id,
            "p_win": round(self.expected_p_win, 4),
            "margin_delta": round(self.terminal_margin_delta, 2),
            "our_money_delta": round(self.our_money_delta, 2),
            "opp_money_delta": round(self.opponent_money_delta, 2),
            "lead_state": self.lead_state.value,
            "sacrifice_accepted": self.temporary_sacrifice_accepted,
            "is_superior": self.is_superior,
            "rationale": self.rationale,
        }


class WinModel:
    """Evaluates candidate simulations under the AEC lexicographic hierarchy."""

    @staticmethod
    def get_lead_state(our_cash: float, opp_cash: float) -> LeadState:
        gap = our_cash - opp_cash
        if gap > 1000.0:
            return LeadState.AHEAD
        elif gap < -1000.0:
            return LeadState.BEHIND
        else:
            return LeadState.CLOSE

    def estimate_p_win(self, current_gap: float, margin_delta: float) -> float:
        """Sigmoid approximation of win probability given projected margin."""
        projected_margin = current_gap + margin_delta
        # Scale factor calibrated such that $1,000 margin difference gives ~73% win prob
        scale = 1000.0
        return 1.0 / (1.0 + math.exp(-projected_margin / scale))

    def evaluate(
        self,
        patch: CoupledPatch,
        outcome: SimulationOutcome,
        econ_state: EconomicState
    ) -> EvaluationResult:
        current_gap = econ_state.farm.cash - econ_state.opponent.observed_cash
        lead_state = self.get_lead_state(econ_state.farm.cash, econ_state.opponent.observed_cash)
        
        base_p_win = self.estimate_p_win(current_gap, 0.0)
        cand_p_win = self.estimate_p_win(current_gap, outcome.delta_terminal_margin)

        # Temporary sacrifice principle (§16, §24, Correction 0.2):
        # Allow our_money_delta < 0 if terminal margin or win probability improves
        temp_sacrifice = outcome.delta_our_money < 0.0 and outcome.delta_terminal_margin > 0.0

        # Primary criterion: P(WIN); Secondary: Terminal Margin; Tertiary: Own Money
        p_win_gain = cand_p_win - base_p_win
        is_superior = False
        rationale = ""

        if p_win_gain > 0.005:  # meaningful win prob advantage
            is_superior = True
            rationale = f"Improves P(WIN) by +{p_win_gain*100:.2f}% (margin delta +${outcome.delta_terminal_margin:.1f})"
        elif outcome.delta_terminal_margin > 15.0:
            is_superior = True
            rationale = f"Positive margin delta: +${outcome.delta_terminal_margin:.1f}"
        elif outcome.delta_our_money > 20.0 and outcome.delta_terminal_margin >= 0.0:
            is_superior = True
            rationale = f"Net money gain +${outcome.delta_our_money:.1f} with non-negative margin delta"
        else:
            is_superior = False
            rationale = f"Insufficient strategic advantage (margin delta ${outcome.delta_terminal_margin:.1f}, money delta ${outcome.delta_our_money:.1f})"

        return EvaluationResult(
            patch_id=patch.patch_id,
            expected_p_win=cand_p_win,
            terminal_margin_delta=outcome.delta_terminal_margin,
            our_money_delta=outcome.delta_our_money,
            opponent_money_delta=outcome.delta_opponent_money,
            lead_state=lead_state,
            temporary_sacrifice_accepted=temp_sacrifice,
            is_superior=is_superior,
            rationale=rationale
        )
