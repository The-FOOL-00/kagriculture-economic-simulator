# SPDX-License-Identifier: MIT
"""Opportunity Candidate Funnel and Bounded Inference Budget (§7, §30, §31)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from aec.config import BOARD_SIZE, EPISODE_STEPS, PRODUCTS, SHED_TILES
from aec.ir.economic_state import EconomicState


class FunnelStage(str, Enum):
    """The 10 formal stages of the candidate funnel (§7)."""
    S1_CHEAP_LEGALITY = "S1_CHEAP_LEGALITY"
    S2_CHEAP_REACHABILITY = "S2_CHEAP_REACHABILITY"
    S3_RESOURCE_FEASIBILITY = "S3_RESOURCE_FEASIBILITY"
    S4_WORKER_AVAILABILITY = "S4_WORKER_AVAILABILITY"
    S5_LABOR_SHADOW_SCREEN = "S5_LABOR_SHADOW_SCREEN"
    S6_DEPENDENCY_CLOSURE = "S6_DEPENDENCY_CLOSURE"
    S7_DOMINANCE_PRUNING = "S7_DOMINANCE_PRUNING"
    S8_ROUTE_COST_SCREEN = "S8_ROUTE_COST_SCREEN"
    S9_DETERMINISTIC_TOP_K = "S9_DETERMINISTIC_TOP_K"
    S10_EXACT_COUNTERFACTUAL = "S10_EXACT_COUNTERFACTUAL"


@dataclass
class InferenceBudget:
    """Explicit runtime budgets to keep inference strictly within limits (§30)."""
    max_turn_time_ms: float = 100.0
    max_exact_simulations: int = 4
    max_candidates_screened: int = 8
    max_raw_candidates: int = 32
    max_stage_latency_ms: float = 20.0

    def is_exhausted(self, elapsed_ms: float, sim_count: int) -> bool:
        """Check if time or simulation capacity has been exhausted."""
        return elapsed_ms >= self.max_turn_time_ms or sim_count >= self.max_exact_simulations


@dataclass
class FunnelStageRecord:
    """Audit record for a single funnel screening stage."""
    stage: FunnelStage
    candidates_in: int
    candidates_out: int
    eliminated_count: int
    elimination_reasons: Dict[str, int] = field(default_factory=dict)
    latency_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage.value,
            "in": self.candidates_in,
            "out": self.candidates_out,
            "eliminated": self.eliminated_count,
            "reasons": dict(self.elimination_reasons),
            "latency_ms": round(self.latency_ms, 3),
        }


@dataclass
class FunnelTelemetry:
    """Full telemetry trail of candidate filtering across all stages (§7)."""
    initial_candidates: int = 0
    final_candidates: int = 0
    exact_simulations_budgeted: int = 0
    stage_records: List[FunnelStageRecord] = field(default_factory=list)
    total_funnel_latency_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "initial_candidates": self.initial_candidates,
            "final_candidates": self.final_candidates,
            "exact_sims_budgeted": self.exact_simulations_budgeted,
            "total_latency_ms": round(self.total_funnel_latency_ms, 3),
            "stages": [r.to_dict() for r in self.stage_records],
        }


class OpportunityCandidateFunnel:
    """Filters large numbers of raw opportunity candidates before exact simulation.
    
    Exact counterfactual simulation costs ~1.86s per full game evaluation.
    This funnel screens candidates using sub-millisecond linear checks,
    ensuring only top-K viable candidates reach the simulation oracle.
    """

    def __init__(
        self,
        budget: Optional[InferenceBudget] = None,
        macro_controller: Optional[Any] = None,
        reservation_policy: Optional[Any] = None
    ) -> None:
        self.budget = budget or InferenceBudget()
        self.macro_controller = macro_controller
        self.reservation_policy = reservation_policy
        self.last_reservation_telemetry: Optional[Any] = None

    def filter_candidates(
        self,
        raw_candidates: List[Any],
        econ_state: EconomicState,
        budget: Optional[InferenceBudget] = None,
        labor_engine: Optional[Any] = None,
        macro_controller: Optional[Any] = None,
        reservation_policy: Optional[Any] = None,
    ) -> Tuple[List[Any], FunnelTelemetry]:
        """Execute the 10-stage tiered pruning pipeline (§7)."""
        t_start = time.perf_counter()
        budget = budget or self.budget
        macro = macro_controller or self.macro_controller
        telemetry = FunnelTelemetry(
            initial_candidates=len(raw_candidates),
            exact_simulations_budgeted=budget.max_exact_simulations
        )

        current = list(raw_candidates)

        # Stage 1: Cheap Legality
        current, rec1 = self._stage_cheap_legality(current, econ_state)
        telemetry.stage_records.append(rec1)

        # Stage 2: Cheap Reachability
        current, rec2 = self._stage_cheap_reachability(current, econ_state)
        telemetry.stage_records.append(rec2)

        # Stage 3: Resource Feasibility
        current, rec3 = self._stage_resource_feasibility(current, econ_state, macro)
        telemetry.stage_records.append(rec3)

        # Stage 4: Worker Availability
        current, rec4 = self._stage_worker_availability(current, econ_state)
        telemetry.stage_records.append(rec4)

        # Stage 5: Labor Shadow Screen
        current, rec5 = self._stage_labor_shadow(current, econ_state, labor_engine)
        telemetry.stage_records.append(rec5)

        # Stage 6: Dependency Closure
        current, rec6 = self._stage_dependency_closure(current, econ_state)
        telemetry.stage_records.append(rec6)

        # Stage 7: Dominance Pruning
        current, rec7 = self._stage_dominance_pruning(current, econ_state)
        telemetry.stage_records.append(rec7)

        # Stage 8: Route-Cost Screen
        current, rec8 = self._stage_route_cost_screen(current, econ_state)
        telemetry.stage_records.append(rec8)

        # Stage 9: Deterministic Top-K Selection (§31)
        # Phase 018 Repair A: optional reservation policy (constructor or per-call).
        policy = reservation_policy if reservation_policy is not None else self.reservation_policy
        self.last_reservation_telemetry = None
        current, rec9 = self._stage_deterministic_top_k(
            current, econ_state, budget.max_exact_simulations, reservation_policy=policy
        )
        telemetry.stage_records.append(rec9)

        telemetry.final_candidates = len(current)
        telemetry.total_funnel_latency_ms = (time.perf_counter() - t_start) * 1000.0
        return current, telemetry

    def _stage_cheap_legality(self, candidates: List[Any], econ_state: EconomicState) -> Tuple[List[Any], FunnelStageRecord]:
        t0 = time.perf_counter()
        survived = []
        reasons: Dict[str, int] = {}
        for c in candidates:
            # Verify coordinates within board boundaries [0, 9]
            target_pos = getattr(c, "target_pos", None) or getattr(c, "target_position", None)
            if target_pos is not None:
                x, y = target_pos
                if not (0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE):
                    reasons["OUT_OF_BOUNDS"] = reasons.get("OUT_OF_BOUNDS", 0) + 1
                    continue
            survived.append(c)
        rec = FunnelStageRecord(
            stage=FunnelStage.S1_CHEAP_LEGALITY,
            candidates_in=len(candidates),
            candidates_out=len(survived),
            eliminated_count=len(candidates) - len(survived),
            elimination_reasons=reasons,
            latency_ms=(time.perf_counter() - t0) * 1000.0
        )
        return survived, rec

    def _stage_cheap_reachability(self, candidates: List[Any], econ_state: EconomicState) -> Tuple[List[Any], FunnelStageRecord]:
        t0 = time.perf_counter()
        survived = []
        reasons: Dict[str, int] = {}
        rem_steps = EPISODE_STEPS - econ_state.step
        for c in candidates:
            wid = getattr(c, "worker_id", 0)
            target_pos = getattr(c, "target_pos", None) or getattr(c, "target_position", None)
            w = next((x for x in econ_state.workers.workers if x.worker_id == wid), None)
            if w is not None and target_pos is not None:
                dist = abs(w.position[0] - target_pos[0]) + abs(w.position[1] - target_pos[1])
                # Worker cannot even reach target before game ends
                if dist >= rem_steps:
                    reasons["UNREACHABLE_BEFORE_END"] = reasons.get("UNREACHABLE_BEFORE_END", 0) + 1
                    continue
            survived.append(c)
        rec = FunnelStageRecord(
            stage=FunnelStage.S2_CHEAP_REACHABILITY,
            candidates_in=len(candidates),
            candidates_out=len(survived),
            eliminated_count=len(candidates) - len(survived),
            elimination_reasons=reasons,
            latency_ms=(time.perf_counter() - t0) * 1000.0
        )
        return survived, rec

    def _stage_resource_feasibility(
        self,
        candidates: List[Any],
        econ_state: EconomicState,
        macro_controller: Optional[Any] = None
    ) -> Tuple[List[Any], FunnelStageRecord]:
        t0 = time.perf_counter()
        survived = []
        reasons: Dict[str, int] = {}
        cash = econ_state.cash

        min_reserve = 0.0
        if macro_controller is not None:
            strat = macro_controller.formulate_strategy(econ_state)
            min_reserve = getattr(strat, "min_cash_reserve", 0.0)

        for c in candidates:
            dep_info = getattr(c, "dependency_info", {}) or {}
            req_cash = float(getattr(c, "required_cash", 0.0) or getattr(c, "upfront_cost", 0.0) or dep_info.get("upfront_cost", 0.0))
            if req_cash > 0:
                if req_cash > cash:
                    reasons["INSUFFICIENT_CASH"] = reasons.get("INSUFFICIENT_CASH", 0) + 1
                    continue
                if cash - req_cash < min_reserve:
                    reasons["VIOLATES_MACRO_RESERVE"] = reasons.get("VIOLATES_MACRO_RESERVE", 0) + 1
                    continue
            survived.append(c)
        rec = FunnelStageRecord(
            stage=FunnelStage.S3_RESOURCE_FEASIBILITY,
            candidates_in=len(candidates),
            candidates_out=len(survived),
            eliminated_count=len(candidates) - len(survived),
            elimination_reasons=reasons,
            latency_ms=(time.perf_counter() - t0) * 1000.0
        )
        return survived, rec

    def _stage_worker_availability(self, candidates: List[Any], econ_state: EconomicState) -> Tuple[List[Any], FunnelStageRecord]:
        t0 = time.perf_counter()
        survived = []
        reasons: Dict[str, int] = {}
        for c in candidates:
            wid = getattr(c, "worker_id", None)
            if wid is not None:
                w = next((x for x in econ_state.workers.workers if x.worker_id == wid), None)
                if w is not None and getattr(w, "is_frozen", False):
                    reasons["WORKER_FROZEN"] = reasons.get("WORKER_FROZEN", 0) + 1
                    continue
            survived.append(c)
        rec = FunnelStageRecord(
            stage=FunnelStage.S4_WORKER_AVAILABILITY,
            candidates_in=len(candidates),
            candidates_out=len(survived),
            eliminated_count=len(candidates) - len(survived),
            elimination_reasons=reasons,
            latency_ms=(time.perf_counter() - t0) * 1000.0
        )
        return survived, rec

    def _stage_labor_shadow(self, candidates: List[Any], econ_state: EconomicState, labor_engine: Optional[Any]) -> Tuple[List[Any], FunnelStageRecord]:
        t0 = time.perf_counter()
        survived = []
        reasons: Dict[str, int] = {}
        for c in candidates:
            # If candidate provides gross revenue and worker displacement cost
            gross = getattr(c, "estimated_revenue", 0.0) or getattr(c, "estimated_economic_value", 0.0)
            opp_cost = getattr(c, "labor_opportunity_cost", 0.0)
            if gross > 0 and opp_cost > gross:
                reasons["LABOR_OPPORTUNITY_COST_EXCEEDS_GROSS"] = reasons.get("LABOR_OPPORTUNITY_COST_EXCEEDS_GROSS", 0) + 1
                continue
            survived.append(c)
        rec = FunnelStageRecord(
            stage=FunnelStage.S5_LABOR_SHADOW_SCREEN,
            candidates_in=len(candidates),
            candidates_out=len(survived),
            eliminated_count=len(candidates) - len(survived),
            elimination_reasons=reasons,
            latency_ms=(time.perf_counter() - t0) * 1000.0
        )
        return survived, rec

    def _stage_dependency_closure(self, candidates: List[Any], econ_state: EconomicState) -> Tuple[List[Any], FunnelStageRecord]:
        t0 = time.perf_counter()
        survived = []
        reasons: Dict[str, int] = {}
        for c in candidates:
            # If candidate requires shed space and shed is full
            req_space = getattr(c, "required_shed_space", 0)
            if req_space > 0 and econ_state.farm.shed_inventory_count + req_space > 100:
                reasons["SHED_CAPACITY_OVERFLOW"] = reasons.get("SHED_CAPACITY_OVERFLOW", 0) + 1
                continue
            survived.append(c)
        rec = FunnelStageRecord(
            stage=FunnelStage.S6_DEPENDENCY_CLOSURE,
            candidates_in=len(candidates),
            candidates_out=len(survived),
            eliminated_count=len(candidates) - len(survived),
            elimination_reasons=reasons,
            latency_ms=(time.perf_counter() - t0) * 1000.0
        )
        return survived, rec

    def _stage_dominance_pruning(self, candidates: List[Any], econ_state: EconomicState) -> Tuple[List[Any], FunnelStageRecord]:
        t0 = time.perf_counter()
        # Prune candidates dominated on (worker_id, target_pos) by shorter duration / higher value
        grouped: Dict[Tuple[int, Tuple[int, int]], List[Any]] = {}
        for c in candidates:
            wid = getattr(c, "worker_id", 0)
            target_pos = getattr(c, "target_pos", None) or getattr(c, "target_position", (0, 0))
            grouped.setdefault((wid, target_pos), []).append(c)

        survived = []
        eliminated = 0
        reasons: Dict[str, int] = {}
        for group in grouped.values():
            if len(group) == 1:
                survived.append(group[0])
            else:
                # Sort descending by value, ascending by duration
                group.sort(
                    key=lambda x: (
                        -float(getattr(x, "estimated_economic_value", 0.0) or getattr(x, "estimated_economic_relevance", 0.0) or getattr(x, "estimated_net_delta", 0.0) or 0.0),
                        getattr(x, "duration_steps", 999)
                    )
                )
                survived.append(group[0])
                eliminated += len(group) - 1
                reasons["PARETO_DOMINATED"] = reasons.get("PARETO_DOMINATED", 0) + (len(group) - 1)

        rec = FunnelStageRecord(
            stage=FunnelStage.S7_DOMINANCE_PRUNING,
            candidates_in=len(candidates),
            candidates_out=len(survived),
            eliminated_count=eliminated,
            elimination_reasons=reasons,
            latency_ms=(time.perf_counter() - t0) * 1000.0
        )
        return survived, rec

    def _stage_route_cost_screen(self, candidates: List[Any], econ_state: EconomicState) -> Tuple[List[Any], FunnelStageRecord]:
        t0 = time.perf_counter()
        survived = []
        reasons: Dict[str, int] = {}
        for c in candidates:
            detour = getattr(c, "detour_cost", 0)
            # Filter out excessively long detours (> 30 steps) for low-value tasks
            val = getattr(c, "estimated_economic_value", 0.0)
            if detour > 30 and val < 100.0:
                reasons["DETOUR_TOO_COSTLY_FOR_VALUE"] = reasons.get("DETOUR_TOO_COSTLY_FOR_VALUE", 0) + 1
                continue
            survived.append(c)
        rec = FunnelStageRecord(
            stage=FunnelStage.S8_ROUTE_COST_SCREEN,
            candidates_in=len(candidates),
            candidates_out=len(survived),
            eliminated_count=len(candidates) - len(survived),
            elimination_reasons=reasons,
            latency_ms=(time.perf_counter() - t0) * 1000.0
        )
        return survived, rec

    def _stage_deterministic_top_k(
        self,
        candidates: List[Any],
        econ_state: EconomicState,
        max_k: int,
        reservation_policy: Optional[Any] = None,
    ) -> Tuple[List[Any], FunnelStageRecord]:
        """Strict deterministic top-K ordering (§31).
        
        Tie-break hierarchy:
        1. Estimated economic relevance / delta (descending)
        2. Mechanism family (alphabetical)
        3. Worker ID (ascending)
        4. Target position (row, col)
        5. Step (ascending)
        6. Candidate / Patch ID (string)
        """
        t0 = time.perf_counter()
        
        def tie_break_key(c: Any) -> Tuple[float, str, int, int, int, int, str]:
            val = round(-float(getattr(c, "estimated_economic_value", 0.0) or getattr(c, "estimated_economic_relevance", 0.0)), 4)
            fam = str(getattr(c, "mechanism_family", "") or getattr(c, "candidate_transformation_family", ""))
            wid = int(getattr(c, "worker_id", 0) or 0)
            pos = getattr(c, "target_pos", None) or getattr(c, "target_position", (0, 0))
            pos_x, pos_y = pos[0], pos[1]
            step = int(getattr(c, "step", econ_state.step) or 0)
            cid = str(getattr(c, "patch_id", "") or getattr(c, "opportunity_id", ""))
            return (val, fam, wid, pos_x, pos_y, step, cid)

        candidates.sort(key=tie_break_key)

        # Phase 018 Repair A: class-floor enforcement on the ranked list.
        # Legacy path executes verbatim when no enabled policy is supplied.
        if reservation_policy is not None and getattr(reservation_policy, "enabled", False):
            from aec.funnel.reservation import apply_reservation
            top_k, res_telem = apply_reservation(
                candidates, max_k, reservation_policy, site="S9_DETERMINISTIC_TOP_K"
            )
            self.last_reservation_telemetry = res_telem
            eliminated = max(0, len(candidates) - len(top_k))
            reasons = {"EXCEEDED_MAX_K_BUDGET": eliminated} if eliminated > 0 else {}
            if res_telem.saved_by_reservation:
                reasons["RESERVED_SEAT_REALLOCATION"] = len(res_telem.saved_by_reservation)
        else:
            top_k = candidates[:max_k]
            eliminated = max(0, len(candidates) - len(top_k))
            reasons = {"EXCEEDED_MAX_K_BUDGET": eliminated} if eliminated > 0 else {}

        rec = FunnelStageRecord(
            stage=FunnelStage.S9_DETERMINISTIC_TOP_K,
            candidates_in=len(candidates),
            candidates_out=len(top_k),
            eliminated_count=eliminated,
            elimination_reasons=reasons,
            latency_ms=(time.perf_counter() - t0) * 1000.0
        )
        return top_k, rec
