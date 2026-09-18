# SPDX-License-Identifier: MIT
"""AEC Phase 003: Multi-Worker Dominance Pruning (§22).

Evaluates candidate multi-worker assignments and prunes dominated plans
using exact state, obligation preservation, and routing evidence without arbitrary bonuses.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from aec.coordination.assignment import LaborOpportunityCost, WorkerAssignment


class MultiWorkerDominancePruner:
    """Deterministic dominance evaluation for multi-worker coordination plans (§22)."""

    @staticmethod
    def dominates(
        plan_a_assignments: List[WorkerAssignment],
        plan_a_cost: LaborOpportunityCost,
        plan_b_assignments: List[WorkerAssignment],
        plan_b_cost: LaborOpportunityCost
    ) -> bool:
        """Return True if Plan A strictly dominates Plan B.
        
        Plan A dominates Plan B if:
        1. Plan A is valid/acceptable and Plan B is not, OR
        2. Both are acceptable, and:
           - Plan A loses fewer mandatory obligations than Plan B, OR
           - Plan A loses same obligations, but preserves strictly more total baseline value, OR
           - Same obligations and value, but Plan A has strictly lower total transit steps, OR
           - Same obligations, value, and transit steps, but Plan A assigns critical duties
             to specialized/preferred workers (e.g. Farmer on high-value harvest).
        """
        # Acceptability gate
        if plan_a_cost.is_acceptable and not plan_b_cost.is_acceptable:
            return True
        if not plan_a_cost.is_acceptable and plan_b_cost.is_acceptable:
            return False
        if not plan_a_cost.is_acceptable and not plan_b_cost.is_acceptable:
            # Both unacceptable: compare lost mandatory obligations
            return plan_a_cost.lost_mandatory_count < plan_b_cost.lost_mandatory_count

        # Both acceptable: Compare mandatory obligations lost
        if plan_a_cost.lost_mandatory_count < plan_b_cost.lost_mandatory_count:
            return True
        if plan_a_cost.lost_mandatory_count > plan_b_cost.lost_mandatory_count:
            return False

        # Compare displaced value (lower displaced value = better)
        if plan_a_cost.displaced_value_est < plan_b_cost.displaced_value_est - 1e-6:
            return True
        if plan_a_cost.displaced_value_est > plan_b_cost.displaced_value_est + 1e-6:
            return False

        # Compare absorbed tasks count (higher absorbed by peer = better preservation)
        if len(plan_a_cost.absorbed_tasks) > len(plan_b_cost.absorbed_tasks):
            return True
        if len(plan_a_cost.absorbed_tasks) < len(plan_b_cost.absorbed_tasks):
            return False

        # Compare total transit steps (lower = better)
        steps_a = sum(len(a.transit_route) for a in plan_a_assignments)
        steps_b = sum(len(b.transit_route) for b in plan_b_assignments)
        if steps_a < steps_b:
            return True
        if steps_a > steps_b:
            return False

        # Worker 0 (Farmer) role preservation: If Plan A keeps Farmer on harvest while Plan B diverts Farmer, A dominates
        farmer_harvests_a = sum(1 for a in plan_a_assignments if a.worker_id == 0 and "HARVEST" in a.task.action_family.value)
        farmer_harvests_b = sum(1 for b in plan_b_assignments if b.worker_id == 0 and "HARVEST" in b.task.action_family.value)
        if farmer_harvests_a > farmer_harvests_b:
            return True

        return False

    @classmethod
    def prune(
        cls,
        candidate_plans: List[Tuple[List[WorkerAssignment], LaborOpportunityCost]]
    ) -> List[Tuple[List[WorkerAssignment], LaborOpportunityCost]]:
        """Filter out all strictly dominated candidate coordination plans."""
        if not candidate_plans:
            return []

        survivors: List[Tuple[List[WorkerAssignment], LaborOpportunityCost]] = []

        for i, (plan_a, cost_a) in enumerate(candidate_plans):
            is_dominated = False
            for j, (plan_b, cost_b) in enumerate(candidate_plans):
                if i == j:
                    continue
                if cls.dominates(plan_b, cost_b, plan_a, cost_a):
                    is_dominated = True
                    break
            if not is_dominated:
                survivors.append((plan_a, cost_a))

        return survivors
