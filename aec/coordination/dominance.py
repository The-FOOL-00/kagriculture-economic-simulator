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
        if farmer_harvests_a < farmer_harvests_b:
            return False

        # Auxiliary worker preference: Plans utilizing auxiliary workers dominate plans diverting Farmer
        farmer_diverted_a = any(a.worker_id == 0 for a in plan_a_assignments)
        farmer_diverted_b = any(b.worker_id == 0 for b in plan_b_assignments)
        if not farmer_diverted_a and farmer_diverted_b:
            return True
        if farmer_diverted_a and not farmer_diverted_b:
            return False

        # Completion timing dominance: Plan completing earlier dominates
        max_step_a = max((a.completion_step for a in plan_a_assignments), default=0)
        max_step_b = max((b.completion_step for b in plan_b_assignments), default=0)
        if max_step_a < max_step_b:
            return True
        if max_step_a > max_step_b:
            return False

        return False

    @staticmethod
    def dominates_assessment(
        assessment_a: Any,
        assessment_b: Any
    ) -> bool:
        """Return True if LaborOpportunityAssessment A strictly dominates B under formal economic relations (§27).
        
        Plan A dominates Plan B if:
        1. Plan A is safe/acceptable and Plan B is not, OR
        2. Both are safe, and:
           - A achieves strictly higher net incremental value with equal or lower opportunity cost, OR
           - A achieves equal net incremental value with strictly lower opportunity cost.
        """
        if getattr(assessment_a, "safe_to_use", False) and not getattr(assessment_b, "safe_to_use", False):
            return True
        if not getattr(assessment_a, "safe_to_use", False) and getattr(assessment_b, "safe_to_use", False):
            return False
        if not getattr(assessment_a, "safe_to_use", False) and not getattr(assessment_b, "safe_to_use", False):
            return False

        net_a = getattr(assessment_a, "net_incremental_value", 0.0)
        net_b = getattr(assessment_b, "net_incremental_value", 0.0)
        oc_a = getattr(assessment_a, "opportunity_cost", 0.0)
        oc_b = getattr(assessment_b, "opportunity_cost", 0.0)

        if net_a > net_b + 1e-6 and oc_a <= oc_b + 1e-6:
            return True
        if net_a >= net_b - 1e-6 and oc_a < oc_b - 1e-6:
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
