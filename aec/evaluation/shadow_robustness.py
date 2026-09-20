# SPDX-License-Identifier: MIT
"""Phase 019: Shadow Robustness & Selection Regret Evaluation Engine (§11–§14).

Computes deterministic sensitivity, perturbation bounds, and selection regret
for committed candidate mechanisms without altering live decisions or game state.
"""

from __future__ import annotations

import copy
import statistics
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from aec.counterfactual.horizon import select_adaptive_horizon
from aec.counterfactual.macro_detector import MacroRegimeTransitionDetector
from aec.counterfactual.simulator import CounterfactualSimulator, SimulationOutcome
from aec.ir.economic_state import EconomicState
from aec.patches.patch import CoupledPatch


class RobustnessCategory(str, Enum):
    """Preregistered deterministic robustness categories (§14).

    IMPORTANT: Categories represent deterministic perturbation sensitivity,
    NOT probabilistic confidence or empirical win probability.
    """
    R0_ROBUST_POSITIVE = "R0_ROBUST_POSITIVE"        # Positive across all defined neighbors
    R1_SENSITIVE_POSITIVE = "R1_SENSITIVE_POSITIVE"    # Positive centrally, negative in >=1 neighbor
    R2_MARGINAL = "R2_MARGINAL"                      # Advantage small (<= $15.0 or safety margin <= $5.0)
    R3_RANKING_DEPENDENT = "R3_RANKING_DEPENDENT"    # Better alternative or foundation candidate available
    R4_MACRO_SENSITIVE = "R4_MACRO_SENSITIVE"        # Macro-escalated with negative continuation delta
    R5_CLEARLY_NEGATIVE = "R5_CLEARLY_NEGATIVE"      # Long-horizon delta <= 0.0


@dataclass
class RobustnessVector:
    """Deterministic diagnostic vector for candidate sensitivity (§13)."""
    local_delta: float = 0.0
    long_horizon_delta: float = 0.0
    terminal_delta: float = 0.0
    min_neighbor_delta: float = 0.0
    median_neighbor_delta: float = 0.0
    max_neighbor_delta: float = 0.0
    sign_stability: bool = True
    quantity_sensitivity: float = 0.0
    timing_sensitivity: float = 0.0
    macro_boundary_distance: int = 720
    safety_margin: float = 0.0
    foundation_relative_delta: Optional[float] = None
    runner_up_gap: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "local_delta": round(self.local_delta, 2),
            "long_horizon_delta": round(self.long_horizon_delta, 2),
            "terminal_delta": round(self.terminal_delta, 2),
            "min_neighbor_delta": round(self.min_neighbor_delta, 2),
            "median_neighbor_delta": round(self.median_neighbor_delta, 2),
            "max_neighbor_delta": round(self.max_neighbor_delta, 2),
            "sign_stability": self.sign_stability,
            "quantity_sensitivity": round(self.quantity_sensitivity, 2),
            "timing_sensitivity": round(self.timing_sensitivity, 2),
            "macro_boundary_distance": self.macro_boundary_distance,
            "safety_margin": round(self.safety_margin, 2),
            "foundation_relative_delta": round(self.foundation_relative_delta, 2) if self.foundation_relative_delta is not None else None,
            "runner_up_gap": round(self.runner_up_gap, 2) if self.runner_up_gap is not None else None,
        }


@dataclass
class ShadowAuditRecord:
    """Observable diagnostic record produced by shadow evaluation (§11)."""
    step: int
    committed_patch_id: str
    committed_mechanism: str
    committed_delta: float
    best_admissible_alt_id: Optional[str] = None
    best_admissible_alt_delta: Optional[float] = None
    selection_regret: float = 0.0
    abstention_regret: float = 0.0
    foundation_patch_id: Optional[str] = None
    foundation_delta: Optional[float] = None
    foundation_opportunity_cost: Optional[float] = None
    robustness_vector: Optional[RobustnessVector] = None
    robustness_category: RobustnessCategory = RobustnessCategory.R0_ROBUST_POSITIVE
    neighbor_deltas: Dict[str, float] = field(default_factory=dict)
    would_abstain: bool = False
    audit_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "committed_patch_id": self.committed_patch_id,
            "committed_mechanism": self.committed_mechanism,
            "committed_delta": round(self.committed_delta, 2),
            "best_admissible_alt_id": self.best_admissible_alt_id,
            "best_admissible_alt_delta": round(self.best_admissible_alt_delta, 2) if self.best_admissible_alt_delta is not None else None,
            "selection_regret": round(self.selection_regret, 2),
            "abstention_regret": round(self.abstention_regret, 2),
            "foundation_patch_id": self.foundation_patch_id,
            "foundation_delta": round(self.foundation_delta, 2) if self.foundation_delta is not None else None,
            "foundation_opportunity_cost": round(self.foundation_opportunity_cost, 2) if self.foundation_opportunity_cost is not None else None,
            "category": self.robustness_category.value,
            "vector": self.robustness_vector.to_dict() if self.robustness_vector else {},
            "neighbor_deltas": {k: round(v, 2) for k, v in self.neighbor_deltas.items()},
            "would_abstain": self.would_abstain,
            "notes": self.audit_notes,
        }


class ShadowRobustnessEvaluator:
    """Isolated shadow evaluation engine for candidate robustness and regret audit (§11).

    Executes side-by-side with live compilation without modifying live actions.
    """

    def __init__(
        self,
        simulator: CounterfactualSimulator,
        macro_detector: MacroRegimeTransitionDetector,
        v3_agent_callable: Optional[Callable] = None,
        config: Optional[Any] = None,
    ) -> None:
        self.simulator = simulator
        self.macro_detector = macro_detector
        self.v3_agent_callable = v3_agent_callable
        self.config = config

    def audit_commit(
        self,
        committed_patch: CoupledPatch,
        committed_outcome: SimulationOutcome,
        all_candidate_patches: List[CoupledPatch],
        simulated_outcomes: Dict[str, SimulationOutcome],
        baseline_action: Dict[str, Any],
        future_trajectory: Optional[List[Dict[str, Any]]],
        econ_state: EconomicState,
    ) -> ShadowAuditRecord:
        """Run diagnostic shadow evaluations around a committed candidate."""
        step = econ_state.step
        comm_id = committed_patch.patch_id
        comm_fam = getattr(committed_patch, "mechanism_family", "")
        comm_delta = committed_outcome.delta_terminal_margin

        # 1. Selection Regret: compare against best simulated alternative
        best_alt_id = None
        best_alt_delta = None
        for p in all_candidate_patches:
            if p.patch_id == comm_id:
                continue
            outcome = simulated_outcomes.get(p.patch_id)
            if outcome is not None:
                if best_alt_delta is None or outcome.delta_terminal_margin > best_alt_delta:
                    best_alt_delta = outcome.delta_terminal_margin
                    best_alt_id = p.patch_id

        selection_regret = max(0.0, (best_alt_delta - comm_delta)) if best_alt_delta is not None else 0.0

        # 2. Abstention Regret: Δ_baseline - Δ_committed = 0.0 - Δ_committed
        # If candidate delta is negative, not acting would have yielded +|comm_delta|
        abstention_regret = max(0.0, -comm_delta)

        # 3. Foundation Opportunity Cost: compare against foundation candidates
        foundation_id = None
        foundation_delta = None
        for p in all_candidate_patches:
            fam = getattr(p, "mechanism_family", "")
            if fam in ("DEPENDENCY_AWARE_MARKET_TIMING", "TERMINAL_LIQUIDATION", "PHASE_SHUTDOWN"):
                outcome = simulated_outcomes.get(p.patch_id)
                if outcome is None:
                    # Simulate foundation candidate in shadow mode if not already done
                    outcome = self._simulate_shadow_patch(p, baseline_action, future_trajectory, econ_state)
                if outcome is not None:
                    if foundation_delta is None or outcome.delta_terminal_margin > foundation_delta:
                        foundation_delta = outcome.delta_terminal_margin
                        foundation_id = p.patch_id

        fnd_opp_cost = (foundation_delta - comm_delta) if foundation_delta is not None else None

        # 4. Candidate Perturbation Set (§12)
        neighbor_deltas: Dict[str, float] = {}
        if comm_fam == "AUTONOMOUS_TRANCHE_ORDER_SYNTHESIZER":
            neighbor_deltas = self._evaluate_tranche_perturbations(
                committed_patch, baseline_action, future_trajectory, econ_state
            )

        # Include central delta in neighbor analysis
        all_neighbor_vals = [comm_delta] + list(neighbor_deltas.values())
        min_neighbor = min(all_neighbor_vals)
        max_neighbor = max(all_neighbor_vals)
        median_neighbor = float(statistics.median(all_neighbor_vals))
        sign_stability = bool(min_neighbor > 0.0)

        # Quantity sensitivity: (Δ(q+1) - Δ(q-1)) / 2 if both present
        q_sens = 0.0
        q_plus = neighbor_deltas.get("q+1")
        q_minus = neighbor_deltas.get("q-1")
        if q_plus is not None and q_minus is not None:
            q_sens = abs(q_plus - q_minus) / 2.0
        elif q_plus is not None:
            q_sens = abs(q_plus - comm_delta)
        elif q_minus is not None:
            q_sens = abs(comm_delta - q_minus)

        # Timing sensitivity: spread across t, t+1, t+2
        timing_vals = [comm_delta]
        if "t+1" in neighbor_deltas:
            timing_vals.append(neighbor_deltas["t+1"])
        if "t+2" in neighbor_deltas:
            timing_vals.append(neighbor_deltas["t+2"])
        t_sens = (max(timing_vals) - min(timing_vals)) if len(timing_vals) > 1 else 0.0

        # Safety margin above $15 hurdle
        safety_margin = comm_delta - 15.0

        # Distance to macro boundary (turns until end of day or macro event)
        turns_in_day = step % 40
        macro_dist = 40 - turns_in_day

        runner_up_gap = (comm_delta - best_alt_delta) if best_alt_delta is not None else None
        fnd_rel_delta = (comm_delta - foundation_delta) if foundation_delta is not None else None

        vec = RobustnessVector(
            local_delta=committed_outcome.direct_intervention_effect,
            long_horizon_delta=comm_delta,
            terminal_delta=comm_delta,
            min_neighbor_delta=min_neighbor,
            median_neighbor_delta=median_neighbor,
            max_neighbor_delta=max_neighbor,
            sign_stability=sign_stability,
            quantity_sensitivity=q_sens,
            timing_sensitivity=t_sens,
            macro_boundary_distance=macro_dist,
            safety_margin=safety_margin,
            foundation_relative_delta=fnd_rel_delta,
            runner_up_gap=runner_up_gap,
        )

        # 5. Deterministic Robustness Category Assignment (§14)
        cat, would_abstain, note = self._categorize_candidate(
            comm_delta=comm_delta,
            vec=vec,
            neighbor_deltas=neighbor_deltas,
            committed_outcome=committed_outcome,
            fnd_opp_cost=fnd_opp_cost,
            selection_regret=selection_regret,
        )

        return ShadowAuditRecord(
            step=step,
            committed_patch_id=comm_id,
            committed_mechanism=comm_fam,
            committed_delta=comm_delta,
            best_admissible_alt_id=best_alt_id,
            best_admissible_alt_delta=best_alt_delta,
            selection_regret=selection_regret,
            abstention_regret=abstention_regret,
            foundation_patch_id=foundation_id,
            foundation_delta=foundation_delta,
            foundation_opportunity_cost=fnd_opp_cost,
            robustness_vector=vec,
            robustness_category=cat,
            neighbor_deltas=neighbor_deltas,
            would_abstain=would_abstain,
            audit_notes=note,
        )

    def _evaluate_tranche_perturbations(
        self,
        patch: CoupledPatch,
        baseline_action: Dict[str, Any],
        future_trajectory: Optional[List[Dict[str, Any]]],
        econ_state: EconomicState,
    ) -> Dict[str, float]:
        """Evaluate legal quantity and timing perturbations of a tranche order (§12)."""
        deltas: Dict[str, float] = {}
        orders = patch.market_mutations or []
        if not orders:
            return deltas

        first_order = orders[0]
        side, commodity, q = first_order[0], first_order[1], int(first_order[2])

        # Current shed inventory of commodity
        current_inv = getattr(econ_state.farm, "shed_inventory", {}).get(commodity, 0)

        # Quantity perturbation: q - 1
        if q > 1:
            p_minus = copy.deepcopy(patch)
            p_minus.patch_id = f"{patch.patch_id}_pert_qm1"
            p_minus.market_mutations = [(side, commodity, q - 1)]
            out_m = self._simulate_shadow_patch(p_minus, baseline_action, future_trajectory, econ_state)
            if out_m is not None:
                deltas["q-1"] = out_m.delta_terminal_margin

        # Quantity perturbation: q + 1
        if q < current_inv:
            p_plus = copy.deepcopy(patch)
            p_plus.patch_id = f"{patch.patch_id}_pert_qp1"
            p_plus.market_mutations = [(side, commodity, q + 1)]
            out_p = self._simulate_shadow_patch(p_plus, baseline_action, future_trajectory, econ_state)
            if out_p is not None:
                deltas["q+1"] = out_p.delta_terminal_margin

        # Timing perturbation: t+1 (delay sale by 1 turn)
        # Apply baseline_action at step 0, and inject the order into continuation step 1
        if future_trajectory and len(future_trajectory) > 1:
            p_delayed = copy.deepcopy(patch)
            p_delayed.patch_id = f"{patch.patch_id}_pert_tp1"
            p_delayed.market_mutations = []  # No market order at step 0
            delayed_cont = copy.deepcopy(future_trajectory)
            step1_market = list(delayed_cont[0].get("market", []))
            step1_market.append((side, commodity, q))
            delayed_cont[0]["market"] = step1_market

            out_t1 = self._simulate_shadow_patch(
                p_delayed, baseline_action, delayed_cont, econ_state
            )
            if out_t1 is not None:
                deltas["t+1"] = out_t1.delta_terminal_margin

        return deltas

    def _simulate_shadow_patch(
        self,
        patch: CoupledPatch,
        baseline_action: Dict[str, Any],
        future_trajectory: Optional[List[Dict[str, Any]]],
        econ_state: EconomicState,
    ) -> Optional[SimulationOutcome]:
        """Perform an isolated shadow simulation."""
        try:
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

            sim_outcome = self.simulator.evaluate(
                candidate_patch=patch,
                baseline_action=baseline_action,
                econ_state=econ_state,
                horizon=horizon,
                continuation_trajectory=patch_continuation,
                v3_agent_callable=self.v3_agent_callable,
                macro_escalated=probe_res.requires_escalation,
                macro_escalation_reason=probe_res.reason if probe_res.requires_escalation else "",
                macro_regime_type=probe_res.regime_type.value,
            )
            return sim_outcome
        except Exception:
            return None

    def _categorize_candidate(
        self,
        comm_delta: float,
        vec: RobustnessVector,
        neighbor_deltas: Dict[str, float],
        committed_outcome: SimulationOutcome,
        fnd_opp_cost: Optional[float],
        selection_regret: float,
    ) -> Tuple[RobustnessCategory, bool, str]:
        """Classify candidate into deterministic robustness categories (§14)."""
        # R5: Clearly negative
        if comm_delta <= 0.0:
            return (
                RobustnessCategory.R5_CLEARLY_NEGATIVE,
                True,
                f"Candidate delta non-positive (${comm_delta:.1f})",
            )

        # R3: Ranking-dependent (available alternative or foundation strictly better)
        if fnd_opp_cost is not None and fnd_opp_cost > 5.0:
            return (
                RobustnessCategory.R3_RANKING_DEPENDENT,
                True,
                f"Foundation candidate superior by +${fnd_opp_cost:.1f}",
            )
        if selection_regret > 15.0:
            return (
                RobustnessCategory.R3_RANKING_DEPENDENT,
                True,
                f"Alternative candidate superior by +${selection_regret:.1f}",
            )

        # R4: Macro-sensitive (macro escalated with continuation loss)
        if committed_outcome.macro_escalated and committed_outcome.macro_induced_continuation_delta < -50.0:
            return (
                RobustnessCategory.R4_MACRO_SENSITIVE,
                True,
                f"Macro continuation delta deeply negative (${committed_outcome.macro_induced_continuation_delta:.1f})",
            )

        # R1: Positive centrally but sensitive (at least one legal neighbor non-positive)
        if not vec.sign_stability or vec.min_neighbor_delta <= 0.0:
            return (
                RobustnessCategory.R1_SENSITIVE_POSITIVE,
                True,
                f"Fragile neighbor: min neighbor delta ${vec.min_neighbor_delta:.1f} <= $0",
            )

        # R2: Marginal (barely clearing $15 hurdle or thin safety margin)
        if comm_delta <= 15.0 or vec.safety_margin <= 5.0:
            return (
                RobustnessCategory.R2_MARGINAL,
                False,
                f"Marginal advantage (delta ${comm_delta:.1f}, safety margin ${vec.safety_margin:.1f})",
            )

        # R0: Robustly positive
        return (
            RobustnessCategory.R0_ROBUST_POSITIVE,
            False,
            f"Robust across perturbations (min neighbor ${vec.min_neighbor_delta:.1f} > $0)",
        )
