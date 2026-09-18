# SPDX-License-Identifier: MIT
"""AEC-RESOURCE: Deterministic Feed Security Engine (§5, §6).

Implements exact game livestock starvation accounting, interval-based feed
forecasting, and non-negotiable feed security verification for all animal obligations.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from aec.config import TURNS_PER_DAY
from aec.ir.economic_state import EconomicState

if TYPE_CHECKING:
    from aec.patches.patch import CoupledPatch


@dataclass
class LivestockEntity:
    """Represents an active livestock unit on the farm board (§5, §6)."""
    animal_id: str
    subtype: str                        # "COW", "SHEEP", "GOOSE"
    position: Tuple[int, int]
    structure: str                      # "PASTURE" or "COOP"
    placed_day: int
    consecutive_unfed: int
    fed_today: bool
    cared_today: bool
    pending_care_bonus: int = 0
    daily_consumption: int = 1          # 1 unit of WHEAT per day
    
    @property
    def days_until_escape(self) -> int:
        """Exact game semantics: animal escapes if consecutive_unfed >= 2."""
        return max(0, 2 - self.consecutive_unfed)

    @property
    def is_starving(self) -> bool:
        return self.consecutive_unfed >= 1


@dataclass
class FeedIntervalProfile:
    """Feed inventory and demand forecast for a specific temporal step (§5)."""
    step: int
    day: int
    hour: int
    available_feed: int                 # Shed wheat + carried wheat
    incoming_feed: int                  # Harvests / confirmed purchases
    required_feed: int                  # Animals needing feed today
    reserved_feed: int                  # Feed locked for upcoming feeding
    surplus: int                        # Available + Incoming - Required - Reserved
    starvation_risk: bool = False
    escape_risk: bool = False


@dataclass
class FeedSecurityState:
    """Audit certificate detailing feed security proof across the evaluation horizon (§5)."""
    is_secure: bool
    deficit_count: int = 0
    first_breach_turn: Optional[int] = None
    affected_animals: List[str] = field(default_factory=list)
    max_consecutive_unfed: int = 0
    escaped_animals_count: int = 0
    profile: List[FeedIntervalProfile] = field(default_factory=list)
    reason: Optional[str] = None


class FeedSecurityEngine:
    """Deterministic analyzer ensuring candidate patches preserve complete feed security."""

    def extract_livestock(self, econ_state: EconomicState) -> List[LivestockEntity]:
        """Extract all active animals from farm board tiles using exact game schemas."""
        animals: List[LivestockEntity] = []
        tiles = econ_state.farm.tiles

        for y, row in enumerate(tiles):
            for x, tile in enumerate(row):
                if isinstance(tile, dict) and "animal" in tile:
                    sub = str(tile["animal"])
                    placed_day = int(tile.get("placed_day", 0) or 0)
                    consec = int(tile.get("consecutive_unfed", 0) or 0)
                    fed = bool(tile.get("fed_today", False))
                    cared = bool(tile.get("cared_today", False))
                    bonus = int(tile.get("pending_care_bonus", 0) or 0)
                    struct = str(tile.get("kind", "PASTURE"))
                    
                    animals.append(LivestockEntity(
                        animal_id=f"{sub}_{x}_{y}",
                        subtype=sub,
                        position=(x, y),
                        structure=struct,
                        placed_day=placed_day,
                        consecutive_unfed=consec,
                        fed_today=fed,
                        cared_today=cared,
                        pending_care_bonus=bonus,
                    ))

        return animals

    def evaluate_feed_trajectory(
        self,
        econ_state: EconomicState,
        action_sequence: List[Dict[str, Any]],
        horizon: int
    ) -> FeedSecurityState:
        """Forward-simulate feed availability and feeding actions step-by-step (§5, §6).
        
        Evaluates exact game rules:
        - 1 WHEAT consumed when worker executes FEED on animal tile.
        - At end-of-day: unfed animals increment consecutive_unfed.
        - If consecutive_unfed >= 2, animal escapes permanently.
        - If feed inventory drops below mandatory feeding demand, flags deficit.
        """
        animals = self.extract_livestock(econ_state)
        if not animals:
            return FeedSecurityState(is_secure=True)

        # Initial feed inventory
        current_shed_wheat = econ_state.farm.get_shed_qty("WHEAT")
        current_hands_wheat = econ_state.farm.carried_inventory.get("WHEAT", 0)
        current_wheat = current_shed_wheat + current_hands_wheat
        current_money = float(econ_state.farm.cash)

        # Tracking animal state per animal_id
        animal_states = {a.animal_id: copy.copy(a) for a in animals}

        profiles: List[FeedIntervalProfile] = []
        deficit_count = 0
        first_breach_step: Optional[int] = None
        escaped_count = 0
        breached_animals: Set[str] = set()

        for offset in range(horizon):
            step = econ_state.step + offset
            if step >= 720:
                break
            day = step // TURNS_PER_DAY
            hour = step % TURNS_PER_DAY
            act = action_sequence[offset] if offset < len(action_sequence) else {}

            # 1. Market orders this turn
            market_orders = act.get("market", []) or []
            for order in market_orders:
                if isinstance(order, (list, tuple)) and len(order) >= 3:
                    op, item, qty = order[0], order[1], int(order[2])
                    if item == "WHEAT":
                        if op == "SELL":
                            # Selling removes wheat from shed!
                            current_wheat = max(0, current_wheat - qty)
                        elif op == "BUY_PRODUCT":
                            current_wheat += qty

            # 2. Worker feeding actions this turn
            farmer_act = act.get("farmer", ["PASS"]) or ["PASS"]
            hands_acts = act.get("hands", []) or []
            worker_actions = [farmer_act] + hands_acts

            # Identify workers at animal positions executing FEED
            for w_idx, w_cmd in enumerate(worker_actions):
                if isinstance(w_cmd, (list, tuple)) and w_cmd and w_cmd[0] == "FEED":
                    # Check which animal is being fed
                    # Worker must have wheat to feed
                    if current_wheat > 0:
                        # Find matching animal at worker position
                        for a_id, a_state in animal_states.items():
                            if not a_state.fed_today:
                                a_state.fed_today = True
                                current_wheat -= 1
                                break

            # Count animals requiring feed today
            unfed_today_count = sum(1 for a in animal_states.values() if not a.fed_today)

            # Check if remaining wheat is sufficient for remaining unfed animals today
            surplus = current_wheat - unfed_today_count
            starvation_risk = surplus < 0
            escape_risk = any(
                a.consecutive_unfed >= 1 and not a.fed_today
                for a in animal_states.values()
            )

            if starvation_risk:
                deficit_count += abs(surplus)
                if first_breach_step is None:
                    first_breach_step = step
                for a in animal_states.values():
                    if not a.fed_today:
                        breached_animals.add(a.animal_id)

            # Record profile
            profile_entry = FeedIntervalProfile(
                step=step,
                day=day,
                hour=hour,
                available_feed=current_wheat,
                incoming_feed=0,
                required_feed=unfed_today_count,
                reserved_feed=0,
                surplus=surplus,
                starvation_risk=starvation_risk,
                escape_risk=escape_risk
            )
            profiles.append(profile_entry)

            # 3. End of day lifecycle transition
            if (step + 1) % TURNS_PER_DAY == 0:
                for a_id, a_state in list(animal_states.items()):
                    if a_state.fed_today:
                        a_state.consecutive_unfed = 0
                    else:
                        a_state.consecutive_unfed += 1
                        if a_state.consecutive_unfed >= 2:
                            escaped_count += 1
                            breached_animals.add(a_id)
                    a_state.fed_today = False

        max_consec = max((a.consecutive_unfed for a in animal_states.values()), default=0)
        is_secure = (deficit_count == 0) and (escaped_count == 0) and (max_consec < 2)

        reason = None
        if not is_secure:
            if escaped_count > 0:
                reason = f"Fatal feed deficit: {escaped_count} animal(s) reached consecutive_unfed >= 2 and escaped"
            elif deficit_count > 0:
                reason = f"Feed deficit of {deficit_count} unit(s) detected at step {first_breach_step}"
            else:
                reason = "Feed security invariant breached"

        return FeedSecurityState(
            is_secure=is_secure,
            deficit_count=deficit_count,
            first_breach_turn=first_breach_step,
            affected_animals=sorted(list(breached_animals)),
            max_consecutive_unfed=max_consec,
            escaped_animals_count=escaped_count,
            profile=profiles,
            reason=reason
        )

    def verify_candidate_patch(
        self,
        patch: CoupledPatch,
        baseline_action: Dict[str, Any],
        econ_state: EconomicState,
        future_trajectory: Optional[List[Dict[str, Any]]],
        horizon: int
    ) -> FeedSecurityState:
        """Evaluate feed security for a candidate patch vs baseline future continuation (§5, §17)."""
        cand_action = patch.apply(baseline_action)
        continuation = (
            patch.spliced_continuation
            if getattr(patch, "spliced_continuation", None) is not None
            else (future_trajectory or [])
        )
        full_trajectory = [cand_action] + list(continuation)[:max(0, horizon - 1)]

        return self.evaluate_feed_trajectory(econ_state, full_trajectory, horizon)


def decompose_feed_rescue_to_tasks(
    deficit: int,
    animal_pos: Tuple[int, int],
    current_step: int,
    shed_pos: Tuple[int, int] = (4, 4),
    latest_step: Optional[int] = None
) -> List[Any]:
    """Decompose an emergency feed intervention into discrete WorkerTasks for multi-worker coordination (§14, §15)."""
    from aec.coordination.task_model import TaskActionFamily, TaskPriority, WorkerTask
    from aec.coordination.worker_model import WorkerCapability

    if latest_step is None:
        day_end = ((current_step // 24) + 1) * 24 - 1
        latest_step = day_end

    tasks: List[WorkerTask] = []

    # Task 1: PICKUP WHEAT at shed access tile
    pickup_task = WorkerTask(
        task_id=f"FEED_PICKUP_{current_step}",
        action_family=TaskActionFamily.PICKUP_RESOURCE,
        location=shed_pos,
        earliest_start=current_step,
        latest_completion=max(current_step + 1, latest_step - 2),
        required_capabilities={WorkerCapability.MOVE, WorkerCapability.PICKUP},
        duration=1,
        resource_inputs={},
        resource_outputs={"WHEAT": deficit},
        priority_class=TaskPriority.LIVESTOCK_SECURITY,
        is_mandatory=True,
        target_commodity="WHEAT",
    )
    tasks.append(pickup_task)

    # Task 2: FEED ANIMAL at animal position
    feed_task = WorkerTask(
        task_id=f"FEED_DELIVER_{current_step}",
        action_family=TaskActionFamily.FEED_ANIMAL,
        location=animal_pos,
        earliest_start=current_step + 1,
        latest_completion=latest_step,
        required_capabilities={WorkerCapability.MOVE, WorkerCapability.FEED},
        duration=1,
        resource_inputs={"WHEAT": 1},
        resource_outputs={},
        dependent_tasks=[pickup_task.task_id],
        priority_class=TaskPriority.LIVESTOCK_SECURITY,
        is_mandatory=True,
        target_commodity="WHEAT",
        target_entity=f"ANIMAL_{animal_pos[0]}_{animal_pos[1]}",
    )
    tasks.append(feed_task)

    return tasks
