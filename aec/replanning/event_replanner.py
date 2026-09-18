# SPDX-License-Identifier: MIT
"""Event-Triggered Replanning Controller and Escalation Policy (§5, §6)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional, Set, Tuple

from aec.config import BOARD_SIZE, EPISODE_STEPS, PRODUCTS, SHED_TILES
from aec.ir.economic_state import EconomicState


class ReplanTrigger(str, Enum):
    """Formal triggers for event-driven replanning (§5)."""
    WORKER_IDLE = "WORKER_IDLE"
    TASK_COMPLETED_EARLY = "TASK_COMPLETED_EARLY"
    CROP_MATURE = "CROP_MATURE"
    ROUTE_BLOCKED = "ROUTE_BLOCKED"
    RESOURCE_DEPENDENCY_CHANGED = "RESOURCE_DEPENDENCY_CHANGED"
    CASH_STATE_CHANGED = "CASH_STATE_CHANGED"
    SHED_CAPACITY_CHANGED = "SHED_CAPACITY_CHANGED"
    LIVESTOCK_SECURITY_RISK = "LIVESTOCK_SECURITY_RISK"
    MARKET_PRICE_CHANGED = "MARKET_PRICE_CHANGED"
    OPPONENT_PRESSURE_CHANGED = "OPPONENT_PRESSURE_CHANGED"
    TERMINAL_WINDOW_ENTERED = "TERMINAL_WINDOW_ENTERED"
    BASELINE_ROUTE_STALE = "BASELINE_ROUTE_STALE"
    POSTCONDITION_INVALIDATED = "POSTCONDITION_INVALIDATED"
    WORKER_ASSIGNMENT_CHANGED = "WORKER_ASSIGNMENT_CHANGED"


class ReplanEscalationLevel(IntEnum):
    """Hierarchical dependency-aware escalation levels (§6)."""
    L1_LOCAL_TACTICAL = 1           # Local tactical change (single step / local order)
    L2_SAME_WORKER_RESOURCE = 2     # Same worker + same resource closure
    L3_ASSET_CASH_DEPENDENCY = 3    # Same asset / same cash dependency
    L4_MULTI_WORKER_MARKET = 4      # Multi-worker / market / terminal impact
    L5_FULL_REMAINING_HORIZON = 5   # Full remaining-horizon replanning


@dataclass
class ReplanEvent:
    """A state-derived trigger event requiring replanning evaluation."""
    trigger: ReplanTrigger
    step: int
    severity: float = 0.5            # 0.0 (negligible) to 1.0 (critical)
    worker_id: Optional[int] = None
    target_pos: Optional[Tuple[int, int]] = None
    entity: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trigger": self.trigger.value,
            "step": self.step,
            "severity": round(self.severity, 3),
            "worker_id": self.worker_id,
            "target_pos": self.target_pos,
            "entity": self.entity,
            "rationale": self.rationale,
            "payload": self.payload,
        }


@dataclass
class ReplanDecision:
    """The outcome of the replanning escalation analysis."""
    should_replan: bool
    escalation_level: ReplanEscalationLevel
    recommended_horizon: int
    affected_workers: List[int] = field(default_factory=list)
    affected_resources: List[str] = field(default_factory=list)
    trigger_events: List[ReplanEvent] = field(default_factory=list)
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "should_replan": self.should_replan,
            "escalation_level": int(self.escalation_level),
            "recommended_horizon": self.recommended_horizon,
            "affected_workers": self.affected_workers,
            "affected_resources": self.affected_resources,
            "trigger_count": len(self.trigger_events),
            "rationale": self.rationale,
        }


@dataclass
class ReplanPolicy:
    """Policy thresholds governing when state changes escalate (§6)."""
    cash_material_delta: float = 150.0
    price_material_shift: float = 0.20
    shed_alarm_threshold: int = 90
    terminal_step_threshold: int = 680
    opponent_pressure_shift: float = 0.25

    # Horizon mapping per level
    horizon_by_level: Dict[ReplanEscalationLevel, int] = field(default_factory=lambda: {
        ReplanEscalationLevel.L1_LOCAL_TACTICAL: 4,
        ReplanEscalationLevel.L2_SAME_WORKER_RESOURCE: 12,
        ReplanEscalationLevel.L3_ASSET_CASH_DEPENDENCY: 24,
        ReplanEscalationLevel.L4_MULTI_WORKER_MARKET: 48,
        ReplanEscalationLevel.L5_FULL_REMAINING_HORIZON: 72,
    })


class EventTriggeredReplanner:
    """Generalized state-derived replan controller.
    
    Detects events, classifies impact, computes dependency closure,
    and escalates horizon dynamically rather than replanning blindly every turn.
    """

    def __init__(self, policy: Optional[ReplanPolicy] = None) -> None:
        self.policy = policy or ReplanPolicy()
        self._last_replan_step: int = -1

    def detect_triggers(
        self,
        econ_state: EconomicState,
        prev_econ_state: Optional[EconomicState],
        baseline_action: Optional[Dict[str, Any]] = None,
        active_patch: Optional[Any] = None,
    ) -> List[ReplanEvent]:
        """Detect all state-derived replanning triggers from current state."""
        events: List[ReplanEvent] = []
        step = econ_state.step

        # 1. Worker Idle & Task Completed Early
        baseline_action = baseline_action or {}
        farmer_acts = baseline_action.get("farmer", [])
        hands_acts = baseline_action.get("hands", [])

        for w in econ_state.workers.workers:
            wid = w.worker_id
            cmd = "PASS"
            if wid == 0:
                cmd = farmer_acts[0] if farmer_acts else "PASS"
            else:
                h_idx = wid - 1
                if h_idx < len(hands_acts) and hands_acts[h_idx]:
                    cmd = hands_acts[h_idx][0]

            if cmd == "PASS" and not getattr(w, "is_frozen", False):
                events.append(ReplanEvent(
                    trigger=ReplanTrigger.WORKER_IDLE,
                    step=step,
                    severity=0.6,
                    worker_id=wid,
                    rationale=f"Worker {wid} is idle ('PASS') while operational.",
                ))

            # Check if previous patch finished early or cargo became empty
            if prev_econ_state is not None:
                prev_w = next((pw for pw in prev_econ_state.workers.workers if pw.worker_id == wid), None)
                if prev_w and prev_w.cargo and not w.cargo:
                    events.append(ReplanEvent(
                        trigger=ReplanTrigger.TASK_COMPLETED_EARLY,
                        step=step,
                        severity=0.5,
                        worker_id=wid,
                        rationale=f"Worker {wid} cargo cleared (task completed).",
                    ))

        # 2. Crop Mature
        for crop in getattr(econ_state.farm, "crops", []):
            is_mature = getattr(crop, "is_mature", False) or getattr(crop, "growth_stage", 0) >= getattr(crop, "max_growth", 1)
            if is_mature:
                pos = getattr(crop, "position", (0, 0))
                events.append(ReplanEvent(
                    trigger=ReplanTrigger.CROP_MATURE,
                    step=step,
                    severity=0.7,
                    target_pos=pos,
                    entity=getattr(crop, "crop_type", "CROP"),
                    rationale=f"Mature crop ready at {pos}.",
                ))

        # 3. Cash State Changed Materially
        if prev_econ_state is not None:
            cash_diff = abs(econ_state.cash - prev_econ_state.cash)
            if cash_diff >= self.policy.cash_material_delta:
                events.append(ReplanEvent(
                    trigger=ReplanTrigger.CASH_STATE_CHANGED,
                    step=step,
                    severity=min(1.0, cash_diff / 500.0),
                    rationale=f"Cash balance shifted materially by ${cash_diff:.1f} (now ${econ_state.cash:.1f}).",
                    payload={"delta_cash": cash_diff, "current_cash": econ_state.cash}
                ))

        # 4. Shed Capacity Changed / Risk
        shed_count = econ_state.farm.shed_inventory_count
        if shed_count >= self.policy.shed_alarm_threshold:
            events.append(ReplanEvent(
                trigger=ReplanTrigger.SHED_CAPACITY_CHANGED,
                step=step,
                severity=0.85,
                rationale=f"Shed capacity near overflow: {shed_count}/100 items.",
                payload={"shed_count": shed_count}
            ))

        # 5. Livestock Security Risk
        for animal in getattr(econ_state.farm, "animals", []):
            turns_to_starve = getattr(animal, "turns_to_starve", 999)
            if turns_to_starve <= 12:
                events.append(ReplanEvent(
                    trigger=ReplanTrigger.LIVESTOCK_SECURITY_RISK,
                    step=step,
                    severity=1.0,
                    entity=getattr(animal, "animal_type", "ANIMAL"),
                    rationale=f"Animal starvation imminent in {turns_to_starve} steps.",
                    payload={"turns_to_starve": turns_to_starve}
                ))

        # 6. Market Price Changed Materially
        if prev_econ_state is not None:
            for prod in PRODUCTS:
                p_curr = econ_state.market.prices.get(prod, 0.0)
                p_prev = prev_econ_state.market.prices.get(prod, 0.0)
                if p_prev > 0:
                    rel_shift = abs(p_curr - p_prev) / p_prev
                    if rel_shift >= self.policy.price_material_shift:
                        events.append(ReplanEvent(
                            trigger=ReplanTrigger.MARKET_PRICE_CHANGED,
                            step=step,
                            severity=min(1.0, rel_shift),
                            entity=prod,
                            rationale=f"Market price of {prod} shifted by {rel_shift*100:.1f}%.",
                            payload={"product": prod, "rel_shift": rel_shift, "price": p_curr}
                        ))

        # 7. Opponent Pressure Changed Materially
        if prev_econ_state is not None and econ_state.opponent is not None and prev_econ_state.opponent is not None:
            opp_curr_cash = getattr(econ_state.opponent, "cash", 0.0)
            opp_prev_cash = getattr(prev_econ_state.opponent, "cash", 0.0)
            if abs(opp_curr_cash - opp_prev_cash) >= 300.0:
                events.append(ReplanEvent(
                    trigger=ReplanTrigger.OPPONENT_PRESSURE_CHANGED,
                    step=step,
                    severity=0.75,
                    rationale=f"Opponent cash changed by ${abs(opp_curr_cash - opp_prev_cash):.1f}.",
                    payload={"opp_cash": opp_curr_cash}
                ))

        # 8. Terminal Window Entered
        if step >= self.policy.terminal_step_threshold:
            rem = EPISODE_STEPS - step
            events.append(ReplanEvent(
                trigger=ReplanTrigger.TERMINAL_WINDOW_ENTERED,
                step=step,
                severity=0.9,
                rationale=f"Terminal endgame window reached ({rem} steps remaining).",
                payload={"remaining_steps": rem}
            ))

        # 9. Active Patch Postcondition / Continuation Invalidated
        if active_patch is not None:
            # Check if active patch pre/postconditions were violated
            if hasattr(active_patch, "is_valid") and not active_patch.is_valid(econ_state):
                events.append(ReplanEvent(
                    trigger=ReplanTrigger.POSTCONDITION_INVALIDATED,
                    step=step,
                    severity=1.0,
                    rationale="Active patch postcondition or invariant invalidated.",
                ))

        return events

    def compute_dependency_closure(
        self,
        events: List[ReplanEvent],
        econ_state: EconomicState
    ) -> Tuple[Set[int], Set[str]]:
        """Compute the set of affected worker IDs and resource entities (§5)."""
        affected_workers: Set[int] = set()
        affected_resources: Set[str] = set()

        for ev in events:
            if ev.worker_id is not None:
                affected_workers.add(ev.worker_id)
            if ev.entity is not None:
                affected_resources.add(ev.entity)
            if ev.trigger in (ReplanTrigger.SHED_CAPACITY_CHANGED, ReplanTrigger.CASH_STATE_CHANGED):
                # Impacts all workers
                for w in econ_state.workers.workers:
                    affected_workers.add(w.worker_id)
            if ev.trigger == ReplanTrigger.TERMINAL_WINDOW_ENTERED:
                for w in econ_state.workers.workers:
                    affected_workers.add(w.worker_id)
                for p in PRODUCTS:
                    affected_resources.add(p)

        return affected_workers, affected_resources

    def classify_and_escalate(
        self,
        events: List[ReplanEvent],
        econ_state: EconomicState
    ) -> ReplanDecision:
        """Classify triggers and assign appropriate escalation level L1-L5 (§6)."""
        if not events:
            return ReplanDecision(
                should_replan=False,
                escalation_level=ReplanEscalationLevel.L1_LOCAL_TACTICAL,
                recommended_horizon=self.policy.horizon_by_level[ReplanEscalationLevel.L1_LOCAL_TACTICAL],
                rationale="No triggers detected."
            )

        affected_workers, affected_resources = self.compute_dependency_closure(events, econ_state)
        triggers = {e.trigger for e in events}

        # Level 5: Full Remaining-Horizon Replanning
        # Required if terminal endgame reached with critical asset/worker dependency
        if (ReplanTrigger.TERMINAL_WINDOW_ENTERED in triggers and len(affected_workers) > 1) or \
           (ReplanTrigger.POSTCONDITION_INVALIDATED in triggers and len(affected_workers) > 1):
            rem_horizon = min(EPISODE_STEPS - econ_state.step, self.policy.horizon_by_level[ReplanEscalationLevel.L5_FULL_REMAINING_HORIZON])
            return ReplanDecision(
                should_replan=True,
                escalation_level=ReplanEscalationLevel.L5_FULL_REMAINING_HORIZON,
                recommended_horizon=max(12, rem_horizon),
                affected_workers=sorted(affected_workers),
                affected_resources=sorted(affected_resources),
                trigger_events=events,
                rationale="L5 Escalation: Critical terminal or invalidation event impacting full system horizon."
            )

        # Level 4: Multi-Worker / Market / Terminal Impact
        if ReplanTrigger.TERMINAL_WINDOW_ENTERED in triggers or \
           ReplanTrigger.SHED_CAPACITY_CHANGED in triggers or \
           ReplanTrigger.LIVESTOCK_SECURITY_RISK in triggers or \
           len(affected_workers) > 1:
            return ReplanDecision(
                should_replan=True,
                escalation_level=ReplanEscalationLevel.L4_MULTI_WORKER_MARKET,
                recommended_horizon=self.policy.horizon_by_level[ReplanEscalationLevel.L4_MULTI_WORKER_MARKET],
                affected_workers=sorted(affected_workers),
                affected_resources=sorted(affected_resources),
                trigger_events=events,
                rationale="L4 Escalation: Multi-worker, high-risk livestock, or shed-wide capacity event."
            )

        # Level 3: Same Asset / Same Cash Dependency
        if ReplanTrigger.CASH_STATE_CHANGED in triggers or \
           ReplanTrigger.MARKET_PRICE_CHANGED in triggers or \
           ReplanTrigger.OPPONENT_PRESSURE_CHANGED in triggers:
            return ReplanDecision(
                should_replan=True,
                escalation_level=ReplanEscalationLevel.L3_ASSET_CASH_DEPENDENCY,
                recommended_horizon=self.policy.horizon_by_level[ReplanEscalationLevel.L3_ASSET_CASH_DEPENDENCY],
                affected_workers=sorted(affected_workers),
                affected_resources=sorted(affected_resources),
                trigger_events=events,
                rationale="L3 Escalation: Financial or market valuation change impacting asset cash dependencies."
            )

        # Level 2: Same Worker + Same Resource Closure
        if ReplanTrigger.CROP_MATURE in triggers or \
           ReplanTrigger.RESOURCE_DEPENDENCY_CHANGED in triggers:
            return ReplanDecision(
                should_replan=True,
                escalation_level=ReplanEscalationLevel.L2_SAME_WORKER_RESOURCE,
                recommended_horizon=self.policy.horizon_by_level[ReplanEscalationLevel.L2_SAME_WORKER_RESOURCE],
                affected_workers=sorted(affected_workers),
                affected_resources=sorted(affected_resources),
                trigger_events=events,
                rationale="L2 Escalation: Mature crop or resource availability on worker's local domain."
            )

        # Level 1: Local Tactical Change (idle worker / route blocked / task completed early)
        return ReplanDecision(
            should_replan=True,
            escalation_level=ReplanEscalationLevel.L1_LOCAL_TACTICAL,
            recommended_horizon=self.policy.horizon_by_level[ReplanEscalationLevel.L1_LOCAL_TACTICAL],
            affected_workers=sorted(affected_workers),
            affected_resources=sorted(affected_resources),
            trigger_events=events,
            rationale="L1 Escalation: Local tactical event (worker idle or completed task early)."
        )

    def decide(
        self,
        econ_state: EconomicState,
        prev_econ_state: Optional[EconomicState],
        baseline_action: Optional[Dict[str, Any]] = None,
        active_patch: Optional[Any] = None,
    ) -> ReplanDecision:
        """Full pipeline: detect -> classify -> compute closure -> decide escalation."""
        triggers = self.detect_triggers(econ_state, prev_econ_state, baseline_action, active_patch)
        decision = self.classify_and_escalate(triggers, econ_state)
        if decision.should_replan:
            self._last_replan_step = econ_state.step
        return decision
