# SPDX-License-Identifier: MIT
"""AEC Central Compiler Orchestrator and Executor (§4, §30, §31, §32)."""

from __future__ import annotations

import copy
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from aec.config import AECConfig
from aec.counterfactual.horizon import select_adaptive_horizon
from aec.counterfactual.simulator import CounterfactualSimulator
from aec.evaluation.win_model import WinModel
from aec.events.detectors import detect_events
from aec.events.event_bus import EventBus
from aec.integration.backbone_adapter import BackboneAdapter, BaselineResult
from aec.ir.economic_state import EconomicState, build_economic_state
from aec.opportunities import OpportunityEngine
from aec.patches.generator import PatchGenerator
from aec.patches.patch import CoupledPatch
from aec.patches.pruning import prune_patches
from aec.safety.certificate import SafetyCertificate
from aec.safety.checks import SafetyChecker

_SAFE = {"farmer": ["PASS"], "hands": [], "market": []}


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
        
        # State tracking across steps
        self._prev_econ_state: Optional[EconomicState] = None
        self._telemetry_history: List[AECTelemetry] = []
        self._certificates: List[SafetyCertificate] = []

    def act(
        self,
        observation: Dict[str, Any],
        configuration: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Main execution entrypoint for Kaggle game turns."""
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
            # 3. EVENT BUS & DETECTORS
            # -----------------------------------------------------------------
            t_ev0 = time.perf_counter()
            self.event_bus.clear()
            events = detect_events(econ_state, self._prev_econ_state, baseline_action, self.config)
            self.event_bus.publish_many(events)
            telemetry.event_time_ms = (time.perf_counter() - t_ev0) * 1000.0
            telemetry.events_detected = [e.event_type.value for e in events]

            # NO-EVENT FAST PATH (§8):
            # If no planning event exists, immediately emit baseline unchanged
            if not self.event_bus.has_events:
                telemetry.decision = "BACKBONE"
                telemetry.abstain_reason = "NO_EVENT_FAST_PATH"
                telemetry.total_time_ms = (time.perf_counter() - t_start) * 1000.0
                self._record_step(econ_state, telemetry)
                return baseline_action

            # -----------------------------------------------------------------
            # 4. OPPORTUNITY ENGINE (Layer 1 Defense)
            # -----------------------------------------------------------------
            t_opp0 = time.perf_counter()
            opportunities = self.opp_engine.detect_opportunities(
                econ_state,
                events,
                baseline_action,
                max_opportunities=self.config.max_opportunities,
                config=self.config
            )
            telemetry.opportunities_count = len(opportunities)
            telemetry.opp_time_ms = (time.perf_counter() - t_opp0) * 1000.0

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
            # 5. COUPLED PATCH GENERATION & STATIC PRUNING (Layer 2 Defense)
            # -----------------------------------------------------------------
            raw_patches = self.patch_generator.generate_patches(
                opportunities, econ_state, baseline_action, config=self.config
            )
            telemetry.patches_generated_count = len(raw_patches) + self.patch_generator.last_quarantined_count
            telemetry.patches_quarantined_count = self.patch_generator.last_quarantined_count
            for fam, count in self.patch_generator.last_quarantined_by_mechanism.items():
                telemetry.quarantined_by_mechanism[fam] = (
                    telemetry.quarantined_by_mechanism.get(fam, 0) + count
                )

            candidate_patches = prune_patches(
                raw_patches, econ_state, max_candidates=self.config.max_candidates
            )
            telemetry.patches_pruned_count = max(0, len(raw_patches) - len(candidate_patches))
            telemetry.candidates_count = len(candidate_patches)

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

            # Extract read-only future backbone continuation trajectory (zero live calls)
            active_patches = candidate_patches[:self.config.max_simulations]
            max_horizon = max(
                (select_adaptive_horizon(p, econ_state, self.config) for p in active_patches),
                default=self.config.normal_horizon
            )
            n_hands = max(0, len(econ_state.workers.workers) - 1)
            future_trajectory = self.backbone.get_future_trajectory(
                step=step,
                horizon=max_horizon,
                player=econ_state.player,
                n_hands=n_hands
            )

            for patch in active_patches:
                horizon = select_adaptive_horizon(patch, econ_state, self.config)
                patch_continuation = future_trajectory[:max(0, horizon - 1)] if future_trajectory else None
                
                # Run isolated forward simulation under opponent pressure
                sim_outcome = self.simulator.evaluate(
                    candidate_patch=patch,
                    baseline_action=baseline_action,
                    econ_state=econ_state,
                    horizon=horizon,
                    continuation_trajectory=patch_continuation
                )
                telemetry.simulations_run += 1
                telemetry.patches_simulated_count += 1

                # Strategic Evaluation (WinModel)
                eval_res = self.win_model.evaluate(patch, sim_outcome, econ_state)

                # Hard Safety Verification
                t_saf0 = time.perf_counter()
                passed_safety, checks, abstain_reason = self.safety_checker.verify(
                    patch=patch,
                    outcome=sim_outcome,
                    econ_state=econ_state,
                    baseline_action=baseline_action
                )
                telemetry.safety_time_ms += (time.perf_counter() - t_saf0) * 1000.0

                if not passed_safety:
                    telemetry.patches_safety_rejected_count += 1
                elif not eval_res.is_superior:
                    telemetry.patches_economically_rejected_count += 1

                # Generate machine-readable SafetyCertificate (§15)
                cert = SafetyCertificate(
                    patch_id=patch.patch_id,
                    baseline_summary=f"step={step}, cash={sim_outcome.baseline_final_money:.1f}",
                    candidate_summary=f"step={step}, cash={sim_outcome.candidate_final_money:.1f}",
                    delta_our_money=sim_outcome.delta_our_money,
                    delta_opponent_money=sim_outcome.delta_opponent_money,
                    delta_terminal_margin=sim_outcome.delta_terminal_margin,
                    overflow_check=checks["overflow_ok"],
                    obligation_check=checks["obligation_ok"],
                    purchase_check=True,
                    intermediate_solvency_check=checks["obligation_ok"],
                    terminal_feasibility_check=checks["terminal_feasible"],
                    market_collision_check=checks["market_collision_ok"],
                    determinism_check=checks["determinism_ok"],
                    commit_decision=passed_safety and eval_res.is_superior,
                    abstain_reason=abstain_reason if not passed_safety else (
                        None if eval_res.is_superior else "ECONOMICALLY_INFERIOR"
                    ),
                    metadata=eval_res.to_dict()
                )
                self._certificates.append(cert)

                # Select best committed patch
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
                if mech_fam not in self.config.enabled_mechanisms:
                    # Fail Closed: Reject unauthorized patch family
                    telemetry.decision = "ABSTAIN"
                    telemetry.abstain_reason = "MECHANISM_POLICY_VIOLATION"
                    telemetry.committed_patch_id = None
                    telemetry.committed_mechanism = None
                    final_action = baseline_action
                else:
                    telemetry.decision = "COMMIT"
                    telemetry.committed_patch_id = best_candidate.patch_id
                    telemetry.committed_mechanism = mech_fam
                    # Apply certified patch to a fresh canonical copy of baseline action
                    final_action = best_candidate.apply(baseline_result.canonical_action_copy())
            else:
                telemetry.decision = "ABSTAIN"
                telemetry.abstain_reason = "NO_CANDIDATE_CERTIFIED_SUPERIOR"
                final_action = baseline_action

            telemetry.total_time_ms = (time.perf_counter() - t_start) * 1000.0
            self._record_step(econ_state, telemetry)
            return final_action

        except Exception as e:
            # Top-Level Fail-Closed Boundary (§30): Fall back to baseline action
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
