# SPDX-License-Identifier: MIT
"""AEC Phase 006: Coupled Trajectory-Preserving Patch Model (§3-§7).

Implements the formal CoupledPatch abstraction, precondition/postcondition model,
trajectory-preservation contract, and patch state machine.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


class CoupledPatchState(str, Enum):
    """Coupled patch lifecycle state machine (§9)."""
    PROPOSED = "PROPOSED"
    FEASIBILITY_CHECK = "FEASIBILITY_CHECK"
    ROUTE_TO_TARGET = "ROUTE_TO_TARGET"
    EXECUTE_TARGET = "EXECUTE_TARGET"
    CARGO_RESOLUTION = "CARGO_RESOLUTION"
    ROUTE_TO_RECONNECT_OR_DEPOSIT = "ROUTE_TO_RECONNECT_OR_DEPOSIT"
    RECONNECT = "RECONNECT"
    VERIFY_POSTCONDITION = "VERIFY_POSTCONDITION"
    COUNTERFACTUAL = "COUNTERFACTUAL"
    SAFETY = "SAFETY"
    ECONOMIC_GATE = "ECONOMIC_GATE"
    COMMITTED = "COMMITTED"
    ABSTAINED = "ABSTAINED"

    # Terminal failure states (§9)
    INFEASIBLE = "INFEASIBLE"
    ROUTE_FAILURE = "ROUTE_FAILURE"
    CARGO_UNRESOLVED = "CARGO_UNRESOLVED"
    DEPENDENCY_FAILURE = "DEPENDENCY_FAILURE"
    RECONNECT_FAILURE = "RECONNECT_FAILURE"
    POSTCONDITION_FAILURE = "POSTCONDITION_FAILURE"
    TERMINAL_RISK = "TERMINAL_RISK"
    COUNTERFACTUAL_FAILURE = "COUNTERFACTUAL_FAILURE"
    SAFETY_FAILURE = "SAFETY_FAILURE"
    ECONOMIC_FAILURE = "ECONOMIC_FAILURE"
    STALE_BASELINE = "STALE_BASELINE"


@dataclass
class PatchPrecondition:
    """Explicit preconditions assumed by the coupled patch (§5)."""
    worker_positions: Dict[int, Tuple[int, int]] = field(default_factory=dict)
    worker_cargo: Dict[int, Dict[str, int]] = field(default_factory=dict)
    shed_inventory: Dict[str, int] = field(default_factory=dict)
    shed_capacity_remaining: int = 0
    required_tiles: Dict[Tuple[int, int], Dict[str, Any]] = field(default_factory=dict)
    earliest_start_step: int = 0
    latest_start_step: int = 720
    is_met: bool = True
    unmet_reasons: List[str] = field(default_factory=list)

    def verify(self, actual_econ_state: Any) -> bool:
        """Verify precondition against an actual economic state."""
        reasons: List[str] = []
        if actual_econ_state is None:
            self.is_met = False
            self.unmet_reasons = ["EconState is None"]
            return False

        # 1. Step bounds
        step = getattr(actual_econ_state, "step", 0)
        if not (self.earliest_start_step <= step <= self.latest_start_step):
            reasons.append(f"Step {step} outside valid window [{self.earliest_start_step}, {self.latest_start_step}]")

        # 2. Worker positions and cargo
        if hasattr(actual_econ_state, "workers") and actual_econ_state.workers:
            for wid, expected_pos in self.worker_positions.items():
                w = actual_econ_state.workers.get_worker(wid)
                if not w:
                    reasons.append(f"Worker {wid} does not exist in state")
                    continue
                if w.position != expected_pos:
                    reasons.append(f"Worker {wid} pos {w.position} != expected {expected_pos}")

            for wid, expected_cargo in self.worker_cargo.items():
                w = actual_econ_state.workers.get_worker(wid)
                if w:
                    for item, qty in expected_cargo.items():
                        act_qty = w.cargo.get(item, 0)
                        if act_qty != qty:
                            reasons.append(f"Worker {wid} cargo {item}={act_qty} != expected {qty}")

        # 3. Required tiles (e.g. mature plant)
        if hasattr(actual_econ_state, "farm") and actual_econ_state.farm:
            tiles = actual_econ_state.farm.tiles
            for (tx, ty), req in self.required_tiles.items():
                if 0 <= ty < len(tiles) and 0 <= tx < len(tiles[0]):
                    t = tiles[ty][tx]
                    if req.get("kind") and t.get("kind") != req["kind"]:
                        reasons.append(f"Tile ({tx}, {ty}) kind {t.get('kind')} != {req['kind']}")
                    if req.get("crop") and t.get("crop") != req["crop"]:
                        reasons.append(f"Tile ({tx}, {ty}) crop {t.get('crop')} != {req['crop']}")
                    if req.get("min_yield") and t.get("yield_units", 0) < req["min_yield"]:
                        reasons.append(f"Tile ({tx}, {ty}) yield {t.get('yield_units')} < {req['min_yield']}")
                else:
                    reasons.append(f"Tile ({tx}, {ty}) out of bounds")

        self.unmet_reasons = reasons
        self.is_met = (len(reasons) == 0)
        return self.is_met


@dataclass
class PatchPostcondition:
    """Guarantees delivered by the coupled patch at completion (§5)."""
    worker_positions: Dict[int, Tuple[int, int]] = field(default_factory=dict)
    worker_cargo: Dict[int, Dict[str, int]] = field(default_factory=dict)
    shed_inventory: Dict[str, int] = field(default_factory=dict)
    delivered_resources: Dict[str, int] = field(default_factory=dict)
    cash_delta: float = 0.0
    baseline_reconnect_step: int = 0
    baseline_executable: bool = True
    is_satisfied: bool = True
    violation_reasons: List[str] = field(default_factory=list)


@dataclass
class PatchStateDelta:
    """State transitions caused by patch execution (§4)."""
    cash_delta: float = 0.0
    cargo_delta: Dict[int, Dict[str, int]] = field(default_factory=dict)
    shed_delta: Dict[str, int] = field(default_factory=dict)
    tiles_delta: Dict[Tuple[int, int], Dict[str, Any]] = field(default_factory=dict)
    worker_pos_delta: Dict[int, Tuple[Tuple[int, int], Tuple[int, int]]] = field(default_factory=dict)


@dataclass
class TrajectoryPreservationCertificate:
    """Formal proof that baseline suffix assumptions remain strictly preserved (§6)."""
    is_valid: bool = True
    worker_positions_aligned: bool = True
    cargo_state_consistent: bool = True
    worker_task_state_compatible: bool = True
    shed_inventory_accounted: bool = True
    resource_state_accounted: bool = True
    timing_shift: int = 0
    timing_feasible: bool = True
    dependencies_intact: bool = True
    terminal_feasibility_ok: bool = True
    multiworker_collision_free: bool = True
    rejection_reasons: List[str] = field(default_factory=list)

    def verify_all(self) -> bool:
        reasons: List[str] = []
        if not self.worker_positions_aligned:
            reasons.append("Worker positions desynchronized at reconnect")
        if not self.cargo_state_consistent:
            reasons.append("Cargo state inconsistent with baseline expectation")
        if not self.worker_task_state_compatible:
            reasons.append("Worker task state incompatible with subsequent baseline obligation")
        if not self.shed_inventory_accounted:
            reasons.append("Shed/inventory unaccounted for in economic state")
        if not self.resource_state_accounted:
            reasons.append("Resource inputs/outputs unaccounted for")
        if not self.timing_feasible:
            reasons.append(f"Timing shift {self.timing_shift} breaks downstream schedule")
        if not self.dependencies_intact:
            reasons.append("Baseline prerequisite invalidated")
        if not self.terminal_feasibility_ok:
            reasons.append("Execution pushes realization beyond terminal boundary")
        if not self.multiworker_collision_free:
            reasons.append("Multi-worker collision or edge-swap detected")

        self.rejection_reasons = reasons
        self.is_valid = (len(reasons) == 0)
        return self.is_valid


@dataclass
class CoupledPatchStep:
    """A discrete time step within a coupled trajectory patch (§4)."""
    relative_step: int
    step_number: int
    worker_actions: Dict[int, List[str]]
    worker_positions: Dict[int, Tuple[int, int]]
    market_orders: Optional[List[List[Any]]] = None
    description: str = ""


@dataclass
class CoupledPatchRequest:
    """Input query to generate a coupled trajectory patch (§4, §8)."""
    opportunity_id: str
    mechanism_family: str
    worker_ids: List[int]
    start_step: int
    econ_state: Any
    baseline_action: Dict[str, Any]
    baseline_continuation: List[Dict[str, Any]]
    target_location: Optional[Tuple[int, int]] = None
    target_commodity: Optional[str] = None
    target_crop_yield: int = 0
    co_worker_trajectories: Optional[Dict[int, List[Tuple[int, int]]]] = None
    horizon: int = 24
    max_bridge_steps: Optional[int] = None
    is_terminal_sweep: bool = False


@dataclass
class CoupledPatch:
    """Bounded alternative trajectory replacing a segment of the baseline (§3, §4).
    
    BASELINE PREFIX + COUPLED PATCH + RECONNECTION / BRIDGE + BASELINE SUFFIX
    """
    patch_id: str
    source_opportunity_id: str
    worker_ids: List[int] = field(default_factory=list)
    start_step: int = 0
    end_step: int = 0

    # Explicit joint action sequence for each turn of the patch: [act_0, act_1, ...]
    actions: List[Dict[str, Any]] = field(default_factory=list)
    steps: List[CoupledPatchStep] = field(default_factory=list)
    locations: Dict[int, List[Tuple[int, int]]] = field(default_factory=dict)

    # Cargo & Inventory conservation accounting
    cargo_before: Dict[int, Dict[str, int]] = field(default_factory=dict)
    cargo_after: Dict[int, Dict[str, int]] = field(default_factory=dict)
    inventory_before: Dict[str, int] = field(default_factory=dict)
    inventory_after: Dict[str, int] = field(default_factory=dict)
    shed_before: Dict[str, int] = field(default_factory=dict)
    shed_after: Dict[str, int] = field(default_factory=dict)

    # Worker state before and after
    worker_state_before: Dict[int, Any] = field(default_factory=dict)
    worker_state_after: Dict[int, Any] = field(default_factory=dict)

    # Dependencies & Resources
    dependencies: List[str] = field(default_factory=list)
    required_resources: Dict[str, int] = field(default_factory=dict)
    created_resources: Dict[str, int] = field(default_factory=dict)
    route_cost: int = 0
    economic_effect: float = 0.0

    # Reconnect target and method
    reconnect_target: Optional[Tuple[int, int]] = None
    reconnect_method: str = "EXACT_WAYPOINT"
    terminal_feasibility: bool = True
    safety_certificate: Optional[Any] = None

    # Pre/Postconditions & Trajectory Preservation Certificate
    precondition: Optional[PatchPrecondition] = None
    postcondition: Optional[PatchPostcondition] = None
    state_delta: Optional[PatchStateDelta] = None
    preservation_certificate: Optional[TrajectoryPreservationCertificate] = None

    # Execution & Reconnect Artefacts
    spliced_continuation: Optional[List[Dict[str, Any]]] = None
    reconnect_result: Optional[Any] = None
    state: CoupledPatchState = CoupledPatchState.PROPOSED

    # Backward compatibility with existing modules
    worker_mutations: Dict[int, List[str]] = field(default_factory=dict)
    market_mutations: Optional[List[List[Any]]] = None
    timing_changes: Dict[str, Any] = field(default_factory=dict)
    resource_changes: Dict[str, Any] = field(default_factory=dict)
    terminal_changes: Dict[str, Any] = field(default_factory=dict)
    mechanism_family: str = ""
    expected_horizon: int = 12
    rationale: str = ""
    affected_obligations: List[str] = field(default_factory=list)
    conversion_metadata: Dict[str, Any] = field(default_factory=dict)
    coordination_plan: Optional[Any] = None

    @property
    def duration(self) -> int:
        return max(1, self.end_step - self.start_step + 1) if self.end_step >= self.start_step else len(self.actions)

    def apply(self, baseline_action: Dict[str, Any]) -> Dict[str, Any]:
        """Apply patch to a deep copy of baseline action for step 0."""
        if self.actions:
            return copy.deepcopy(self.actions[0])

        new_action = copy.deepcopy(baseline_action)
        for worker_id, cmd in self.worker_mutations.items():
            if worker_id == 0:
                new_action["farmer"] = list(cmd)
            else:
                hands = new_action.setdefault("hands", [])
                h_idx = worker_id - 1
                while len(hands) <= h_idx:
                    hands.append(["PASS"])
                hands[h_idx] = list(cmd)

        if self.market_mutations is not None:
            new_action["market"] = copy.deepcopy(self.market_mutations)[:10]

        return new_action

    def get_action_at_offset(self, offset: int, default_action: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Return the patched joint action at relative offset from patch start."""
        if 0 <= offset < len(self.actions):
            return copy.deepcopy(self.actions[offset])
        if self.spliced_continuation and offset > 0 and (offset - 1) < len(self.spliced_continuation):
            return copy.deepcopy(self.spliced_continuation[offset - 1])
        return copy.deepcopy(default_action) if default_action is not None else {"farmer": ["PASS"], "hands": [], "market": []}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "patch_id": self.patch_id,
            "opportunity_id": self.source_opportunity_id,
            "mechanism_family": self.mechanism_family,
            "worker_ids": list(self.worker_ids),
            "start_step": self.start_step,
            "end_step": self.end_step,
            "duration": self.duration,
            "state": self.state.value if isinstance(self.state, CoupledPatchState) else str(self.state),
            "route_cost": self.route_cost,
            "economic_effect": round(self.economic_effect, 2),
            "reconnect_target": self.reconnect_target,
            "reconnect_method": self.reconnect_method,
            "terminal_feasibility": self.terminal_feasibility,
            "preservation_valid": self.preservation_certificate.is_valid if self.preservation_certificate else True,
            "dependencies": list(self.dependencies),
            "created_resources": dict(self.created_resources),
            "rationale": self.rationale,
        }


@dataclass
class CoupledPatchResult:
    """Formal result certificate from coupled patch compilation and validation (§4, §8)."""
    status: str
    patch: Optional[CoupledPatch] = None
    trajectory_certificate: Optional[TrajectoryPreservationCertificate] = None
    exact_delta: float = 0.0
    labor_opportunity_cost: float = 0.0
    local_estimate: float = 0.0
    rejection_reason: Optional[str] = None

    @property
    def is_accepted(self) -> bool:
        return self.status == "ACCEPTED" and self.patch is not None and self.exact_delta > 0.0
