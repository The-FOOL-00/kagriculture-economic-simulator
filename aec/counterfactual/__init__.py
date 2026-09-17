# SPDX-License-Identifier: MIT
"""AEC Counterfactual Simulator Package."""

from aec.counterfactual.horizon import select_adaptive_horizon
from aec.counterfactual.opponent_pressure import OpponentPressureModel
from aec.counterfactual.simulator import CounterfactualSimulator, SimulationOutcome

__all__ = [
    "select_adaptive_horizon",
    "OpponentPressureModel",
    "CounterfactualSimulator",
    "SimulationOutcome",
]
