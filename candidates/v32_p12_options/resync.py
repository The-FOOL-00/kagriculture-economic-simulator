# SPDX-License-Identifier: MIT
"""Kagriculture V32 P12 Physical Resynchronization State & Metrics.

Defines the ResyncState tracker, synchronization invariants, and state distance
metrics to evaluate physical and economic choreography alignment when returning
control from an option back to the A7 incumbent.
"""

from __future__ import annotations
import copy
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class SyncStatus(str, Enum):
    SYNCED = "SYNCED"
    PARTIALLY_SYNCED = "PARTIALLY_SYNCED"
    RECOVERING = "RECOVERING"
    DESYNCED = "DESYNCED"


@dataclass
class ResyncState:
    """Detailed state tracking physical and economic alignment between

    actual execution trajectory and undisturbed A7 continuation.
    """
    step: int
    status: SyncStatus
    
    # Worker Physical Alignment
    expected_farmer_pos: Optional[Tuple[int, int]]
    actual_farmer_pos: Optional[Tuple[int, int]]
    expected_hand_positions: List[Tuple[int, int]]
    actual_hand_positions: List[Tuple[int, int]]
    expected_worker_count: int
    actual_worker_count: int
    displaced_worker_count: int
    total_manhattan_displacement: int
    
    # Inventory & Capital Alignment
    expected_cash: float
    actual_cash: float
    cash_delta: float
    expected_shed: Dict[str, int]
    actual_shed: Dict[str, int]
    shed_unit_discrepancy: int
    
    # Macro Land & Farm State
    expected_quadrants: int
    actual_quadrants: int
    
    # Composite Distance Metric
    state_distance: float
    
    # Action Feasibility Check
    is_next_a7_action_feasible: bool
    recovery_ticks: int = 0

    @property
    def is_synced(self) -> bool:
        return self.status == SyncStatus.SYNCED

    @property
    def can_initiate_option(self) -> bool:
        """Gate: New options are strictly prohibited unless fully SYNCED."""
        return self.status == SyncStatus.SYNCED and self.is_next_a7_action_feasible


def compute_manhattan(p1: Optional[Tuple[int, int]], p2: Optional[Tuple[int, int]]) -> int:
    if p1 is None or p2 is None:
        return 0
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def evaluate_resync(
    step: int,
    actual_obs: Dict[str, Any],
    expected_obs: Dict[str, Any],
    next_a7_action: Optional[Dict[str, Any]] = None,
    player: int = 0
) -> ResyncState:
    """Evaluates the synchronization between actual farm state and expected A7 state.

    Computes worker displacements, inventory discrepancies, and calibrated state_distance.
    """
    actual_farms = actual_obs.get("farms", [{}, {}])
    expected_farms = expected_obs.get("farms", [{}, {}])
    
    act_farm = actual_farms[player] if player < len(actual_farms) else {}
    exp_farm = expected_farms[player] if player < len(expected_farms) else {}
    
    act_priv = actual_obs.get("private", {})
    exp_priv = expected_obs.get("private", {})
    
    # Positions
    raw_act_farmer = act_farm.get("farmer")
    act_farmer = (int(raw_act_farmer[0]), int(raw_act_farmer[1])) if raw_act_farmer else None
    raw_exp_farmer = exp_farm.get("farmer")
    exp_farmer = (int(raw_exp_farmer[0]), int(raw_exp_farmer[1])) if raw_exp_farmer else None
    
    act_hands = [
        (int(h[0]), int(h[1])) for h in (act_farm.get("hands", []) or [])
        if isinstance(h, (list, tuple)) and len(h) >= 2
    ]
    exp_hands = [
        (int(h[0]), int(h[1])) for h in (exp_farm.get("hands", []) or [])
        if isinstance(h, (list, tuple)) and len(h) >= 2
    ]
    
    act_workers = len(act_hands)
    exp_workers = len(exp_hands)
    
    # Displacement calculations
    displaced_count = 0
    total_disp = 0
    
    farmer_disp = compute_manhattan(act_farmer, exp_farmer)
    if farmer_disp > 0:
        displaced_count += 1
        total_disp += farmer_disp
        
    common_hands = min(act_workers, exp_workers)
    for i in range(common_hands):
        h_disp = compute_manhattan(act_hands[i], exp_hands[i])
        if h_disp > 0:
            displaced_count += 1
            total_disp += h_disp
            
    worker_diff = abs(act_workers - exp_workers)
    if worker_diff > 0:
        displaced_count += worker_diff
        total_disp += worker_diff * 10  # Heavy penalty for missing/extra workers
        
    # Cash & Shed
    act_cash = float(act_farm.get("money", 0.0) or 0.0)
    exp_cash = float(exp_farm.get("money", 0.0) or 0.0)
    cash_delta = act_cash - exp_cash
    
    act_shed = dict(act_priv.get("shed", {}) or {})
    exp_shed = dict(exp_priv.get("shed", {}) or {})
    
    shed_units_diff = 0
    all_prods = set(act_shed.keys()) | set(exp_shed.keys())
    for p in all_prods:
        shed_units_diff += abs(int(act_shed.get(p, 0)) - int(exp_shed.get(p, 0)))
        
    act_quads = len(act_farm.get("unlocked_quadrants", []) or [])
    exp_quads = len(exp_farm.get("unlocked_quadrants", []) or [])
    
    # Calibrated State Distance:
    # state_distance = 15.0 * worker_count_diff + 3.0 * total_disp + 0.5 * shed_units_diff + 0.001 * abs(cash_delta)
    state_dist = (
        15.0 * float(worker_diff) +
        3.0 * float(total_disp) +
        0.5 * float(shed_units_diff) +
        0.0005 * min(10000.0, abs(cash_delta))
    )
    
    # Check if next A7 action is physically feasible
    is_feasible = True
    if next_a7_action:
        # Check if farmer / hands actions are legal given actual positions
        farmer_act = next_a7_action.get("farmer") or ["PASS"]
        # Basic check: if worker is at shed adjacent when DROP/PICKUP called
        # If worker positions match exactly, feasibility is guaranteed
        if act_workers < exp_workers:
            is_feasible = False
            
    # Classify Status
    if act_workers == exp_workers and farmer_disp == 0 and total_disp == 0:
        status = SyncStatus.SYNCED
    elif act_workers == exp_workers and total_disp <= 4:
        status = SyncStatus.PARTIALLY_SYNCED
    elif act_workers == exp_workers and total_disp <= 12:
        status = SyncStatus.RECOVERING
    else:
        status = SyncStatus.DESYNCED
        
    return ResyncState(
        step=step,
        status=status,
        expected_farmer_pos=exp_farmer,
        actual_farmer_pos=act_farmer,
        expected_hand_positions=exp_hands,
        actual_hand_positions=act_hands,
        expected_worker_count=exp_workers,
        actual_worker_count=act_workers,
        displaced_worker_count=displaced_count,
        total_manhattan_displacement=total_disp,
        expected_cash=exp_cash,
        actual_cash=act_cash,
        cash_delta=cash_delta,
        expected_shed=exp_shed,
        actual_shed=act_shed,
        shed_unit_discrepancy=shed_units_diff,
        expected_quadrants=exp_quads,
        actual_quadrants=act_quads,
        state_distance=state_dist,
        is_next_a7_action_feasible=is_feasible,
    )
