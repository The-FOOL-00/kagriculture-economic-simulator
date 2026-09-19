# SPDX-License-Identifier: MIT
"""AEC Central Compiler Orchestrator and Executor (§4, §30, §31, §32)."""

from __future__ import annotations

import copy
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from aec.config import AECConfig, MECHANISM_REGISTRY, ScientificStatus
from aec.counterfactual.horizon import select_adaptive_horizon
from aec.counterfactual.macro_detector import MacroRegimeTransitionDetector
from aec.counterfactual.simulator import CounterfactualSimulator
from aec.evaluation.win_model import WinModel
from aec.events.detectors import detect_events
from aec.events.event_bus import EventBus
from aec.integration.backbone_adapter import BackboneAdapter, BaselineResult
from aec.ir.economic_state import EconomicState, build_economic_state
from aec.counterfactual.opponent_pressure import ContinuousOpponentPressureAnalyzer, OpponentPressureState
from aec.funnel.candidate_funnel import FunnelTelemetry, InferenceBudget, OpportunityCandidateFunnel
from aec.funnel.reservation import FunnelReservationPolicy
from aec.integration.fallback import FallbackReason, FallbackRecord, RobustFallbackPolicy
from aec.macro.macro_controller import MacroController, MacroStrategy
from aec.meta.meta_policy import AECMode, MetaOrchestrator, MetaPolicyDecision
from aec.opportunities import OpportunityEngine
from aec.patches.generator import PatchGenerator
from aec.patches.patch import CoupledPatch
from aec.patches.pruning import prune_patches
from aec.replanning.event_replanner import EventTriggeredReplanner, ReplanDecision
from aec.safety.certificate import SafetyCertificate
from aec.safety.checks import SafetyChecker
from aec.tactical.tactical_planner import TacticalPlanner

_SAFE = {"farmer": ["PASS"], "hands": [], "market": []}


@dataclass
class CandidateTelemetry:
    """Detailed audit trace for an individual candidate mechanism (§14)."""
    patch_id: str
    mechanism_family: str
    opportunity_detected: bool = True
    patch_generated: bool = False
    patch_pruned: bool = False
    simulation_run: bool = False
    simulation_horizon: int = 0
    delta_money: float = 0.0
    delta_margin: float = 0.0
    delta_route_cost: float = 0.0
    delta_dependency_completion: float = 0.0
    delta_opponent_pressure: float = 0.0
    weed_asset_value: float = 0.0
    delta_money_realized: float = 0.0
    delta_margin_realized: float = 0.0
    projected_asset_value: float = 0.0
    projection_status: str = "REALIZED"
    spatial_consistency_ok: bool = True
    safety_pass: bool = False
    safety_rejection_reason: Optional[str] = None
    economic_rejection_reason: Optional[str] = None
    commit_decision: bool = False
    baseline_action: Optional[Dict[str, Any]] = None
    candidate_action: Optional[Dict[str, Any]] = None
    terminal_telemetry: Optional[Dict[str, Any]] = None
    why_v3_did_not_do_this: Optional[str] = None
    candidate_quantity: int = 0
    candidate_reason: Optional[str] = None
    macro_escalated: bool = False
    macro_regime_type: str = "NONE"
    macro_escalation_reason: Optional[str] = None
    first_divergence_turn: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "patch_id": self.patch_id,
            "family": self.mechanism_family,
            "opp_detected": self.opportunity_detected,
            "patch_generated": self.patch_generated,
            "patch_pruned": self.patch_pruned,
            "sim_run": self.simulation_run,
            "horizon": self.simulation_horizon,
            "delta_money": round(self.delta_money, 2),
            "delta_margin": round(self.delta_margin, 2),
            "delta_route_cost": round(self.delta_route_cost, 2),
            "delta_dependency_completion": self.delta_dependency_completion,
            "delta_opponent_pressure": round(self.delta_opponent_pressure, 2),
            "weed_asset_value": round(self.weed_asset_value, 2),
            "delta_money_realized": round(self.delta_money_realized, 2),
            "delta_margin_realized": round(self.delta_margin_realized, 2),
            "projected_asset_value": round(self.projected_asset_value, 2),
            "projection_status": self.projection_status,
            "spatial_consistency_ok": self.spatial_consistency_ok,
            "safety_pass": self.safety_pass,
            "safety_rejection": self.safety_rejection_reason,
            "economic_rejection": self.economic_rejection_reason,
            "commit_decision": self.commit_decision,
            "baseline_action": self.baseline_action,
            "candidate_action": self.candidate_action,
            "why_v3_did_not_do_this": self.why_v3_did_not_do_this,
            "candidate_quantity": self.candidate_quantity,
            "candidate_reason": self.candidate_reason,
            "macro_escalated": self.macro_escalated,
            "macro_regime_type": self.macro_regime_type,
            "macro_escalation_reason": self.macro_escalation_reason,
            "first_divergence_turn": self.first_divergence_turn,
        }
        if self.terminal_telemetry is not None:
            d["terminal_telemetry"] = self.terminal_telemetry
        return d



@dataclass
class AECTelemetry:
    """Structured telemetry recording AEC compiler decision trail per turn."""
    step: int = 0
    decision: str = "BACKBONE"          # "COMMIT", "BACKBONE", "ABSTAIN", "FAIL_SAFE"
    events_detected: List[str] = field(default_factory=list)
    opportunities_count: int = 0
    opportunities_quarantined_count: int = 0
    quarantined_by_mechanism: Dict[str, int] = field(default_factory=dict)
    candidates_count: int = 0
    simulations_run: int = 0
    committed_patch_id: Optional[str] = None
    committed_mechanism: Optional[str] = None
    abstain_reason: Optional[str] = None

    # Patch lifecycle counts
    patches_generated_count: int = 0
    patches_quarantined_count: int = 0
    patches_pruned_count: int = 0
    patches_simulated_count: int = 0
    patches_safety_rejected_count: int = 0
    patches_economically_rejected_count: int = 0

    # Macro-Aware Escalation telemetry (Phase 016)
    macro_escalations_count: int = 0
    macro_escalated_by_regime: Dict[str, int] = field(default_factory=dict)

    # Funnel reservation telemetry (Phase 018 Repair A): per-site records
    funnel_reservation: Dict[str, Any] = field(default_factory=dict)

    # Asset-holding firing log (Phase 018 Repair C): per-commodity trigger records
    trigger_firings: List[Dict[str, Any]] = field(default_factory=list)

    # Detailed per-candidate audit trace (§14)
    candidates: List[CandidateTelemetry] = field(default_factory=list)

    @property
    def mechanism(self) -> Optional[str]:
        """Alias for committed_mechanism or attempted mechanism for telemetry inspection."""
        return self.committed_mechanism

    # Latencies in milliseconds
    ir_time_ms: float = 0.0
    event_time_ms: float = 0.0
    opp_time_ms: float = 0.0
    sim_time_ms: float = 0.0
    safety_time_ms: float = 0.0
    total_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "decision": self.decision,
            "events": self.events_detected,
            "opp_count": self.opportunities_count,
            "opp_quarantined_count": self.opportunities_quarantined_count,
            "quarantined_by_mechanism": dict(self.quarantined_by_mechanism),
            "cand_count": self.candidates_count,
            "sim_count": self.simulations_run,
            "macro_escalations_count": self.macro_escalations_count,
            "macro_escalated_by_regime": dict(self.macro_escalated_by_regime),
            "funnel_reservation": {
                k: (v.to_dict() if hasattr(v, "to_dict") else v)
                for k, v in self.funnel_reservation.items()
            },
            "trigger_firings": [dict(r) for r in self.trigger_firings],
            "patch_id": self.committed_patch_id,
            "committed_mechanism": self.committed_mechanism,
            "abstain_reason": self.abstain_reason,
            "lifecycle": {
                "generated": self.patches_generated_count,
                "quarantined": self.patches_quarantined_count,
                "pruned": self.patches_pruned_count,
                "simulated": self.patches_simulated_count,
                "safety_rejected": self.patches_safety_rejected_count,
                "economically_rejected": self.patches_economically_rejected_count,
                "committed": 1 if self.decision == "COMMIT" else 0,
            },
            "candidates": [c.to_dict() for c in self.candidates],
            "latency_ms": {
                "ir": round(self.ir_time_ms, 2),
                "event": round(self.event_time_ms, 2),
                "opp": round(self.opp_time_ms, 2),
                "sim": round(self.sim_time_ms, 2),
                "safety": round(self.safety_time_ms, 2),
                "total": round(self.total_time_ms, 2),
            }
        }


class AECExecutor:
    """The Adaptive Economic Compiler runtime orchestrator.

    Coordinates the pipeline:
    Observe -> Baseline -> IR -> Events -> Opportunities -> Patches ->
    Counterfactuals -> Win Model -> Safety Certificate -> Commit / Abstain
    """

    def __init__(
        self,
        backbone_adapter: Optional[BackboneAdapter] = None,
        config: Optional[AECConfig] = None
    ) -> None:
        self.config = config or AECConfig()
        self.backbone = backbone_adapter or BackboneAdapter(config=self.config)

        # Subsystems with mechanism gating configuration
        self.event_bus = EventBus()
        self.opp_engine = OpportunityEngine(config=self.config)
        self.patch_generator = PatchGenerator(config=self.config)
        self.simulator = CounterfactualSimulator()
        self.win_model = WinModel()
        self.safety_checker = SafetyChecker()
        self.macro_detector = MacroRegimeTransitionDetector()

        # Phase 007 Architectural Subsystems (§5, §8, §10, §11, §12, §30)
        self.replanner = EventTriggeredReplanner()
        self.opponent_analyzer = ContinuousOpponentPressureAnalyzer()
        self.macro_controller = MacroController()
        self.tactical_planner = TacticalPlanner()
        mode_str = getattr(self.config, "operational_mode", "ROBUST_MODE")
        mode_enum = getattr(AECMode, mode_str, AECMode.ROBUST_MODE)
        self.meta_orchestrator = MetaOrchestrator(mode=mode_enum)
        self.funnel = OpportunityCandidateFunnel()
        self.fallback_policy = RobustFallbackPolicy()

        # Phase 018 Repair A: funnel reservation policy derived from config
        # (single mechanism shared by all truncation sites; OFF unless enabled).
        self._reservation_policy = FunnelReservationPolicy(
            enabled=bool(getattr(self.config, "enable_funnel_reservation", False)),
            reserved_fraction=float(
                getattr(self.config, "funnel_reserved_fraction", 0.25) or 0.25
            ),
        )

        # State tracking across steps
        self._prev_econ_state: Optional[EconomicState] = None
        self._telemetry_history: List[AECTelemetry] = []
        self._certificates: List[SafetyCertificate] = []
        self._latest_committed_patch: Optional[Any] = None
        self._in_flight_patch: Optional[Any] = None
        self._in_flight_start_step: int = 0

    def act(
        self,
        observation: Dict[str, Any],
        configuration: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Main execution entrypoint for Kaggle game turns."""
        self._latest_committed_patch = None
        t_start = time.perf_counter()
        step = int(observation.get("step", 0) or 0)
        telemetry = AECTelemetry(step=step)

        # ---------------------------------------------------------------------
        # 1. LIVE BASELINE INVOCATION (Enforces exactly one live call per turn)
        # ---------------------------------------------------------------------
        try:
            baseline_result: BaselineResult = self.backbone.call_once(observation, configuration)
        except Exception as e:
            telemetry.decision = "FAIL_SAFE"
            telemetry.abstain_reason = f"Backbone invocation failure: {str(e)}"
            telemetry.total_time_ms = (time.perf_counter() - t_start) * 1000.0
            self._telemetry_history.append(telemetry)
            return dict(_SAFE)

        baseline_action = baseline_result.canonical_action_copy()

        try:
            # -----------------------------------------------------------------
            # 2. ECONOMIC IR CONSTRUCTION
            # -----------------------------------------------------------------
            t_ir0 = time.perf_counter()
            econ_state = build_economic_state(observation, self._prev_econ_state)
            telemetry.ir_time_ms = (time.perf_counter() - t_ir0) * 1000.0

            # -----------------------------------------------------------------
            # 2B. OPPONENT PRESSURE, MACRO STRATEGY, & META ORCHESTRATION (§8, §10, §12)
            # -----------------------------------------------------------------
            pressure_state = self.opponent_analyzer.analyze(econ_state, self._prev_econ_state)
            macro_strategy = self.macro_controller.formulate_strategy(econ_state, pressure_state)
            meta_decision = self.meta_orchestrator.orchestrate(pressure_state, econ_state)

            # -----------------------------------------------------------------
            # 3. EVENT BUS, DETECTORS, & EVENT-TRIGGERED REPLANNER (§5, §6)
            # -----------------------------------------------------------------
            t_ev0 = time.perf_counter()
            self.event_bus.clear()
            events = detect_events(econ_state, self._prev_econ_state, baseline_action, self.config)
            self.event_bus.publish_many(events)
            replan_decision = self.replanner.decide(econ_state, self._prev_econ_state, baseline_action, self._latest_committed_patch)
            telemetry.event_time_ms = (time.perf_counter() - t_ev0) * 1000.0
            telemetry.events_detected = [e.event_type.value for e in events]

            # -----------------------------------------------------------------
            # 3B. IN-FLIGHT COUPLED TRAJECTORY PATCH CONTINUATION (§4, §8)
            # -----------------------------------------------------------------
            if step == 0:
                self._in_flight_patch = None
                self._in_flight_start_step = 0

            if self._in_flight_patch is not None:
                offset = step - self._in_flight_start_step
                # Critical abort if emergency feed deficit or solvency risk detected
                critical_abort = any(
                    e.event_type.value in ("FEED_DEFICIT_RISK", "SOLVENCY_RISK") for e in events
                )
                flight_actions = getattr(self._in_flight_patch, "actions", [])
                if not critical_abort and 0 < offset < len(flight_actions):
                    flight_act = flight_actions[offset]
                    final_action = copy.deepcopy(baseline_action)
                    w_ids = getattr(self._in_flight_patch, "worker_ids", [0])
                    spatial_valid = True
                    for wid in w_ids:
                        worker = econ_state.workers.get_worker(wid)
                        if worker is None:
                            spatial_valid = False
                            break
                        if wid == 0:
                            cmd = flight_act.get("farmer", ["PASS"])
                            final_action["farmer"] = list(cmd)
                        else:
                            h_cmds = flight_act.get("hands", []) or []
                            if wid - 1 < len(h_cmds):
                                while len(final_action.get("hands", [])) < wid:
                                    final_action.setdefault("hands", []).append(["PASS"])
                                final_action["hands"][wid - 1] = list(h_cmds[wid - 1])

                    if flight_act.get("market"):
                        m_orders = copy.deepcopy(final_action.get("market", []) or [])
                        for o in flight_act["market"]:
                            has_o = any(
                                isinstance(existing, (list, tuple)) and len(existing) >= 2 and len(o) >= 2 and existing[0] == o[0] and existing[1] == o[1]
                                for existing in m_orders
                            )
                            if not has_o and len(m_orders) < 10:
                                m_orders.insert(0, copy.deepcopy(o))
                        final_action["market"] = m_orders[:10]

                    if spatial_valid:
                        telemetry.decision = "COMMIT"
                        telemetry.committed_patch_id = f"{self._in_flight_patch.patch_id}_step_{offset}"
                        telemetry.committed_mechanism = getattr(self._in_flight_patch, "mechanism_family", "")
                        telemetry.total_time_ms = (time.perf_counter() - t_start) * 1000.0
                        self._record_step(econ_state, telemetry)
                        return final_action
                    else:
                        self._in_flight_patch = None
                else:
                    self._in_flight_patch = None

            # NO-EVENT FAST PATH (§8):
            # If no planning event exists, immediately emit baseline unchanged
            if not self.event_bus.has_events:
                telemetry.decision = "BACKBONE"
                telemetry.abstain_reason = "NO_EVENT_FAST_PATH"
                telemetry.total_time_ms = (time.perf_counter() - t_start) * 1000.0
                self._record_step(econ_state, telemetry)
                return baseline_action

            # -----------------------------------------------------------------
            # 4. OPPORTUNITY ENGINE (Layer 1 Defense & §23)
            # -----------------------------------------------------------------
            # Read-only future backbone continuation trajectory (zero live calls).
            # Extracted here (moved up from §5, behavior-neutral) so Phase 018 C3
            # tape separation can consult V3's native sale schedule at detection.
            n_hands = max(0, len(econ_state.workers.workers) - 1)
            future_trajectory = self.backbone.get_future_trajectory(
                step=step,
                horizon=self.config.extended_horizon,
                player=econ_state.player,
                n_hands=n_hands
            )
            t_opp0 = time.perf_counter()
            opportunities = self.opp_engine.detect_opportunities(
                econ_state,
                events,
                baseline_action,
                max_opportunities=self.config.max_opportunities,
                config=self.config,
                pressure_state=pressure_state,
                v3_tape=future_trajectory,
            )
            telemetry.trigger_firings = list(
                getattr(self.opp_engine, "last_firing_log", []) or []
            )
            telemetry.opportunities_count = len(opportunities)
            telemetry.opp_time_ms = (time.perf_counter() - t_opp0) * 1000.0

            if getattr(self.opp_engine, "last_reservation_telemetry", None) is not None:
                telemetry.funnel_reservation["opportunities"] = (
                    self.opp_engine.last_reservation_telemetry
                )

            quarantined_opps = self.opp_engine.last_quarantined_opportunities
            telemetry.opportunities_quarantined_count = len(quarantined_opps)
            for q in quarantined_opps:
                fam = q.candidate_transformation_family
                telemetry.quarantined_by_mechanism[fam] = (
                    telemetry.quarantined_by_mechanism.get(fam, 0) + 1
                )

            if not opportunities:
                telemetry.decision = "BACKBONE"
                telemetry.abstain_reason = "NO_OPPORTUNITIES_FOUND"
                telemetry.total_time_ms = (time.perf_counter() - t_start) * 1000.0
                self._record_step(econ_state, telemetry)
                return baseline_action

            # -----------------------------------------------------------------
            # 5. COUPLED PATCH GENERATION, FUNNEL, & MACRO/META SCREENING (Layer 2 Defense & §7, §10, §12)
            # -----------------------------------------------------------------
            # (future_trajectory extracted once above §4 and reused here.)
            from aec.replanning.reconnect import extract_all_worker_trajectories
            co_worker_trajectories = extract_all_worker_trajectories(econ_state, future_trajectory)

            raw_patches = self.patch_generator.generate_patches(
                opportunities,
                econ_state,
                baseline_action,
                config=self.config,
                baseline_continuation=future_trajectory,
                co_worker_trajectories=co_worker_trajectories,
            )
            telemetry.patches_generated_count = len(raw_patches) + self.patch_generator.last_quarantined_count
            telemetry.patches_quarantined_count = self.patch_generator.last_quarantined_count
            for fam, count in self.patch_generator.last_quarantined_by_mechanism.items():
                telemetry.quarantined_by_mechanism[fam] = (
                    telemetry.quarantined_by_mechanism.get(fam, 0) + count
                )

            # 5A. Candidate Funnel Screening (§7, §30)
            funnel_budget = InferenceBudget(
                max_turn_time_ms=self.config.per_step_latency_limit_ms,
                max_exact_simulations=self.config.max_simulations,
                max_candidates_screened=self.config.max_candidates,
            )
            screened_patches, funnel_telem = self.funnel.filter_candidates(
                raw_patches,
                econ_state,
                budget=funnel_budget,
                reservation_policy=self._reservation_policy,
                market_discrimination=bool(
                    getattr(self.config, "enable_market_patch_discrimination", False)
                ),
            )
            if getattr(self.funnel, "last_reservation_telemetry", None) is not None:
                telemetry.funnel_reservation["s9_top_k"] = (
                    self.funnel.last_reservation_telemetry
                )

            # 5B. Macro Compatibility Validation (§10)
            macro_approved_patches = []
            for p in screened_patches:
                m_ok, m_reason = self.macro_controller.validate_tactical_compatibility(p, macro_strategy, econ_state)
                if m_ok:
                    macro_approved_patches.append(p)
                else:
                    telemetry.candidates.append(CandidateTelemetry(
                        patch_id=p.patch_id,
                        mechanism_family=p.mechanism_family,
                        opportunity_detected=True,
                        patch_generated=True,
                        patch_pruned=True,
                        simulation_run=False,
                        safety_pass=False,
                        economic_rejection_reason=f"MACRO_INCOMPATIBLE: {m_reason}"
                    ))

            # 5C. META Strategic Prioritization (§12, §13)
            prioritized_patches = self.meta_orchestrator.prioritize_candidates(
                macro_approved_patches, meta_decision, pressure_state
            )

            candidate_patches = prune_patches(
                prioritized_patches,
                econ_state,
                max_candidates=self.config.max_candidates,
                reservation_policy=self._reservation_policy,
            )
            if getattr(self._reservation_policy, "last_telemetry", None) is not None:
                telemetry.funnel_reservation["prune_cap"] = (
                    self._reservation_policy.last_telemetry
                )
            telemetry.patches_pruned_count = max(0, len(raw_patches) - len(candidate_patches))
            telemetry.candidates_count = len(candidate_patches)

            # Record pruned patches in candidate telemetry (§14)
            cand_ids = {p.patch_id for p in candidate_patches}
            for p in raw_patches:
                if p.patch_id not in cand_ids:
                    telemetry.candidates.append(CandidateTelemetry(
                        patch_id=p.patch_id,
                        mechanism_family=p.mechanism_family,
                        opportunity_detected=True,
                        patch_generated=True,
                        patch_pruned=True,
                        simulation_run=False,
                        safety_pass=False,
                        economic_rejection_reason="STATIC_PRUNING_FEASIBILITY"
                    ))

            if not candidate_patches:
                telemetry.decision = "BACKBONE"
                telemetry.abstain_reason = "NO_FEASIBLE_CANDIDATE_PATCHES"
                telemetry.total_time_ms = (time.perf_counter() - t_start) * 1000.0
                self._record_step(econ_state, telemetry)
                return baseline_action

            # -----------------------------------------------------------------
            # 6. COUNTERFACTUAL SIMULATION & EVALUATION
            # -----------------------------------------------------------------
            t_sim0 = time.perf_counter()
            best_candidate: Optional[CoupledPatch] = None
            best_certificate: Optional[SafetyCertificate] = None
            best_eval_result = None
            quarantined_superior_patch: Optional[CoupledPatch] = None

            active_patches = candidate_patches[:self.config.max_simulations]

            for patch in active_patches:
                cand_action = patch.apply(baseline_action)

                # Macro-Regime Boundary Detection (Phase 016)
                probe_res = self.macro_detector.probe_candidate(
                    patch=patch,
                    baseline_action=baseline_action,
                    econ_state=econ_state,
                )

                horizon = select_adaptive_horizon(
                    patch,
                    econ_state,
                    self.config,
                    future_trajectory,
                    macro_probe_result=probe_res,
                )
                patch_continuation = future_trajectory[:max(0, horizon - 1)] if future_trajectory else None

                if probe_res.requires_escalation:
                    telemetry.macro_escalations_count += 1
                    reg_val = probe_res.regime_type.value
                    telemetry.macro_escalated_by_regime[reg_val] = (
                        telemetry.macro_escalated_by_regime.get(reg_val, 0) + 1
                    )

                # Run isolated forward simulation with frozen V3 continuation if escalated
                v3_callable = getattr(self.backbone, "_agent_fn", None)
                sim_outcome = self.simulator.evaluate(
                    candidate_patch=patch,
                    baseline_action=baseline_action,
                    econ_state=econ_state,
                    horizon=horizon,
                    continuation_trajectory=patch_continuation,
                    v3_agent_callable=v3_callable,
                    macro_escalated=probe_res.requires_escalation,
                    macro_escalation_reason=probe_res.reason if probe_res.requires_escalation else "",
                    macro_regime_type=probe_res.regime_type.value,
                )
                telemetry.simulations_run += 1
                telemetry.patches_simulated_count += 1

                # Strategic Evaluation (WinModel)
                eval_res = self.win_model.evaluate(
                    patch=patch,
                    outcome=sim_outcome,
                    econ_state=econ_state,
                    continuation_trajectory=patch_continuation,
                    baseline_action=baseline_action
                )

                # Hard Safety Verification
                t_saf0 = time.perf_counter()
                passed_safety, checks, abstain_reason = self.safety_checker.verify(
                    patch=patch,
                    outcome=sim_outcome,
                    econ_state=econ_state,
                    baseline_action=baseline_action,
                    future_trajectory=patch_continuation
                )
                telemetry.safety_time_ms += (time.perf_counter() - t_saf0) * 1000.0

                # Scientific Quarantine and Governance Gate (§2, §3)
                mech_fam = getattr(patch, "mechanism_family", "")
                reg_entry = MECHANISM_REGISTRY.get(mech_fam, {})
                is_quarantined = (
                    reg_entry.get("status") == ScientificStatus.QUARANTINED
                    or mech_fam == "LOCAL_WEED_DIG"
                ) and (mech_fam in self.config.quarantined_mechanisms or mech_fam not in self.config.enabled_mechanisms)
                candidate_otherwise_attractive = bool(passed_safety and eval_res.is_superior)

                if not passed_safety:
                    telemetry.patches_safety_rejected_count += 1
                elif is_quarantined and candidate_otherwise_attractive:
                    telemetry.patches_quarantined_count += 1
                    telemetry.quarantined_by_mechanism[mech_fam] = telemetry.quarantined_by_mechanism.get(mech_fam, 0) + 1
                    quarantined_superior_patch = patch
                elif not eval_res.is_superior:
                    telemetry.patches_economically_rejected_count += 1

                # Terminal Telemetry for emergency feed purchases (§21)
                term_telem = None
                if mech_fam == "EMERGENCY_FEED_PURCHASE":
                    from aec.terminal.obligations import FeedTerminalCausalAnalyzer
                    causal_analyzer = FeedTerminalCausalAnalyzer()
                    animals = getattr(econ_state.farm, "animals", [])
                    if not animals:
                        from aec.resource.feed_security import FeedSecurityEngine
                        animals = FeedSecurityEngine().extract_livestock(econ_state)
                    deficit_val = 1
                    if hasattr(patch, "dependency_info") and isinstance(patch.dependency_info, dict):
                        deficit_val = patch.dependency_info.get("deficit", 1)
                    _, p_cat, p_reason, p_details = causal_analyzer.assess_terminal_feed_purpose(
                        econ_state=econ_state,
                        animals=animals,
                        deficit=deficit_val,
                        baseline_trajectory=patch_continuation
                    )
                    term_telem = {
                        "candidate_id": patch.patch_id,
                        "current_step": econ_state.step,
                        "remaining_steps": econ_state.remaining_horizon,
                        "feed_deficit_horizon": patch.expected_horizon,
                        "purpose": p_details.get("purpose", p_cat.value),
                        "required_downstream_actions": ["FEED", "HARVEST", "DROP", "SELL"],
                        "required_cash_obligations": p_details.get("purchase_cost", 0.0),
                        "earliest_realizable_benefit": p_details.get("earliest_realizable_benefit"),
                        "latest_feasible_execution": p_details.get("latest_feasible_execution"),
                        "baseline_obligations_affected": list(patch.affected_obligations),
                        "terminal_purpose_status": p_cat.value,
                        "counterfactual_status": getattr(sim_outcome, "fidelity", "VERIFIED"),
                        "safety_status": "PASS" if passed_safety else "FAIL",
                        "abstain_commit_reason": abstain_reason if not passed_safety else ("COMMIT" if candidate_otherwise_attractive and not is_quarantined else "ABSTAIN"),
                    }

                # Record per-candidate telemetry (§14, Phase 016)
                cand_telem = CandidateTelemetry(
                    patch_id=patch.patch_id,
                    mechanism_family=patch.mechanism_family,
                    opportunity_detected=True,
                    patch_generated=True,
                    patch_pruned=False,
                    simulation_run=True,
                    simulation_horizon=horizon,
                    delta_money=eval_res.delta_money,
                    delta_margin=eval_res.delta_margin,
                    delta_route_cost=eval_res.delta_route_cost,
                    delta_dependency_completion=eval_res.delta_dependency_completion,
                    delta_opponent_pressure=eval_res.delta_opponent_pressure,
                    weed_asset_value=eval_res.weed_asset_value,
                    delta_money_realized=eval_res.delta_money_realized,
                    delta_margin_realized=eval_res.delta_margin_realized,
                    projected_asset_value=eval_res.projected_asset_value,
                    projection_status=eval_res.projection_status,
                    spatial_consistency_ok=eval_res.spatial_consistency_ok,
                    safety_pass=passed_safety,
                    safety_rejection_reason=(
                        "SCIENTIFIC_QUARANTINE" if (is_quarantined and candidate_otherwise_attractive)
                        else (abstain_reason if not passed_safety else None)
                    ),
                    economic_rejection_reason=eval_res.rationale if not eval_res.is_superior else None,
                    commit_decision=candidate_otherwise_attractive and not is_quarantined,
                    baseline_action=copy.deepcopy(baseline_action),
                    candidate_action=copy.deepcopy(cand_action),
                    terminal_telemetry=term_telem,
                    why_v3_did_not_do_this=getattr(patch, "dependency_info", {}).get("why_v3_did_not_do_this"),
                    candidate_quantity=int(getattr(patch, "dependency_info", {}).get("quantity", 0) or 0),
                    candidate_reason=getattr(patch, "dependency_info", {}).get("reason"),
                    macro_escalated=probe_res.requires_escalation,
                    macro_regime_type=probe_res.regime_type.value,
                    macro_escalation_reason=probe_res.reason if probe_res.requires_escalation else None,
                    first_divergence_turn=sim_outcome.first_divergence_turn,
                )
                telemetry.candidates.append(cand_telem)

                # Feedback exact outcome to asset-holding lifecycle deduplicator (§9, §40)
                fp_str = getattr(patch, "dependency_info", {}).get("structural_fingerprint")
                if fp_str and hasattr(self.opp_engine, "asset_holding_analyzer"):
                    self.opp_engine.asset_holding_analyzer.trigger.record_counterfactual_outcome(
                        fp_str, was_accepted=bool(candidate_otherwise_attractive and not is_quarantined)
                    )

                # Generate machine-readable SafetyCertificate (§15)
                cert = SafetyCertificate(
                    patch_id=patch.patch_id,
                    baseline_summary=f"step={step}, cash={sim_outcome.baseline_final_money:.1f}",
                    candidate_summary=f"step={step}, cash={sim_outcome.candidate_final_money:.1f}",
                    delta_our_money=sim_outcome.delta_our_money,
                    delta_opponent_money=sim_outcome.delta_opponent_money,
                    delta_terminal_margin=sim_outcome.delta_terminal_margin,
                    overflow_check=checks.get("overflow_ok", False),
                    obligation_check=checks.get("obligation_ok", False),
                    purchase_check=checks.get("purchase_ok", True),
                    intermediate_solvency_check=checks.get("obligation_ok", False),
                    terminal_feasibility_check=checks.get("terminal_feasible", False),
                    market_collision_check=checks.get("market_collision_ok", False),
                    spatial_consistency_check=checks.get("spatial_consistency_ok", True),
                    fidelity_check=checks.get("fidelity_ok", True),
                    counterfactual_fidelity=getattr(sim_outcome, "fidelity", "VERIFIED"),
                    commit_decision=candidate_otherwise_attractive and not is_quarantined and getattr(sim_outcome, "fidelity", "VERIFIED") != "FAILED",
                    abstain_reason=(
                        "SCIENTIFIC_QUARANTINE" if (is_quarantined and candidate_otherwise_attractive)
                        else (abstain_reason if not passed_safety else (
                            "UNVERIFIED_COUNTERFACTUAL_FIDELITY" if getattr(sim_outcome, "fidelity", "VERIFIED") == "FAILED"
                            else (None if eval_res.is_superior else "ECONOMICALLY_INFERIOR")
                        ))
                    ),
                    metadata=eval_res.to_dict()
                )
                self._certificates.append(cert)

                # Select best committed patch among authorized, non-quarantined mechanisms
                if cert.commit_decision:
                    if best_eval_result is None or eval_res.expected_p_win > best_eval_result.expected_p_win:
                        best_candidate = patch
                        best_certificate = cert
                        best_eval_result = eval_res

            telemetry.sim_time_ms = (time.perf_counter() - t_sim0) * 1000.0

            # -----------------------------------------------------------------
            # 7. COMMIT PATCH OR ABSTAIN -> BACKBONE (Layer 3 Final Defense Gate)
            # -----------------------------------------------------------------
            if best_candidate is not None and best_certificate is not None:
                # Assert mechanism is authorized under immutable config (§9)
                mech_fam = getattr(best_candidate, "mechanism_family", "")
                reg_entry = MECHANISM_REGISTRY.get(mech_fam, {})
                is_scientifically_quarantined = (
                    reg_entry.get("status") == ScientificStatus.QUARANTINED
                    or mech_fam == "LOCAL_WEED_DIG"
                ) and (mech_fam in self.config.quarantined_mechanisms or mech_fam not in self.config.enabled_mechanisms)
                if is_scientifically_quarantined:
                    # Fail Closed: Reject quarantined mechanism for scientific validation status
                    telemetry.decision = "ABSTAIN"
                    telemetry.abstain_reason = "SCIENTIFIC_QUARANTINE"
                    telemetry.committed_patch_id = None
                    telemetry.committed_mechanism = mech_fam
                    final_action = baseline_action
                    for c in telemetry.candidates:
                        if c.patch_id == best_candidate.patch_id:
                            c.commit_decision = False
                            c.safety_rejection_reason = "SCIENTIFIC_QUARANTINE"
                elif mech_fam not in self.config.enabled_mechanisms:
                    # Fail Closed: Reject unauthorized patch family
                    telemetry.decision = "ABSTAIN"
                    telemetry.abstain_reason = "MECHANISM_POLICY_VIOLATION"
                    telemetry.committed_patch_id = None
                    telemetry.committed_mechanism = None
                    final_action = baseline_action
                    for c in telemetry.candidates:
                        if c.patch_id == best_candidate.patch_id:
                            c.commit_decision = False
                            c.safety_rejection_reason = "MECHANISM_POLICY_VIOLATION"
                else:
                    telemetry.decision = "COMMIT"
                    telemetry.committed_patch_id = best_candidate.patch_id
                    telemetry.committed_mechanism = mech_fam
                    self._latest_committed_patch = best_candidate
                    if len(getattr(best_candidate, "actions", [])) > 1:
                        self._in_flight_patch = best_candidate
                        self._in_flight_start_step = step
                    else:
                        self._in_flight_patch = None
                    for c in telemetry.candidates:
                        c.commit_decision = (c.patch_id == best_candidate.patch_id)
                    # Apply certified patch to a fresh canonical copy of baseline action
                    final_action = best_candidate.apply(baseline_result.canonical_action_copy())
            else:
                self._in_flight_patch = None
                telemetry.decision = "ABSTAIN"
                if quarantined_superior_patch is not None:
                    telemetry.abstain_reason = "SCIENTIFIC_QUARANTINE"
                    telemetry.committed_mechanism = getattr(quarantined_superior_patch, "mechanism_family", "LOCAL_WEED_DIG")
                else:
                    telemetry.abstain_reason = "NO_CANDIDATE_CERTIFIED_SUPERIOR"
                    telemetry.committed_mechanism = None
                for c in telemetry.candidates:
                    c.commit_decision = False
                final_action = baseline_action
                self.fallback_policy.record_fallback(
                    step=step,
                    reason=FallbackReason.SCIENTIFIC_QUARANTINE if telemetry.abstain_reason == "SCIENTIFIC_QUARANTINE" else FallbackReason.ECONOMICALLY_INFERIOR,
                    baseline_action=baseline_action,
                    candidate_id=getattr(best_candidate, "patch_id", None),
                    mechanism_family=telemetry.committed_mechanism,
                    rationale=telemetry.abstain_reason or "ABSTAIN"
                )

            telemetry.total_time_ms = (time.perf_counter() - t_start) * 1000.0
            self._record_step(econ_state, telemetry)
            return final_action


        except Exception as e:
            # Top-Level Fail-Closed Boundary (§30): Fall back to baseline action
            self.fallback_policy.record_fallback(
                step=step,
                reason=FallbackReason.BACKBONE_INVOCATION_EXCEPTION,
                baseline_action=baseline_action,
                rationale=str(e)
            )
            telemetry.decision = "ABSTAIN_EXCEPTION"
            telemetry.abstain_reason = f"Unhandled AEC exception: {str(e)}"
            telemetry.total_time_ms = (time.perf_counter() - t_start) * 1000.0
            self._telemetry_history.append(telemetry)
            return baseline_action

    def _record_step(self, econ_state: EconomicState, telemetry: AECTelemetry) -> None:
        self._prev_econ_state = econ_state
        self._telemetry_history.append(telemetry)

    @property
    def latest_telemetry(self) -> Optional[AECTelemetry]:
        return self._telemetry_history[-1] if self._telemetry_history else None

    @property
    def latest_certificate(self) -> Optional[SafetyCertificate]:
        return self._certificates[-1] if self._certificates else None

    def get_all_certificates(self) -> List[SafetyCertificate]:
        return list(self._certificates)

    @property
    def latest_committed_patch(self) -> Optional[Any]:
        return self._latest_committed_patch
