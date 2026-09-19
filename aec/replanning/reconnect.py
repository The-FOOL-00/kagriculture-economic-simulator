# SPDX-License-Identifier: MIT
"""AEC-RECONNECT: Dynamic Worker Trajectory Reconnection & Route Splicing (§4-§16).

This module implements trajectory reconstruction, exact constrained pathfinding,
reconnection target selection, multi-worker space-time coordination,
route splicing, and adaptive causal escalation.
"""

from __future__ import annotations

import copy
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional, Set, Tuple

from aec.config import BOARD_SIZE, MOVES, SHED_TILES, TURNS_PER_DAY

# Canonical tie-breaking order for deterministic movement
CANONICAL_DIRECTIONS: List[str] = ["NORTH", "SOUTH", "EAST", "WEST"]
TILE_OPERATIONS: Set[str] = {
    "DIG", "PLANT", "WATER", "HARVEST", "DROP", "STORE", "TAKE",
    "FEED", "CARE", "FERTILIZE", "BUY_LAND"
}


class ReconnectionStatus(Enum):
    """Authoritative outcome status of trajectory reconnection attempt (§4)."""
    SAFE_RECONNECT = "SAFE_RECONNECT"
    RECONNECT_WITH_TIMING_SHIFT = "RECONNECT_WITH_TIMING_SHIFT"
    ESCALATE_REPLAN = "ESCALATE_REPLAN"
    INVAL_CANNOT_RECONNECT = "INVAL_CANNOT_RECONNECT"
    INVAL_DOWNSTREAM_CONFLICT = "INVAL_DOWNSTREAM_CONFLICT"
    INVAL_SPATIAL_CONFLICT = "INVAL_SPATIAL_CONFLICT"
    INVAL_OBLIGATION_CONFLICT = "INVAL_OBLIGATION_CONFLICT"
    INVAL_FIDELITY_FAILURE = "INVAL_FIDELITY_FAILURE"


class EscalationScope(IntEnum):
    """Multi-tier causal escalation levels replacing fixed step limits (§5)."""
    LOCAL = 1
    DEPENDENCY_CLOSURE = 2
    MEDIUM_REPLAN = 3
    EXTENDED_REPLAN = 4
    FULL_REPLAN = 5


@dataclass
class WorkerTrajectoryState:
    """Formal representation of worker trajectory and operational state (§6)."""
    worker_id: int
    position: Tuple[int, int]
    task: str = "PASS"
    target: Optional[Tuple[int, int]] = None
    route: List[str] = field(default_factory=list)
    eta: int = 0
    carried_inventory: Dict[str, int] = field(default_factory=dict)
    hand_usage: Dict[str, Any] = field(default_factory=dict)
    action_dependencies: List[str] = field(default_factory=list)
    downstream_waypoints: List[Tuple[int, int]] = field(default_factory=list)
    critical_obligations: List[Dict[str, Any]] = field(default_factory=list)
    expected_resource_arrivals: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_cargo(self) -> int:
        return sum(self.carried_inventory.values())


@dataclass
class TrajectorySegment:
    """Discrete trajectory interval with spatio-temporal and economic impacts (§6)."""
    start_state: WorkerTrajectoryState
    action_sequence: List[Dict[str, Any]]
    expected_end_state: WorkerTrajectoryState
    timing: int
    spatial_occupancy: List[Tuple[int, Tuple[int, int]]]
    resource_consequences: Dict[str, int] = field(default_factory=dict)
    market_consequences: Dict[str, Any] = field(default_factory=dict)
    obligation_consequences: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReconnectRequest:
    """Formal input specification for a trajectory reconnection request (§6)."""
    worker: int
    divergence_point: int
    patched_action: List[str]
    intended_target_state: Optional[Tuple[int, int]] = None
    baseline_continuation: List[Dict[str, Any]] = field(default_factory=list)
    causal_closure: Set[str] = field(default_factory=set)
    econ_state: Optional[Any] = None
    co_worker_trajectories: Optional[Dict[int, List[Tuple[int, int]]]] = None
    critical_obligations: Optional[List[Dict[str, Any]]] = None
    scheduled_market_sales: Optional[List[Dict[str, Any]]] = None
    max_bridge_steps: Optional[int] = None
    remaining_steps: int = 720


@dataclass
class ReconnectResult:
    """Formal output certificate of trajectory reconnection compilation (§6)."""
    status: ReconnectionStatus
    path: List[str] = field(default_factory=list)
    timing_shift: int = 0
    affected_nodes: Set[str] = field(default_factory=set)
    affected_workers: Set[int] = field(default_factory=set)
    affected_resources: Dict[str, int] = field(default_factory=dict)
    fidelity: str = "VERIFIED"
    safety: bool = True
    reconnect_waypoint_index: int = 0
    reconnect_target_pos: Optional[Tuple[int, int]] = None
    spliced_trajectory: List[Dict[str, Any]] = field(default_factory=list)
    escalation_scope: EscalationScope = EscalationScope.LOCAL
    rejection_reason: Optional[str] = None

    @property
    def is_safe(self) -> bool:
        return self.safety and self.status in (
            ReconnectionStatus.SAFE_RECONNECT,
            ReconnectionStatus.RECONNECT_WITH_TIMING_SHIFT
        )


def manhattan(p1: Tuple[int, int], p2: Tuple[int, int]) -> int:
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def is_within_bounds(pos: Tuple[int, int], board_size: int = BOARD_SIZE) -> bool:
    return 0 <= pos[0] < board_size and 0 <= pos[1] < board_size


def compute_next_pos(pos: Tuple[int, int], move_cmd: str, board_size: int = BOARD_SIZE) -> Tuple[int, int]:
    """Compute deterministic next position after a move command."""
    if move_cmd in MOVES:
        dx, dy = MOVES[move_cmd]
        nx, ny = pos[0] + dx, pos[1] + dy
        if 0 <= nx < board_size and 0 <= ny < board_size:
            return (nx, ny)
    return pos


def extract_worker_trajectory(
    action_sequence: List[Dict[str, Any]],
    start_pos: Tuple[int, int],
    worker_id: int,
    board_size: int = BOARD_SIZE
) -> List[Tuple[Tuple[int, int], List[str]]]:
    """Trace positions and actions of a worker across an action sequence."""
    trajectory: List[Tuple[Tuple[int, int], List[str]]] = []
    curr = start_pos
    for act in action_sequence:
        if worker_id == 0:
            cmd = act.get("farmer", ["PASS"]) or ["PASS"]
        else:
            hands = act.get("hands", []) or []
            h_idx = worker_id - 1
            cmd = hands[h_idx] if h_idx < len(hands) else ["PASS"]
        trajectory.append((curr, list(cmd)))
        if cmd and cmd[0] in MOVES:
            curr = compute_next_pos(curr, cmd[0], board_size)
    return trajectory


def extract_all_worker_trajectories(
    econ_state: Any,
    action_sequence: List[Dict[str, Any]],
    board_size: int = BOARD_SIZE
) -> Dict[int, List[Tuple[int, int]]]:
    """Trace positions for all workers across an action sequence, indexed by step offset."""
    trajectories: Dict[int, List[Tuple[int, int]]] = {}
    if econ_state is None or getattr(econ_state, "workers", None) is None:
        return trajectories
    for w in econ_state.workers.workers:
        tr = extract_worker_trajectory(action_sequence, w.position, w.worker_id, board_size)
        trajectories[w.worker_id] = [w.position] + [p for p, _ in tr]
    return trajectories


class SpacetimeReservationTable:
    """Reservation table enforcing collision-free multi-worker space-time coordination (§11)."""

    def __init__(self, board_size: int = BOARD_SIZE):
        self.board_size = board_size
        # (time_step, pos) -> worker_id
        self.vertex_reservations: Dict[Tuple[int, Tuple[int, int]], int] = {}
        # (time_step, from_pos, to_pos) -> worker_id
        self.edge_reservations: Dict[Tuple[int, Tuple[int, int], Tuple[int, int]], int] = {}
        # (time_step, task_id) -> worker_id
        self.task_reservations: Dict[Tuple[int, str], int] = {}
        # (time_step, resource_key) -> worker_id
        self.resource_reservations: Dict[Tuple[int, str], int] = {}
        # (time_step, pos) -> worker_id (exclusive structure building / access)
        self.building_reservations: Dict[Tuple[int, Tuple[int, int]], int] = {}

    def reserve_vertex(self, step: int, pos: Tuple[int, int], worker_id: int) -> bool:
        key = (step, pos)
        existing = self.vertex_reservations.get(key)
        if existing is not None and existing != worker_id:
            return False
        self.vertex_reservations[key] = worker_id
        return True

    def reserve_edge(self, step: int, from_pos: Tuple[int, int], to_pos: Tuple[int, int], worker_id: int) -> bool:
        # Check swap collision with another worker moving in the opposite direction
        reverse_key = (step, to_pos, from_pos)
        existing = self.edge_reservations.get(reverse_key)
        if existing is not None and existing != worker_id:
            return False
        key = (step, from_pos, to_pos)
        self.edge_reservations[key] = worker_id
        return True

    def is_vertex_available(self, step: int, pos: Tuple[int, int], worker_id: int) -> bool:
        existing = self.vertex_reservations.get((step, pos))
        return existing is None or existing == worker_id

    def is_edge_available(self, step: int, from_pos: Tuple[int, int], to_pos: Tuple[int, int], worker_id: int) -> bool:
        reverse_existing = self.edge_reservations.get((step, to_pos, from_pos))
        return reverse_existing is None or reverse_existing == worker_id

    def reserve_task(self, step: int, task_id: str, worker_id: int) -> bool:
        key = (step, task_id)
        existing = self.task_reservations.get(key)
        if existing is not None and existing != worker_id:
            return False
        self.task_reservations[key] = worker_id
        return True

    def is_task_available(self, step: int, task_id: str, worker_id: int) -> bool:
        existing = self.task_reservations.get((step, task_id))
        return existing is None or existing == worker_id

    def reserve_resource(self, step: int, resource_key: str, worker_id: int) -> bool:
        key = (step, resource_key)
        existing = self.resource_reservations.get(key)
        if existing is not None and existing != worker_id:
            return False
        self.resource_reservations[key] = worker_id
        return True

    def is_resource_available(self, step: int, resource_key: str, worker_id: int) -> bool:
        existing = self.resource_reservations.get((step, resource_key))
        return existing is None or existing == worker_id

    def reserve_building(self, step: int, pos: Tuple[int, int], worker_id: int) -> bool:
        key = (step, pos)
        existing = self.building_reservations.get(key)
        if existing is not None and existing != worker_id:
            return False
        self.building_reservations[key] = worker_id
        return True

    def is_building_available(self, step: int, pos: Tuple[int, int], worker_id: int) -> bool:
        existing = self.building_reservations.get((step, pos))
        return existing is None or existing == worker_id

    def reserve_trajectory(
        self,
        trajectory_points: List[Tuple[int, Tuple[int, int]]],
        worker_id: int
    ) -> bool:
        """Reserve all vertex and edge transitions along a trajectory."""
        prev_p: Optional[Tuple[int, int]] = None
        for step, pos in trajectory_points:
            if not self.reserve_vertex(step, pos, worker_id):
                return False
            if prev_p is not None:
                if not self.reserve_edge(step, prev_p, pos, worker_id):
                    return False
            prev_p = pos
        return True

    def is_trajectory_collision_free(
        self,
        trajectory_points: List[Tuple[int, Tuple[int, int]]],
        worker_id: int
    ) -> bool:
        """Check if entire trajectory can be executed without collision."""
        prev_p: Optional[Tuple[int, int]] = None
        for step, pos in trajectory_points:
            if not self.is_vertex_available(step, pos, worker_id):
                return False
            if prev_p is not None:
                if not self.is_edge_available(step, prev_p, pos, worker_id):
                    return False
            prev_p = pos
        return True


def deterministic_find_path(
    start: Tuple[int, int],
    target: Tuple[int, int],
    start_step: int,
    reservations: Optional[SpacetimeReservationTable] = None,
    worker_id: int = 0,
    max_steps: int = 20,
    board_size: int = BOARD_SIZE,
    allow_pass: bool = False
) -> Optional[List[str]]:
    """Deterministic, collision-aware shortest pathfinding using canonical directional ordering (§7)."""
    if start == target:
        return []

    if not is_within_bounds(start, board_size) or not is_within_bounds(target, board_size):
        return None

    # Queue contains: (curr_pos, current_step, path_moves)
    queue: deque = deque([(start, start_step, [])])
    visited: Set[Tuple[int, Tuple[int, int]]] = {(start_step, start)}

    while queue:
        curr_pos, cur_step, path = queue.popleft()

        if curr_pos == target:
            return path

        if len(path) >= max_steps:
            continue

        next_step = cur_step + 1

        # Evaluate directional moves in strictly deterministic canonical order
        for d_name in CANONICAL_DIRECTIONS:
            dx, dy = MOVES[d_name]
            nxt = (curr_pos[0] + dx, curr_pos[1] + dy)

            if not is_within_bounds(nxt, board_size):
                continue

            state_key = (next_step, nxt)
            if state_key in visited:
                continue

            # Collision checks
            if reservations is not None:
                if not reservations.is_vertex_available(next_step, nxt, worker_id):
                    continue
                if not reservations.is_edge_available(next_step, curr_pos, nxt, worker_id):
                    continue

            visited.add(state_key)
            queue.append((nxt, next_step, path + [d_name]))

        # Allow PASS / wait on cell if explicitly enabled
        if allow_pass:
            state_key = (next_step, curr_pos)
            if state_key not in visited:
                if reservations is None or reservations.is_vertex_available(next_step, curr_pos, worker_id):
                    visited.add(state_key)
                    queue.append((curr_pos, next_step, path + ["PASS"]))

    return None


class ReconnectionEngine:
    """Core compiler component for worker route reconnection and trajectory splicing (§4-§16)."""

    def __init__(self, board_size: int = BOARD_SIZE):
        self.board_size = board_size

    def build_reservation_table(
        self,
        co_worker_trajectories: Optional[Dict[int, List[Tuple[int, int]]]],
        active_worker: int,
        horizon: int
    ) -> SpacetimeReservationTable:
        """Construct multi-worker space-time reservations from known baseline trajectories."""
        table = SpacetimeReservationTable(self.board_size)
        if not co_worker_trajectories:
            return table

        for other_id, pos_seq in co_worker_trajectories.items():
            if other_id == active_worker:
                continue
            prev_p: Optional[Tuple[int, int]] = None
            for step_idx, p in enumerate(pos_seq):
                if step_idx >= horizon:
                    break
                # step_idx 0 is starting position, step_idx 1 is position after turn 0, etc.
                table.reserve_vertex(step_idx, p, other_id)
                if prev_p is not None:
                    table.reserve_edge(step_idx, prev_p, p, other_id)
                prev_p = p

        return table

    def identify_reconnection_targets(
        self,
        baseline_continuation: List[Dict[str, Any]],
        start_pos: Tuple[int, int],
        worker_id: int
    ) -> List[Dict[str, Any]]:
        """Identify candidate reconnection waypoints along the baseline continuation tape (§9).
        
        W_k is the position the baseline worker reaches AFTER executing continuation[k].
        """
        targets: List[Dict[str, Any]] = []
        curr_pos = start_pos

        for offset, act in enumerate(baseline_continuation):
            if worker_id == 0:
                cmd = act.get("farmer", ["PASS"]) or ["PASS"]
            else:
                hands = act.get("hands", []) or []
                h_idx = worker_id - 1
                cmd = hands[h_idx] if h_idx < len(hands) else ["PASS"]

            op = cmd[0] if cmd else "PASS"

            # Compute position after executing this continuation action
            if op in MOVES:
                next_pos = compute_next_pos(curr_pos, op, self.board_size)
            else:
                next_pos = curr_pos

            # Target waypoint after completing this continuation offset
            target_types = []
            if offset == 0:
                target_types.append("IMMEDIATE_NEXT_WAYPOINT")
            if op in TILE_OPERATIONS:
                target_types.append("TASK_BOUNDARY")
            if op in ("DROP", "STORE"):
                target_types.append("RESOURCE_BOUNDARY")
            if (offset + 1) % TURNS_PER_DAY == 0:
                target_types.append("MACRO_CHECKPOINT")

            targets.append({
                "offset": offset,
                "target_pos": next_pos,
                "scheduled_cmd": cmd,
                "target_types": target_types,
                "priority": 1 if "IMMEDIATE_NEXT_WAYPOINT" in target_types else (2 if "TASK_BOUNDARY" in target_types else 3)
            })

            curr_pos = next_pos

        if not targets:
            targets.append({
                "offset": 0,
                "target_pos": start_pos,
                "scheduled_cmd": ["PASS"],
                "target_types": ["FALLBACK_WAYPOINT"],
                "priority": 4
            })

        # Sort targets by priority then offset
        targets.sort(key=lambda t: (t["priority"], t["offset"]))
        return targets

    def evaluate_downstream_viability(
        self,
        target_info: Dict[str, Any],
        bridge_length: int,
        request: ReconnectRequest
    ) -> Tuple[bool, int, Optional[str], EscalationScope]:
        """Validate whether the timing shift and detour are safe for downstream obligations (§10, §13)."""
        target_offset = target_info["offset"]
        expected_time = target_offset + 1

        # Timing shift
        if bridge_length <= expected_time:
            timing_shift = 0
        else:
            timing_shift = bridge_length - expected_time

        # Reconnect arrival in absolute game steps
        reconnect_arrival = request.divergence_point + 1 + bridge_length

        # 1. Check scheduled market sales
        if request.scheduled_market_sales:
            for sale in request.scheduled_market_sales:
                sale_step = sale.get("step", 9999)
                commodity = sale.get("commodity", "")
                if reconnect_arrival > sale_step:
                    return False, timing_shift, f"Detour delay misses scheduled market sale for {commodity} at step {sale_step}", EscalationScope.MEDIUM_REPLAN

        # 2. Check critical obligations (e.g. feed animals before starvation)
        if request.critical_obligations:
            for ob in request.critical_obligations:
                deadline = ob.get("deadline_step", 9999)
                if reconnect_arrival > deadline:
                    return False, timing_shift, f"Detour delay breaches critical obligation '{ob.get('description', '')}' at step {deadline}", EscalationScope.EXTENDED_REPLAN

        # 3. Dynamic escalation tier mapping (§5)
        closure_size = len(request.causal_closure)

        if request.remaining_steps <= 24:
            return True, timing_shift, None, EscalationScope.FULL_REPLAN
        elif closure_size >= 5 or timing_shift > 4:
            return True, timing_shift, None, EscalationScope.EXTENDED_REPLAN
        elif closure_size >= 3 or timing_shift > 2:
            return True, timing_shift, None, EscalationScope.MEDIUM_REPLAN
        elif timing_shift > 0 or closure_size == 2:
            return True, timing_shift, None, EscalationScope.DEPENDENCY_CLOSURE
        else:
            return True, 0, None, EscalationScope.LOCAL

    def splice_route(
        self,
        patched_action_cmd: List[str],
        bridge_path: List[str],
        baseline_continuation: List[Dict[str, Any]],
        target_offset: int,
        worker_id: int,
        timing_shift: int,
        co_worker_trajectories: Optional[Dict[int, List[Tuple[int, int]]]] = None
    ) -> List[Dict[str, Any]]:
        """Constructs: PREFIX (implicit at divergence) + PATCH + BRIDGE + BASELINE SUFFIX (§8)."""
        spliced: List[Dict[str, Any]] = []

        # 1. Bridge Actions for continuation steps (offset 0 .. len(bridge_path)-1)
        for b_step, move_name in enumerate(bridge_path):
            base_act = baseline_continuation[b_step] if b_step < len(baseline_continuation) else {}
            new_act = copy.deepcopy(base_act)

            if worker_id == 0:
                new_act["farmer"] = [move_name]
                new_act.setdefault("hands", base_act.get("hands", []))
            else:
                hands = copy.deepcopy(new_act.get("hands", []))
                h_idx = worker_id - 1
                while len(hands) <= h_idx:
                    hands.append(["PASS"])
                hands[h_idx] = [move_name]
                new_act["hands"] = hands
                new_act.setdefault("farmer", base_act.get("farmer", ["PASS"]))

            new_act.setdefault("market", copy.deepcopy(base_act.get("market", [])))
            spliced.append(new_act)

        # 2. Baseline Suffix:
        # If target action is a tile operation/task, include it in the suffix so the worker executes it
        target_act = baseline_continuation[target_offset] if target_offset < len(baseline_continuation) else {}
        if worker_id == 0:
            target_cmd = target_act.get("farmer", ["PASS"]) or ["PASS"]
        else:
            h_list = target_act.get("hands", []) or []
            h_idx = worker_id - 1
            target_cmd = h_list[h_idx] if h_idx < len(h_list) else ["PASS"]

        if target_cmd and target_cmd[0] in TILE_OPERATIONS:
            suffix_start = target_offset
        else:
            suffix_start = target_offset + 1

        for base_offset in range(suffix_start, len(baseline_continuation)):
            base_act = baseline_continuation[base_offset]
            new_act = copy.deepcopy(base_act)
            spliced.append(new_act)

        return spliced

    def reconnect(self, request: ReconnectRequest) -> ReconnectResult:
        """Execute full trajectory reconnection compiler pass (§4-§16)."""
        worker_id = request.worker

        # 1. Determine starting position before divergence
        if request.econ_state is not None:
            w_entity = request.econ_state.workers.get_worker(worker_id)
            initial_pos = w_entity.position if w_entity else (0, 0)
        else:
            initial_pos = (0, 0)

        # 2. Calculate position after executing patched action
        patched_cmd = request.patched_action
        if patched_cmd and patched_cmd[0] in MOVES:
            dx, dy = MOVES[patched_cmd[0]]
            nx, ny = initial_pos[0] + dx, initial_pos[1] + dy
            if not is_within_bounds((nx, ny), self.board_size):
                return ReconnectResult(
                    status=ReconnectionStatus.INVAL_CANNOT_RECONNECT,
                    safety=False,
                    fidelity="FAILED",
                    rejection_reason=f"Worker {worker_id} patched move {patched_cmd[0]} out of bounds from {initial_pos}"
                )
            diverged_pos = (nx, ny)
        else:
            diverged_pos = initial_pos

        # 3. Build Spacetime Reservation Table for multi-worker coordination
        horizon = len(request.baseline_continuation) + 10
        reservations = self.build_reservation_table(
            request.co_worker_trajectories, worker_id, horizon
        )

        # Check for immediate collision at step 1 (after executing patched action at step 0)
        if not reservations.is_vertex_available(1, diverged_pos, worker_id):
            return ReconnectResult(
                status=ReconnectionStatus.INVAL_SPATIAL_CONFLICT,
                safety=False,
                fidelity="FAILED",
                rejection_reason=f"Worker {worker_id} collided with another worker on cell {diverged_pos} at step 1"
            )
        if not reservations.is_edge_available(1, initial_pos, diverged_pos, worker_id):
            return ReconnectResult(
                status=ReconnectionStatus.INVAL_SPATIAL_CONFLICT,
                safety=False,
                fidelity="FAILED",
                rejection_reason=f"Worker {worker_id} swap collision between {initial_pos} and {diverged_pos} at step 1"
            )

        # 4. Identify Candidate Reconnection Targets along baseline continuation
        targets = self.identify_reconnection_targets(
            request.baseline_continuation, initial_pos, worker_id
        )

        # 5. Search for earliest safe bridge to a candidate target
        viable_plans: List[Dict[str, Any]] = []
        unviable_plans: List[Dict[str, Any]] = []
        max_allowed_bridge = request.max_bridge_steps or (
            12 if request.remaining_steps > 24 else max(2, request.remaining_steps)
        )

        for target in targets:
            tgt_pos = target["target_pos"]
            tgt_offset = target["offset"]
            expected_time = tgt_offset + 1

            # Compute shortest collision-free path from diverged_pos to tgt_pos
            bridge_moves = deterministic_find_path(
                start=diverged_pos,
                target=tgt_pos,
                start_step=1,
                reservations=reservations,
                worker_id=worker_id,
                max_steps=max_allowed_bridge,
                board_size=self.board_size,
                allow_pass=False
            )

            if bridge_moves is None:
                continue

            raw_len = len(bridge_moves)
            if raw_len > max_allowed_bridge:
                continue

            bridge_len = raw_len

            # Evaluate downstream viability
            viable, timing_shift, conflict_reason, esc_scope = self.evaluate_downstream_viability(
                target, bridge_len, request
            )

            plan_entry = {
                "unviable": not viable,
                "target": target,
                "bridge_moves": bridge_moves,
                "timing_shift": timing_shift,
                "conflict_reason": conflict_reason,
                "esc_scope": esc_scope
            }

            if viable:
                viable_plans.append(plan_entry)
            else:
                unviable_plans.append(plan_entry)

        best_plan: Optional[Dict[str, Any]] = None
        if viable_plans:
            # Rank viable plans:
            # 1. timing_shift == 0 first (exact / on-time reconnect)
            # 2. task boundaries preferred over passive moves
            # 3. minimal timing shift
            # 4. earliest target offset
            viable_plans.sort(key=lambda p: (
                0 if p["timing_shift"] == 0 else 1,
                0 if ("TASK_BOUNDARY" in p["target"]["target_types"] or "RESOURCE_BOUNDARY" in p["target"]["target_types"]) else 1,
                p["timing_shift"],
                p["target"]["priority"],
                p["target"]["offset"]
            ))
            best_plan = viable_plans[0]
        elif unviable_plans:
            best_plan = unviable_plans[0]

        # 6. Formulate outcome certificate
        if best_plan is None:
            return ReconnectResult(
                status=ReconnectionStatus.INVAL_CANNOT_RECONNECT,
                safety=False,
                fidelity="FAILED",
                rejection_reason=f"Worker {worker_id} could not find any valid bridge to baseline waypoints within {max_allowed_bridge} steps"
            )

        if best_plan.get("unviable"):
            return ReconnectResult(
                status=ReconnectionStatus.INVAL_DOWNSTREAM_CONFLICT,
                safety=False,
                fidelity="FAILED",
                escalation_scope=best_plan.get("esc_scope", EscalationScope.MEDIUM_REPLAN),
                rejection_reason=best_plan.get("conflict_reason", "Downstream conflict detected")
            )

        target_info = best_plan["target"]
        bridge_moves = best_plan["bridge_moves"]
        timing_shift = best_plan["timing_shift"]
        esc_scope = best_plan["esc_scope"]

        spliced_continuation = self.splice_route(
            patched_action_cmd=patched_cmd,
            bridge_path=bridge_moves,
            baseline_continuation=request.baseline_continuation,
            target_offset=target_info["offset"],
            worker_id=worker_id,
            timing_shift=timing_shift,
            co_worker_trajectories=request.co_worker_trajectories
        )

        status = (
            ReconnectionStatus.SAFE_RECONNECT
            if timing_shift == 0
            else ReconnectionStatus.RECONNECT_WITH_TIMING_SHIFT
        )

        affected_workers = {worker_id}
        if request.co_worker_trajectories:
            for w in request.co_worker_trajectories:
                if w != worker_id:
                    affected_workers.add(w)

        return ReconnectResult(
            status=status,
            path=bridge_moves,
            timing_shift=timing_shift,
            affected_nodes=set(request.causal_closure),
            affected_workers=affected_workers,
            fidelity="VERIFIED",
            safety=True,
            reconnect_waypoint_index=target_info["offset"],
            reconnect_target_pos=target_info["target_pos"],
            spliced_trajectory=spliced_continuation,
            escalation_scope=esc_scope
        )


def reconnect_worker_trajectory(request: ReconnectRequest) -> ReconnectResult:
    """Entry point for trajectory reconnection compiler pass (§4)."""
    engine = ReconnectionEngine()
    return engine.reconnect(request)
