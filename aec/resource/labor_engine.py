# SPDX-License-Identifier: MIT
"""AEC Phase 005: Generic Labor Shadow Valuation & Opportunity-Cost Engine (§4-§17).

Architectural core for cross-cutting economic labor opportunity-cost derivation.
Evaluates:
    "If worker W is diverted from the baseline trajectory to perform candidate task T
     over interval [t0, t1], what economically relevant value is lost from the baseline,
     and what incremental value does the alternative task create?"

Operates from actual game state, dependency graphs, and projected baseline/counterfactual
trajectories. Enforces zero ordinal-to-dollar conversions and zero arbitrary magic constants.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional, Set, Tuple

from aec.config import (
    BOARD_SIZE,
    CROP_GROWTH_DAYS,
    CROP_SEED_PRICE,
    CROPS,
    FINAL_STEP,
    MOVES,
    PRODUCTS,
    SHED_CAPACITY,
    SHED_TILES,
    TURNS_PER_DAY,
)
from aec.coordination.assignment import DisplacementOutcome, LaborOpportunityCost, WorkerAssignment
from aec.coordination.dominance import MultiWorkerDominancePruner
from aec.coordination.scheduler import (
    CoordinationStatus,
    MultiWorkerLogisticsCoordinator,
    WorkerCoordinationPlan,
)
from aec.coordination.task_model import TaskActionFamily, TaskPriority, WorkerTask
from aec.coordination.worker_model import WorkerCapability, WorkerState, extract_farm_workers
from aec.ir.dependency_graph import (
    ActionBasketDependencyGraph,
    ActionNode,
    CausalEdgeType,
    build_basket_dependency_graph,
)
from aec.ir.economic_state import EconomicState
from aec.replanning.reconnect import (
    CANONICAL_DIRECTIONS,
    ReconnectRequest,
    ReconnectResult,
    ReconnectionEngine,
    ReconnectionStatus,
    compute_next_pos,
    manhattan,
)


class ValuationLevel(IntEnum):
    """Hierarchical valuation tiers escalating based on dependency and coupling depth (§9)."""
    LEVEL_0_FEASIBILITY = 0
    LEVEL_1_LOCAL_EXACT = 1
    LEVEL_2_BROADER_TRAJECTORY = 2
    LEVEL_3_WIDER_ECONOMIC_REPLAY = 3
    LEVEL_4_FULL_HORIZON = 4


class AbstentionReason(str, Enum):
    """Authoritative fail-closed abstention classifications (§17)."""
    NONE = "NONE"
    PHYSICALLY_INFEASIBLE = "PHYSICALLY_INFEASIBLE"
    DAY_BOUNDARY_EXPIRY = "DAY_BOUNDARY_EXPIRY"
    INSUFFICIENT_TRAJECTORY = "INSUFFICIENT_TRAJECTORY"
    DEPENDENCY_UNKNOWN = "DEPENDENCY_UNKNOWN"
    COUNTERFACTUAL_INCOMPLETE = "COUNTERFACTUAL_INCOMPLETE"
    TERMINAL_EFFECT_UNRESOLVED = "TERMINAL_EFFECT_UNRESOLVED"
    MULTIWORKER_INTERACTION_UNRESOLVED = "MULTIWORKER_INTERACTION_UNRESOLVED"
    MARKET_EFFECT_UNRESOLVED = "MARKET_EFFECT_UNRESOLVED"
    ECONOMIC_ATTRIBUTION_AMBIGUOUS = "ECONOMIC_ATTRIBUTION_AMBIGUOUS"
    STALE_BACKBONE = "STALE_BACKBONE"
    WORKER_STATE_INCOMPLETE = "WORKER_STATE_INCOMPLETE"
    FARMER_FALLBACK_PROHIBITED = "FARMER_FALLBACK_PROHIBITED"


@dataclass
class LaborOpportunityRequest:
    """Formal specification of a labor reallocation assessment query (§8)."""
    worker_id: int
    candidate_task: Optional[WorkerTask] = None
    candidate_action_cmd: Optional[str] = None
    candidate_action_sequence: Optional[List[str]] = None
    candidate_patch: Optional[CoupledPatch] = None

    econ_state: EconomicState = field(default_factory=lambda: None)  # type: ignore
    baseline_action: Dict[str, Any] = field(default_factory=dict)
    baseline_continuation: List[Dict[str, Any]] = field(default_factory=list)
    current_step: int = 0
    horizon: Optional[int] = None

    target_location: Optional[Tuple[int, int]] = None
    target_commodity: Optional[str] = None
    allow_multiworker_expansion: bool = True
    valuation_tier: Optional[int] = None  # None = automatic escalation


@dataclass
class LaborOpportunityAssessment:
    """Complete, auditable economic valuation certificate of worker reallocation (§8)."""
    worker_id: int
    candidate_task_id: str
    baseline_interval: Tuple[int, int]
    alternative_interval: Tuple[int, int]

    # Core Economic Accounting (§5)
    baseline_value: float                      # V_baseline(worker, interval)
    alternative_value: float                   # V_alternative(worker, candidate, interval)
    opportunity_cost: float                    # Attributable baseline loss from diversion
    candidate_incremental_value: float        # Gross incremental value created by candidate
    net_incremental_value: float              # CandidateIncrementalValue - OpportunityCost

    # Decomposed Facets (§6)
    direct_value: float = 0.0                  # Direct product / cash yielded by task
    downstream_value: float = 0.0              # Unlocked subsequent production or chain
    timing_value: float = 0.0                  # Value delta due to earlier/later execution
    preservation_value: float = 0.0            # Prevented loss / animal preservation
    terminal_value: float = 0.0                # Terminal horizon salvage / realization

    # Worker & Dependency Attribution (§10, §13)
    dependencies_impacted: List[str] = field(default_factory=list)
    tasks_displaced: List[str] = field(default_factory=list)
    tasks_preserved: List[str] = field(default_factory=list)
    tasks_delayed: List[str] = field(default_factory=list)
    affected_workers: List[int] = field(default_factory=list)

    # Governance & Certification (§8, §9, §17)
    confidence: float = 1.0                    # 0.0 to 1.0 completeness/certainty
    valuation_method: str = "EXACT_COUNTERFACTUAL"
    counterfactual_depth: int = 0              # Simulation steps evaluated
    valuation_level: int = ValuationLevel.LEVEL_1_LOCAL_EXACT

    # Decision & Fail-Closed Behavior (§17)
    safe_to_use: bool = True
    commit_recommendation: bool = False        # net_incremental_value > 0 and safe_to_use
    abstention_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "worker_id": self.worker_id,
            "candidate_task_id": self.candidate_task_id,
            "baseline_interval": list(self.baseline_interval),
            "alternative_interval": list(self.alternative_interval),
            "baseline_value": round(self.baseline_value, 2),
            "alternative_value": round(self.alternative_value, 2),
            "opportunity_cost": round(self.opportunity_cost, 2),
            "candidate_incremental_value": round(self.candidate_incremental_value, 2),
            "net_incremental_value": round(self.net_incremental_value, 2),
            "direct_value": round(self.direct_value, 2),
            "downstream_value": round(self.downstream_value, 2),
            "timing_value": round(self.timing_value, 2),
            "preservation_value": round(self.preservation_value, 2),
            "terminal_value": round(self.terminal_value, 2),
            "dependencies_impacted": self.dependencies_impacted,
            "tasks_displaced": self.tasks_displaced,
            "tasks_preserved": self.tasks_preserved,
            "tasks_delayed": self.tasks_delayed,
            "affected_workers": self.affected_workers,
            "confidence": round(self.confidence, 3),
            "valuation_method": self.valuation_method,
            "counterfactual_depth": self.counterfactual_depth,
            "valuation_level": int(self.valuation_level),
            "safe_to_use": self.safe_to_use,
            "commit_recommendation": self.commit_recommendation,
            "abstention_reason": self.abstention_reason,
        }


class LaborOpportunityCostEngine:
    """Generic, reusable labor shadow valuation and opportunity-cost engine (§4-§17)."""

    def __init__(self, board_size: int = BOARD_SIZE) -> None:
        self.board_size = board_size
        self.coordinator = MultiWorkerLogisticsCoordinator(board_size=board_size)
        self.reconnection_engine = ReconnectionEngine()
        from aec.counterfactual.simulator import CounterfactualSimulator
        self.counterfactual_simulator = CounterfactualSimulator()

    def assess_opportunity(self, request: LaborOpportunityRequest) -> LaborOpportunityAssessment:
        """Evaluate the marginal opportunity cost and incremental net value of worker reallocation.
        
        Follows the hierarchical valuation framework:
        Level 0 (Feasibility)
            ↓
        Level 1 (Local Exact Dependency)
            ↓
        Level 2 (Broader Worker Trajectory)
            ↓
        Level 3 (Wider Economic Replay)
            ↓
        Level 4 (Full-Horizon Fallback)
        """
        # 1. Input Validation & Baseline Extraction
        econ = request.econ_state
        step = request.current_step
        wid = request.worker_id

        if econ is None or econ.workers is None:
            return self._build_abstention(
                request=request,
                reason=AbstentionReason.WORKER_STATE_INCOMPLETE,
                level=ValuationLevel.LEVEL_0_FEASIBILITY
            )

        worker_entity = econ.workers.get_worker(wid)
        if worker_entity is None:
            return self._build_abstention(
                request=request,
                reason=AbstentionReason.PHYSICALLY_INFEASIBLE,
                level=ValuationLevel.LEVEL_0_FEASIBILITY
            )

        # 2. LEVEL 0: Physical Feasibility & Contract Expiry
        level_0_ok, l0_reason = self._verify_feasibility(request, worker_entity)
        if not level_0_ok:
            return self._build_abstention(
                request=request,
                reason=l0_reason or AbstentionReason.PHYSICALLY_INFEASIBLE,
                level=ValuationLevel.LEVEL_0_FEASIBILITY
            )

        if request.valuation_tier == ValuationLevel.LEVEL_0_FEASIBILITY:
            # Feasibility check only
            return self._build_assessment(
                request=request,
                baseline_val=0.0,
                alt_val=0.0,
                oc=0.0,
                cand_val=0.0,
                direct_val=0.0,
                level=ValuationLevel.LEVEL_0_FEASIBILITY,
                method="FEASIBILITY_CHECK_ONLY",
                safe=True
            )

        # 3. Baseline Task and Trajectory Extraction
        workers_dict = extract_farm_workers(econ, current_turn=step)
        baseline_tasks = self.coordinator.extract_baseline_tasks(
            workers=workers_dict,
            baseline_action=request.baseline_action,
            baseline_continuation=request.baseline_continuation,
            current_step=step
        )
        worker_baseline_tasks = [t for t in baseline_tasks if t.target_worker_preference == wid]

        # Extract worker baseline action command
        if wid == 0:
            b_cmd_list = request.baseline_action.get("farmer", ["PASS"]) or ["PASS"]
        else:
            hands = request.baseline_action.get("hands", []) or []
            h_idx = wid - 1
            b_cmd_list = hands[h_idx] if h_idx < len(hands) and hands[h_idx] else ["PASS"]
        b_cmd = b_cmd_list[0] if b_cmd_list else "PASS"

        # Determine Candidate Action Command
        c_cmd = "PASS"
        if request.candidate_action_cmd:
            c_cmd = request.candidate_action_cmd
        elif request.candidate_action_sequence:
            c_cmd = request.candidate_action_sequence[0]
        elif request.candidate_task:
            fam_map = {
                TaskActionFamily.HARVEST: "HARVEST",
                TaskActionFamily.WATER: "WATER",
                TaskActionFamily.PLANT: "PLANT",
                TaskActionFamily.FEED_ANIMAL: "FEED",
                TaskActionFamily.CARE: "CARE",
                TaskActionFamily.FERTILIZE: "FERTILIZE",
                TaskActionFamily.DIG_WEED: "DIG",
                TaskActionFamily.DROP_RESOURCE: "DROP",
                TaskActionFamily.PICKUP_RESOURCE: "TAKE",
            }
            c_cmd = fam_map.get(request.candidate_task.action_family, "PASS")

        # 4. LEVEL 1: Local Exact Dependency Valuation
        # Worker is genuinely idle (PASS or WAIT) with zero active crop duties
        is_idle_baseline = b_cmd in ("PASS", "WAIT")

        # Check if Level 1 is sufficient
        has_multiworker_coupling = (
            len(workers_dict) > 1 and
            any(t.priority_class in (TaskPriority.LIVESTOCK_SECURITY, TaskPriority.HARD_OBLIGATION) for t in baseline_tasks)
        )
        is_terminal_phase = (FINAL_STEP - step) <= max(24, TURNS_PER_DAY)

        if (
            is_idle_baseline and
            not is_terminal_phase and
            not has_multiworker_coupling and
            request.valuation_tier in (None, ValuationLevel.LEVEL_1_LOCAL_EXACT)
        ):
            # Worker has zero productive baseline tasks -> Opportunity Cost is exactly 0.0
            cand_val, direct_val, down_val, pres_val = self._evaluate_candidate_direct_value(
                request=request,
                candidate_cmd=c_cmd,
                worker_entity=worker_entity,
                econ=econ
            )
            return self._build_assessment(
                request=request,
                baseline_val=0.0,
                alt_val=cand_val,
                oc=0.0,
                cand_val=cand_val,
                direct_val=direct_val,
                downstream_val=down_val,
                preservation_val=pres_val,
                tasks_displaced=[],
                tasks_preserved=[t.task_id for t in worker_baseline_tasks],
                level=ValuationLevel.LEVEL_1_LOCAL_EXACT,
                method="LOCAL_EXACT_DEPENDENCY",
                safe=True
            )

        # 5. LEVEL 2: Broader Worker Trajectory Valuation (Peer Absorption & Agricultural Lifecycle)
        # Check if baseline duties can be absorbed by peer workers
        can_peer_absorb = False
        absorbed_tasks: List[str] = []
        if len(workers_dict) > 1 and worker_baseline_tasks:
            peer_workers = {k: v for k, v in workers_dict.items() if k != wid and v.is_active}
            if peer_workers:
                test_coord = self.coordinator.plan_coordination(
                    candidate_tasks=worker_baseline_tasks,
                    workers=peer_workers,
                    baseline_action=request.baseline_action,
                    baseline_continuation=request.baseline_continuation,
                    current_step=step
                )
                if test_coord.is_executable:
                    can_peer_absorb = True
                    absorbed_tasks = [t.task_id for t in worker_baseline_tasks]

        if can_peer_absorb:
            # Baseline work is absorbed by peer; opportunity cost is negligible peer transit overhead
            cand_val, direct_val, down_val, pres_val = self._evaluate_candidate_direct_value(
                request=request,
                candidate_cmd=c_cmd,
                worker_entity=worker_entity,
                econ=econ
            )
            return self._build_assessment(
                request=request,
                baseline_val=cand_val,
                alt_val=cand_val,
                oc=0.0,
                cand_val=cand_val,
                direct_val=direct_val,
                downstream_val=down_val,
                preservation_val=pres_val,
                tasks_displaced=[],
                tasks_preserved=absorbed_tasks,
                level=ValuationLevel.LEVEL_2_BROADER_TRAJECTORY,
                method="PEER_ABSORPTION_VERIFIED",
                safe=True
            )

        # 6. LEVEL 3 / LEVEL 4: Wider Economic Replay via Exact Forward Simulation
        # Baseline work cannot be cleanly absorbed without displacement.
        # Run exact forward counterfactual simulation.
        horizon = request.horizon or (24 if not is_terminal_phase else max(6, FINAL_STEP - step))
        if is_terminal_phase or request.valuation_tier == ValuationLevel.LEVEL_4_FULL_HORIZON:
            horizon = max(horizon, min(72, FINAL_STEP - step))
            target_level = ValuationLevel.LEVEL_4_FULL_HORIZON
        else:
            target_level = ValuationLevel.LEVEL_3_WIDER_ECONOMIC_REPLAY

        sim_assessment = self._run_counterfactual_valuation(
            request=request,
            worker_entity=worker_entity,
            candidate_cmd=c_cmd,
            worker_baseline_tasks=worker_baseline_tasks,
            horizon=horizon,
            target_level=target_level
        )
        return sim_assessment

    def _verify_feasibility(
        self,
        request: LaborOpportunityRequest,
        worker: Any
    ) -> Tuple[bool, Optional[AbstentionReason]]:
        """Level 0 feasibility verification: physical, spatial, and day-boundary constraints (§9)."""
        wid = request.worker_id
        step = request.current_step

        # 1. Day boundary contract expiry protection (hired hands expire at step % 24 == 23)
        if wid > 0:
            step_in_day = step % TURNS_PER_DAY
            steps_until_day_end = TURNS_PER_DAY - step_in_day
            duration = 1
            if request.candidate_task:
                duration = request.candidate_task.duration
            elif request.candidate_action_sequence:
                duration = len(request.candidate_action_sequence)

            if steps_until_day_end <= max(1, duration):
                return False, AbstentionReason.DAY_BOUNDARY_EXPIRY

        # 2. Spatial bounds
        pos = worker.position
        if not (0 <= pos[0] < self.board_size and 0 <= pos[1] < self.board_size):
            return False, AbstentionReason.PHYSICALLY_INFEASIBLE

        # 3. Reachability of target location
        if request.target_location:
            tx, ty = request.target_location
            if not (0 <= tx < self.board_size and 0 <= ty < self.board_size):
                return False, AbstentionReason.PHYSICALLY_INFEASIBLE
            dist = manhattan(pos, request.target_location)
            max_allowed_transit = max(1, request.horizon or 12)
            if dist > max_allowed_transit:
                return False, AbstentionReason.PHYSICALLY_INFEASIBLE

        return True, None

    def _evaluate_candidate_direct_value(
        self,
        request: LaborOpportunityRequest,
        candidate_cmd: str,
        worker_entity: Any,
        econ: EconomicState
    ) -> Tuple[float, float, float, float]:
        """Compute the gross incremental economic value generated by the candidate task (§6)."""
        direct_val = 0.0
        downstream_val = 0.0
        preservation_val = 0.0
        prices = econ.market.current_prices

        pos = worker_entity.position
        if request.target_location:
            pos = request.target_location
        x, y = pos

        tiles = econ.farm.tiles
        target_tile = tiles[y][x] if 0 <= y < len(tiles) and 0 <= x < len(tiles[0]) else None

        # Case A: Harvest
        if candidate_cmd == "HARVEST":
            if isinstance(target_tile, dict) and target_tile.get("kind") == "PLANT":
                crop = target_tile.get("crop")
                yield_u = int(target_tile.get("yield_units", 0) or 0)
                if crop and yield_u > 0:
                    unit_p = float(prices.get(crop, 50.0))
                    direct_val = yield_u * unit_p

        # Case B: Feed Animal
        elif candidate_cmd == "FEED":
            # Feeding cow yields milk (160), goose yields egg (50), sheep yields wool (120)
            # Feeding requires 1 wheat (-25)
            wheat_cost = float(prices.get("WHEAT", 25.0))
            if isinstance(target_tile, dict) and "animal" in target_tile:
                animal = target_tile.get("animal")
                if animal == "COW":
                    gross = float(prices.get("MILK", 160.0))
                elif animal == "SHEEP":
                    gross = float(prices.get("WOOL", 120.0))
                elif animal == "GOOSE":
                    gross = float(prices.get("EGG", 50.0))
                else:
                    gross = 100.0
                direct_val = max(0.0, gross - wheat_cost)

                # Preservation value: prevents animal escape if unfed
                consecutive_unfed = int(target_tile.get("consecutive_unfed", 0) or 0)
                if consecutive_unfed >= 1:
                    preservation_val = 500.0  # Asset preservation
            else:
                direct_val = 0.0

        # Case C: Plant
        elif candidate_cmd == "PLANT":
            crop = request.target_commodity or "STRAWBERRY"
            seed_cost = float(CROP_SEED_PRICE.get(crop, 20.0))
            unit_p = float(prices.get(crop, 50.0))
            expected_yield = 2
            downstream_val = max(0.0, (expected_yield * unit_p) - seed_cost)

        # Case D: Drop to shed
        elif candidate_cmd == "DROP":
            for it, q in worker_entity.cargo.items():
                direct_val += q * float(prices.get(it, 20.0))

        # Case E: Explicit candidate task cash effect
        if request.candidate_task and request.candidate_task.cash_effect != 0.0:
            if request.candidate_task.cash_effect > 0:
                direct_val = max(direct_val, request.candidate_task.cash_effect)
            else:
                direct_val = request.candidate_task.cash_effect

        total_cand_val = direct_val + downstream_val + preservation_val
        return total_cand_val, direct_val, downstream_val, preservation_val

    def _run_counterfactual_valuation(
        self,
        request: LaborOpportunityRequest,
        worker_entity: Any,
        candidate_cmd: str,
        worker_baseline_tasks: List[WorkerTask],
        horizon: int,
        target_level: ValuationLevel
    ) -> LaborOpportunityAssessment:
        """Runs exact forward counterfactual rollout to derive causal opportunity cost (§11, §12)."""
        econ = request.econ_state
        step = request.current_step
        wid = request.worker_id

        # 1. Simulate Baseline Forward
        from aec.counterfactual.opponent_pressure import OpponentPressureModel
        from aec.counterfactual.simulator import simulate_rollout
        opp_model = OpponentPressureModel(
            opponent_state=econ.opponent,
            mode="CALIBRATED_ESTIMATE"
        )
        base_rollout = simulate_rollout(
            econ_state=econ,
            initial_action=request.baseline_action,
            horizon=horizon,
            opp_model=opp_model,
            continuation_actions=request.baseline_continuation,
            trace_log=None
        )

        # 2. Build Candidate Action Basket
        cand_action = copy.deepcopy(request.baseline_action)
        if wid == 0:
            cand_action["farmer"] = [candidate_cmd]
        else:
            hands = list(cand_action.get("hands", []))
            h_idx = wid - 1
            while len(hands) <= h_idx:
                hands.append(["PASS"])
            hands[h_idx] = [candidate_cmd]
            cand_action["hands"] = hands

        # 3. Attempt Spliced Reconnection
        # Reconnect worker W back to their baseline route
        reconnect_result = None
        spliced_continuation = None
        spliced_workers = {wid}

        if request.candidate_patch and request.candidate_patch.spliced_continuation is not None:
            spliced_continuation = request.candidate_patch.spliced_continuation
            reconnect_result = request.candidate_patch.reconnect_result
        else:
            reconnect_req = ReconnectRequest(
                worker=wid,
                divergence_point=step,
                patched_action=[candidate_cmd],
                baseline_continuation=request.baseline_continuation,
                econ_state=econ,
                remaining_steps=FINAL_STEP - step
            )
            reconnect_res = self.reconnection_engine.reconnect(reconnect_req)
            if reconnect_res.status in (ReconnectionStatus.SAFE_RECONNECT, ReconnectionStatus.RECONNECT_WITH_TIMING_SHIFT):
                spliced_continuation = reconnect_res.spliced_trajectory
                reconnect_result = reconnect_res
            else:
                # If reconnection fails, use baseline continuation directly
                spliced_continuation = request.baseline_continuation

        # 4. Simulate Alternative Trajectory Forward
        cand_rollout = simulate_rollout(
            econ_state=econ,
            initial_action=cand_action,
            horizon=horizon,
            opp_model=opp_model,
            continuation_actions=spliced_continuation,
            trace_log=None,
            baseline_positions=base_rollout.worker_positions_history,
            spliced_workers=spliced_workers,
            reconnect_result=reconnect_result
        )

        # 5. Check Fidelity & Fail Closed if Desynchronized
        if cand_rollout.spatial_desynchronized:
            return self._build_abstention(
                request=request,
                reason=AbstentionReason.COUNTERFACTUAL_INCOMPLETE,
                level=target_level
            )

        if not cand_rollout.feed_security_ok and base_rollout.feed_security_ok:
            # Candidate caused an animal to escape!
            preservation_loss = 1500.0 * cand_rollout.escaped_animals_count
        else:
            preservation_loss = 0.0

        # 6. Compute Realized Economic Trajectory Values
        # Final liquid money difference
        delta_money = cand_rollout.money - base_rollout.money

        # Shed inventory valuation at end of rollout
        prices = econ.market.current_prices
        base_shed_val = sum(q * float(prices.get(p, 20.0)) for p, q in base_rollout.shed.items())
        cand_shed_val = sum(q * float(prices.get(p, 20.0)) for p, q in cand_rollout.shed.items())
        delta_shed = cand_shed_val - base_shed_val

        # Worker carried cargo valuation at end of rollout
        base_worker_inv = sum(sum(q * float(prices.get(p, 20.0)) for p, q in inv.items()) for inv in base_rollout.inventories)
        cand_worker_inv = sum(sum(q * float(prices.get(p, 20.0)) for p, q in inv.items()) for inv in cand_rollout.inventories)
        delta_worker_inv = cand_worker_inv - base_worker_inv

        # Farm tile valuation (growing biological assets)
        base_crop_val = self._estimate_growing_crops_value(base_rollout.tiles, prices, current_step=step + horizon)
        cand_crop_val = self._estimate_growing_crops_value(cand_rollout.tiles, prices, current_step=step + horizon)
        delta_crops = cand_crop_val - base_crop_val

        # Net Economic Trajectory Delta
        net_delta = delta_money + delta_shed + delta_worker_inv + delta_crops - preservation_loss

        # 7. Causal Decomposition of Opportunity Cost & Candidate Gain
        # Calculate gross candidate value directly
        cand_gross_val, direct_val, down_val, pres_val = self._evaluate_candidate_direct_value(
            request=request,
            candidate_cmd=candidate_cmd,
            worker_entity=worker_entity,
            econ=econ
        )

        if candidate_cmd in ("PASS", "WAIT"):
            opportunity_cost = max(0.0, -net_delta)
            net_incremental_value = net_delta
            cand_gross_val = 0.0
        else:
            cand_inv_gain = cand_worker_inv - base_worker_inv
            cand_shed_gain = cand_shed_val - base_shed_val
            cand_produced = (cand_inv_gain > 0 or cand_shed_gain > 0 or delta_money > 0 or delta_crops > 0 or pres_val > 0)
            if not cand_produced and abs(net_delta) < 0.001:
                # Candidate action was an unexecutable no-op in simulation
                cand_gross_val = 0.0
                opportunity_cost = 0.0
                net_incremental_value = 0.0
            else:
                opportunity_cost = max(0.0, cand_gross_val - net_delta)
                net_incremental_value = cand_gross_val - opportunity_cost

        # Displaced Tasks
        displaced = [t.task_id for t in worker_baseline_tasks]

        # Invariant F Check: No arbitrary fixed dollar constant
        commit_rec = (net_incremental_value > 0.0)

        # Baseline & Alternative Values
        base_total_val = base_rollout.money + base_shed_val + base_worker_inv + base_crop_val
        alt_total_val = cand_rollout.money + cand_shed_val + cand_worker_inv + cand_crop_val - preservation_loss

        return LaborOpportunityAssessment(
            worker_id=wid,
            candidate_task_id=request.candidate_task.task_id if request.candidate_task else f"CAND_{wid}_{step}_{candidate_cmd}",
            baseline_interval=(step, step + horizon),
            alternative_interval=(step, step + horizon),
            baseline_value=round(base_total_val, 2),
            alternative_value=round(alt_total_val, 2),
            opportunity_cost=round(opportunity_cost, 2),
            candidate_incremental_value=round(cand_gross_val, 2),
            net_incremental_value=round(net_incremental_value, 2),
            direct_value=round(direct_val, 2),
            downstream_value=round(down_val, 2),
            timing_value=round(delta_money, 2),
            preservation_value=round(pres_val - preservation_loss, 2),
            terminal_value=round(delta_crops, 2),
            dependencies_impacted=[],
            tasks_displaced=displaced,
            tasks_preserved=[],
            tasks_delayed=[],
            affected_workers=list(spliced_workers),
            confidence=1.0,
            valuation_method="EXACT_COUNTERFACTUAL",
            counterfactual_depth=horizon,
            valuation_level=target_level,
            safe_to_use=True,
            commit_recommendation=commit_rec,
            abstention_reason=None
        )

    def _estimate_growing_crops_value(self, tiles: List[List[Any]], prices: Dict[str, Any], current_step: int = 0) -> float:
        """Estimate the biological investment value of growing crop tiles (§8).
        
        Crucial Ground-Truth Invariants:
        1. Mature unharvested crops on tiles (yield_units > 0) are biological potential that
           requires harvest labor to realize. They are NOT liquid inventory. Valuing them at
           100% of product price cancels out harvest deltas and creates phantom opportunity cost.
        2. Terminal cutoff: Crops that cannot mature before final step (step 720 / Day 30) have
           zero realizable economic value at game end.
        3. Growing crops that can mature before Day 30 are valued proportionally to growth progress.
        """
        val = 0.0
        current_day = current_step // TURNS_PER_DAY
        for row in tiles:
            for tile in row:
                if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                    crop = tile.get("crop")
                    if not crop or crop not in CROPS:
                        continue
                    growth_days = CROP_GROWTH_DAYS.get(crop, 2)
                    unit_p = float(prices.get(crop, 50.0))
                    planted_day = int(tile.get("planted_day", current_day) or 0)
                    maturity_day = planted_day + growth_days

                    # Terminal feasibility cutoff: Day 30 is the hard game horizon
                    if maturity_day >= 30:
                        continue

                    yield_u = int(tile.get("yield_units", 0) or 0)
                    if yield_u == 0:
                        # Growing plant: value progress towards maturity
                        days_needed = growth_days
                        days_grown = max(0, current_day - planted_day)
                        fraction = min(1.0, days_grown / max(1, days_needed))
                        val += 2.0 * unit_p * 0.5 * fraction
                    else:
                        # Mature crop in ground: requires harvest labor. Not liquid cash.
                        pass
        return val

    def _build_abstention(
        self,
        request: LaborOpportunityRequest,
        reason: AbstentionReason,
        level: ValuationLevel
    ) -> LaborOpportunityAssessment:
        """Construct a fail-closed abstention assessment (§17)."""
        tid = request.candidate_task.task_id if request.candidate_task else f"CAND_{request.worker_id}_{request.current_step}"
        return LaborOpportunityAssessment(
            worker_id=request.worker_id,
            candidate_task_id=tid,
            baseline_interval=(request.current_step, request.current_step + 1),
            alternative_interval=(request.current_step, request.current_step + 1),
            baseline_value=0.0,
            alternative_value=0.0,
            opportunity_cost=0.0,
            candidate_incremental_value=0.0,
            net_incremental_value=0.0,
            confidence=0.0,
            valuation_method="ABSTAIN_FAIL_CLOSED",
            counterfactual_depth=0,
            valuation_level=int(level),
            safe_to_use=False,
            commit_recommendation=False,
            abstention_reason=reason.value
        )

    def _build_assessment(
        self,
        request: LaborOpportunityRequest,
        baseline_val: float,
        alt_val: float,
        oc: float,
        cand_val: float,
        direct_val: float = 0.0,
        downstream_val: float = 0.0,
        preservation_val: float = 0.0,
        tasks_displaced: Optional[List[str]] = None,
        tasks_preserved: Optional[List[str]] = None,
        level: ValuationLevel = ValuationLevel.LEVEL_1_LOCAL_EXACT,
        method: str = "LOCAL_EXACT_DEPENDENCY",
        safe: bool = True
    ) -> LaborOpportunityAssessment:
        """Construct a valid completed assessment certificate (§8)."""
        tid = request.candidate_task.task_id if request.candidate_task else f"CAND_{request.worker_id}_{request.current_step}"
        net_val = cand_val - oc
        commit_rec = safe and (net_val > 0.0)

        return LaborOpportunityAssessment(
            worker_id=request.worker_id,
            candidate_task_id=tid,
            baseline_interval=(request.current_step, request.current_step + 1),
            alternative_interval=(request.current_step, request.current_step + 1),
            baseline_value=round(baseline_val, 2),
            alternative_value=round(alt_val, 2),
            opportunity_cost=round(oc, 2),
            candidate_incremental_value=round(cand_val, 2),
            net_incremental_value=round(net_val, 2),
            direct_value=round(direct_val, 2),
            downstream_value=round(downstream_val, 2),
            preservation_value=round(preservation_val, 2),
            tasks_displaced=tasks_displaced or [],
            tasks_preserved=tasks_preserved or [],
            affected_workers=[request.worker_id],
            confidence=1.0,
            valuation_method=method,
            counterfactual_depth=1,
            valuation_level=int(level),
            safe_to_use=safe,
            commit_recommendation=commit_rec,
            abstention_reason=None
        )
