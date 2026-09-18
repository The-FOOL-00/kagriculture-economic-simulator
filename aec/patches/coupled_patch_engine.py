# SPDX-License-Identifier: MIT
"""AEC Phase 006: Coupled Patch Execution & Trajectory Preservation Engine (§3, §8, §9).

The authoritative compiler and validation engine for all coupled patch mechanisms.
Implements the end-to-end pipeline:
Opportunity -> PatchRequest -> Feasibility -> Dependency Closure ->
Worker Assignment -> Patch Construction -> Postcondition Construction ->
Reconnect -> Exact Counterfactual -> Safety -> Economic Evaluation -> Commit/Abstain
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

from aec.config import BOARD_SIZE
from aec.coordination.dominance import MultiWorkerDominancePruner
from aec.coordination.scheduler import MultiWorkerLogisticsCoordinator
from aec.coordination.worker_model import extract_farm_workers
from aec.counterfactual.simulator import CounterfactualSimulator
from aec.ir.economic_state import EconomicState
from aec.opportunities.base import Opportunity
from aec.patches.coupled_patch import (
    CoupledPatch,
    CoupledPatchRequest,
    CoupledPatchResult,
    CoupledPatchState,
    TrajectoryPreservationCertificate,
)
from aec.patches.harvest_patch import HarvestCoupledPatchGenerator
from aec.replanning.reconnect import ReconnectionEngine


class CoupledPatchEngine:
    """Authoritative architectural orchestrator for trajectory-preserving coupled patches."""

    def __init__(self, board_size: int = BOARD_SIZE) -> None:
        self.board_size = board_size
        self.reconnection_engine = ReconnectionEngine(board_size=board_size)
        self.multiworker_coordinator = MultiWorkerLogisticsCoordinator(board_size=board_size)
        self.dominance_pruner = MultiWorkerDominancePruner()
        self.simulator = CounterfactualSimulator()
        self.harvest_generator = HarvestCoupledPatchGenerator(board_size=board_size)

    def process_request(self, request: CoupledPatchRequest) -> CoupledPatchResult:
        """Process a formal CoupledPatchRequest through the complete state machine (§8, §9)."""
        # Fail-closed check on unknown/invalid state
        if request.econ_state is None:
            return CoupledPatchResult(
                status=CoupledPatchState.INFEASIBLE.value,
                rejection_reason="Economic state is None (fail-closed)"
            )

        # Mechanism-specific routing
        family = request.mechanism_family
        if family in ("DYNAMIC_SHADOW_HARVEST", "TERMINAL_HARVEST_SWEEP"):
            return self.harvest_generator.generate_harvest_patch(request)

        # Generic / unhandled mechanism families fail closed until validated
        return CoupledPatchResult(
            status=CoupledPatchState.INFEASIBLE.value,
            rejection_reason=f"Mechanism family '{family}' does not have an active coupled patch compiler"
        )

    def evaluate_opportunity(
        self,
        opportunity: Opportunity,
        econ_state: EconomicState,
        baseline_action: Dict[str, Any],
        baseline_continuation: List[Dict[str, Any]],
        co_worker_trajectories: Optional[Dict[int, List[Tuple[int, int]]]] = None,
        is_terminal_sweep: bool = False
    ) -> CoupledPatchResult:
        """Convenience bridge to evaluate an opportunity via CoupledPatchEngine."""
        dep_info = opportunity.dependency_info or {}
        worker_id = dep_info.get("worker_id", 0)
        target_xy = dep_info.get("target_xy")
        crop = dep_info.get("crop")

        request = CoupledPatchRequest(
            opportunity_id=opportunity.opportunity_id,
            mechanism_family=opportunity.candidate_transformation_family,
            worker_ids=[worker_id],
            start_step=econ_state.step,
            econ_state=econ_state,
            baseline_action=baseline_action,
            baseline_continuation=baseline_continuation,
            target_location=target_xy,
            target_commodity=crop,
            co_worker_trajectories=co_worker_trajectories,
            horizon=opportunity.required_horizon,
            is_terminal_sweep=is_terminal_sweep
        )

        return self.process_request(request)
