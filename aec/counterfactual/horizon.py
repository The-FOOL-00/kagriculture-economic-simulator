# SPDX-License-Identifier: MIT
"""Adaptive Counterfactual Horizon Selector (§12, §22, Correction 0.3)."""

from __future__ import annotations

from aec.config import AECConfig
from aec.ir.economic_state import EconomicState
from aec.patches.patch import CoupledPatch


def select_adaptive_horizon(
    patch: CoupledPatch,
    econ_state: EconomicState,
    config: AECConfig
) -> int:
    """Select appropriate simulation horizon driven by patch dependency and game phase.
    
    AEC rejects global fixed H=24 in favor of:
    - SHORT (4–8 steps): cheap local events (weed dig, single move)
    - NORMAL (12–24 steps): standard economic patches (harvesting, market order frontload)
    - EXTENDED (24–48 steps): long dependency chains, town-cycle sync, terminal convergence
    """
    remaining = econ_state.remaining_horizon
    if remaining <= 1:
        return 1

    # Terminal endgame proximity overrides
    if remaining <= 12:
        return min(remaining, 12)

    # 1. Local / Short patches
    if "WEED_DIG" in patch.source_opportunity_id:
        h = config.short_horizon
    elif "FRONTLOAD" in patch.source_opportunity_id:
        h = config.short_horizon
    elif "TERMINAL_LIQUIDATE" in patch.source_opportunity_id:
        h = min(remaining, 2)
    # 2. Extended patches
    elif "PREEMPT" in patch.source_opportunity_id or "TOWN_CYCLE" in patch.source_opportunity_id:
        h = config.normal_horizon
    elif "SHUTDOWN" in patch.source_opportunity_id or "SWEEP" in patch.source_opportunity_id:
        h = min(remaining, config.extended_horizon)
    # 3. Normal economic patches
    else:
        h = max(patch.expected_horizon, config.normal_horizon)

    # Cap to remaining game steps and bounds
    return max(1, min(remaining, h))
