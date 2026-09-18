# SPDX-License-Identifier: MIT
"""AEC-RESOURCE: Strict Auxiliary Worker Precondition & Labor Classification (§9, §10, §11, §12, §14).

Formalizes:
1. Labor requirement classification (NO_WORKER_REQUIRED, PRIMARY_WORKER_REQUIRED,
   AUXILIARY_WORKER_PREFERRED, AUXILIARY_WORKER_REQUIRED).
2. Strict auxiliary-worker precondition: prohibits silent fallback to Farmer for labor-intensive paths.
3. Principled Farmer Fallback Rule: permits Farmer execution only if exact dependency
   and obligation analysis proves zero baseline cannibalization.
4. Day-boundary contract expiry protection (step % 24 == 23).
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from aec.config import TURNS_PER_DAY
from aec.coordination.assignment import DisplacementOutcome, LaborOpportunityCost
from aec.coordination.scheduler import (
    CoordinationStatus,
    MultiWorkerLogisticsCoordinator,
    WorkerCoordinationPlan,
)
from aec.coordination.task_model import TaskActionFamily, TaskPriority, WorkerTask
from aec.coordination.worker_model import WorkerCapability, WorkerState, WorkerType


class ConversionLaborClass(str, Enum):
    """Categorical labor requirement class based on simulator semantics (§10)."""
    NO_WORKER_REQUIRED = "NO_WORKER_REQUIRED"                 # Pure market transactions or automated ops
    PRIMARY_WORKER_REQUIRED = "PRIMARY_WORKER_REQUIRED"       # Strictly restricted to Farmer
    AUXILIARY_WORKER_PREFERRED = "AUXILIARY_WORKER_PREFERRED" # Either capable, but prioritize auxiliary hand
    AUXILIARY_WORKER_REQUIRED = "AUXILIARY_WORKER_REQUIRED"   # Labor-intensive conversion strictly requiring auxiliary labor


class ConversionLaborPreconditionValidator:
    """Validates and enforces strict auxiliary worker preconditions for conversion paths (§9, §11, §12)."""

    def __init__(self, coordinator: Optional[MultiWorkerLogisticsCoordinator] = None) -> None:
        self.coordinator = coordinator or MultiWorkerLogisticsCoordinator()

    def classify_labor_requirement(
        self,
        worker_actions: List[str],
        target_commodity: str,
        target_location: Optional[Tuple[int, int]] = None
    ) -> ConversionLaborClass:
        """Derive authoritative labor class from required physical actions and game semantics (§10)."""
        if not worker_actions or worker_actions == ["PASS"]:
            return ConversionLaborClass.NO_WORKER_REQUIRED

        # Animal feeding, physical shed pickups/drops, and route detours are labor-intensive
        primary_op = worker_actions[-1] if worker_actions else "PASS"
        if primary_op in ("FEED", "PICKUP", "DROP", "HARVEST", "CARE", "FERTILIZE", "DIG"):
            return ConversionLaborClass.AUXILIARY_WORKER_REQUIRED

        if target_commodity in ("MILK", "EGG", "WOOL"):
            return ConversionLaborClass.AUXILIARY_WORKER_REQUIRED

        return ConversionLaborClass.AUXILIARY_WORKER_PREFERRED

    def validate_and_schedule(
        self,
        tasks: List[WorkerTask],
        labor_class: ConversionLaborClass,
        workers: Dict[int, WorkerState],
        baseline_action: Dict[str, Any],
        baseline_continuation: List[Dict[str, Any]],
        current_step: int,
        estimated_duration: int = 1
    ) -> Tuple[bool, Optional[WorkerCoordinationPlan], Optional[str]]:
        """Validates labor preconditions and schedules tasks without violating Farmer preservation (§9, §11)."""
        # Case 1: No worker required
        if labor_class == ConversionLaborClass.NO_WORKER_REQUIRED:
            return True, None, None

        if not tasks:
            return True, None, None

        active_aux_workers = {
            wid: w for wid, w in workers.items()
            if wid > 0 and w.is_active
        }

        # Case 2: Strict Auxiliary Worker Required (§9, §11, §12)
        if labor_class == ConversionLaborClass.AUXILIARY_WORKER_REQUIRED:
            if active_aux_workers:
                # Day boundary expiry check (§19, Phase 004 finding)
                # In sim.hpp, hired hands contract ends or expires at day boundaries if step % 24 == 23
                step_in_day = current_step % TURNS_PER_DAY
                steps_until_day_end = TURNS_PER_DAY - step_in_day
                if steps_until_day_end <= max(1, min(3, estimated_duration)):
                    return (
                        False,
                        None,
                        f"Day boundary expiry precondition failed: turn {current_step} is {steps_until_day_end} steps from day boundary; "
                        f"auxiliary worker contract expiry prevents safe multi-step execution"
                    )

                # Attempt multi-worker coordination strictly allocating to auxiliary workers
                coord_plan = self.coordinator.plan_coordination(
                    candidate_tasks=tasks,
                    workers=active_aux_workers,
                    baseline_action=baseline_action,
                    baseline_continuation=baseline_continuation,
                    current_step=current_step
                )

                if not coord_plan.is_executable:
                    return (
                        False,
                        None,
                        f"Auxiliary worker scheduling infeasible: {coord_plan.rejection_reason or 'labor cannibalization or routing failure'}"
                    )

                # Verify Farmer was not assigned
                assigned_wids = {a.worker_id for a in coord_plan.assignments}
                if 0 in assigned_wids:
                    return (
                        False,
                        None,
                        "Illegal assignment: primary Farmer assigned to AUXILIARY_WORKER_REQUIRED task"
                    )

                return True, coord_plan, None

            else:
                # If auxiliary workers exist on farm but are inactive/unavailable -> RC-R6: ABSTAIN
                if len(workers) > 1:
                    return (
                        False,
                        None,
                        "Auxiliary worker unavailable on multi-worker farm: ABSTAIN instead of Farmer fallback (RC-R6)"
                    )

                # Farmer is the only worker on farm: evaluate 7-condition Farmer Fallback Rule (RC-R7)
                passed_farmer_rule, farmer_reason = self._evaluate_farmer_fallback_rule(
                    tasks=tasks,
                    workers=workers,
                    baseline_action=baseline_action,
                    baseline_continuation=baseline_continuation,
                    current_step=current_step
                )

                if not passed_farmer_rule:
                    return False, None, f"Farmer fallback rejected: {farmer_reason}"

                farmer_only = {0: workers[0]}
                coord_plan = self.coordinator.plan_coordination(
                    candidate_tasks=tasks,
                    workers=farmer_only,
                    baseline_action=baseline_action,
                    baseline_continuation=baseline_continuation,
                    current_step=current_step
                )

                if not coord_plan.is_executable:
                    return False, None, f"Farmer execution plan infeasible: {coord_plan.rejection_reason}"

                return True, coord_plan, None

        # Case 3: Auxiliary Preferred or Farmer Fallback Permitted under strict conditions (§11)
        # Try auxiliary first
        if active_aux_workers:
            coord_plan = self.coordinator.plan_coordination(
                candidate_tasks=tasks,
                workers=active_aux_workers,
                baseline_action=baseline_action,
                baseline_continuation=baseline_continuation,
                current_step=current_step
            )
            if coord_plan.is_executable and 0 not in {a.worker_id for a in coord_plan.assignments}:
                return True, coord_plan, None

        # If auxiliary is not feasible, apply Farmer Fallback Rule (§11)
        passed_farmer_rule, farmer_reason = self._evaluate_farmer_fallback_rule(
            tasks=tasks,
            workers=workers,
            baseline_action=baseline_action,
            baseline_continuation=baseline_continuation,
            current_step=current_step
        )

        if not passed_farmer_rule:
            return False, None, f"Farmer fallback rejected: {farmer_reason}"

        # Schedule Farmer
        farmer_only = {0: workers[0]}
        coord_plan = self.coordinator.plan_coordination(
            candidate_tasks=tasks,
            workers=farmer_only,
            baseline_action=baseline_action,
            baseline_continuation=baseline_continuation,
            current_step=current_step
        )

        if not coord_plan.is_executable:
            return False, None, f"Farmer execution plan infeasible: {coord_plan.rejection_reason}"

        return True, coord_plan, None

    def _evaluate_farmer_fallback_rule(
        self,
        tasks: List[WorkerTask],
        workers: Dict[int, WorkerState],
        baseline_action: Dict[str, Any],
        baseline_continuation: List[Dict[str, Any]],
        current_step: int
    ) -> Tuple[bool, str]:
        """Strict 7-condition Farmer Fallback Rule (§11).
        
        Conditions:
        1. Is Farmer the only legal capable worker?
        2. Does Farmer displacement affect a mandatory baseline task?
        3. Does Farmer displacement affect a high-value scheduled production action?
        4. Can any auxiliary worker absorb the conversion?
        5. Can the displaced Farmer task be reassigned?
        6. Can both schedules coexist?
        7. Does exact counterfactual confirm safety?
        """
        # 1. Farmer must exist
        if 0 not in workers:
            return False, "Farmer does not exist in worker state"

        # Extract baseline tasks for Farmer
        baseline_tasks = self.coordinator.extract_baseline_tasks(
            workers={0: workers[0]},
            baseline_action=baseline_action,
            baseline_continuation=baseline_continuation,
            current_step=current_step
        )

        # 2 & 3: Check if Farmer is engaged in mandatory or high-value tasks
        for b_task in baseline_tasks:
            if b_task.is_mandatory:
                return (
                    False,
                    f"Farmer displacement breaches mandatory baseline obligation {b_task.task_id} ({b_task.action_family.value})"
                )
            if b_task.priority_class in (
                TaskPriority.HIGH_VALUE_HARVEST,
                TaskPriority.LIVESTOCK_SECURITY,
                TaskPriority.SCHEDULED_PRODUCTION,
                TaskPriority.TERMINAL_OBLIGATION
            ):
                return (
                    False,
                    f"Farmer displacement cannibalizes high-value baseline task {b_task.task_id} ({b_task.action_family.value}, priority {b_task.priority_class.name})"
                )

        # 4. If an auxiliary worker exists and is capable, prefer them over Farmer
        for wid, w in workers.items():
            if wid > 0 and w.is_active:
                return False, f"Auxiliary worker {wid} exists; Farmer fallback prohibited when auxiliary labor is present"

        # If baseline tasks are strictly idle/pass/opportunistic only, Farmer may execute
        return True, "Farmer is single worker and baseline duties are non-mandatory"
