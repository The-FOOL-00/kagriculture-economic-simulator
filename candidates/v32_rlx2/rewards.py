# SPDX-License-Identifier: MIT
"""Kagriculture V32 RL-X2 Reward Formulations.

Implements R0 (terminal cash), R1 (A7-relative paired delta),
R2 (opponent margin), and R3 (potential-shaped economic progress).
"""

from __future__ import annotations
from typing import Any, Dict, Optional

try:
    from state import EconomicFeatures
except ImportError:
    from candidates.v32_rlx2.state import EconomicFeatures


def compute_potential(features: EconomicFeatures) -> float:
    """Computes economic potential Phi(s) in scaled units."""
    plant_val = sum(features.planted_crop_counts.values()) * 30.0
    animal_val = features.cow_count * 600.0 + features.sheep_count * 500.0 + features.goose_count * 300.0
    tot_wealth = features.cash + features.liquid_inventory_value + plant_val + animal_val
    return tot_wealth / 100000.0


def compute_step_reward(
    reward_mode: str,
    features: EconomicFeatures,
    prev_features: Optional[EconomicFeatures],
    is_terminal: bool,
    final_cash: float,
    a7_final_cash: Optional[float] = None,
    opp_final_cash: Optional[float] = None
) -> float:
    """Calculates step reward based on specified reward mode."""
    if reward_mode == "R0":
        # Terminal cash only
        if is_terminal:
            return final_cash / 100000.0
        return 0.0
        
    elif reward_mode == "R1":
        # A7-relative delta
        if is_terminal and a7_final_cash is not None:
            return (final_cash - a7_final_cash) / 10000.0
        elif is_terminal:
            return final_cash / 100000.0
        return 0.0
        
    elif reward_mode == "R2":
        # Opponent margin
        if is_terminal and opp_final_cash is not None:
            return (final_cash - opp_final_cash) / 10000.0
        return 0.0
        
    elif reward_mode == "R3":
        # Potential-based shaping: r' = gamma * Phi(s') - Phi(s)
        if prev_features is None:
            return 0.0
        phi_curr = compute_potential(features)
        phi_prev = compute_potential(prev_features)
        intermediate = phi_curr - phi_prev
        if is_terminal and a7_final_cash is not None:
            intermediate += (final_cash - a7_final_cash) / 10000.0
        return intermediate
        
    return 0.0
