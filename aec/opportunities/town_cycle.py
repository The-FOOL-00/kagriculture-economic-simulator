# SPDX-License-Identifier: MIT
"""Town Shop Demand and Economic Cycle Signal Architecture (§22)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from aec.config import SHOP_UNLOCK_INTERVAL, ScientificStatus
from aec.ir.economic_state import EconomicState
from aec.opportunities.base import Opportunity


@dataclass
class TownCycleSignal:
    """Probabilistic signal representing town economic cycle phase (§22).
    
    Treated as a prior / signal, never a guaranteed deterministic event.
    """
    step: int
    cycle_phase: float              # 0.0 to 1.0 within 72-step shop interval
    steps_to_next_unlock: int
    prior_price_bump_probability: float = 0.5
    recommended_timing_bias: str = "NEUTRAL"   # "HOLD_FOR_BUMP", "SELL_NOW", "NEUTRAL"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "cycle_phase": round(self.cycle_phase, 3),
            "steps_to_unlock": self.steps_to_next_unlock,
            "bump_prob": round(self.prior_price_bump_probability, 2),
            "timing_bias": self.recommended_timing_bias,
        }


class TownCycleSignalDetector:
    """Analyzes town shop unlock intervals and provides Bayesian timing priors."""

    def extract_signal(self, econ_state: EconomicState) -> TownCycleSignal:
        step = econ_state.step
        interval = SHOP_UNLOCK_INTERVAL  # 72
        next_unlock = ((step // interval) + 1) * interval
        steps_left = next_unlock - step
        phase = (step % interval) / float(interval)

        # In steps 60-71 of cycle, town demand refresh is imminent (higher bump likelihood)
        if steps_left <= 8:
            bias = "HOLD_FOR_BUMP"
            prob = 0.70
        elif phase <= 0.20:
            bias = "SELL_NOW"
            prob = 0.30
        else:
            bias = "NEUTRAL"
            prob = 0.50

        return TownCycleSignal(
            step=step,
            cycle_phase=phase,
            steps_to_next_unlock=steps_left,
            prior_price_bump_probability=prob,
            recommended_timing_bias=bias,
        )
