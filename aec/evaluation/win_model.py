# SPDX-License-Identifier: MIT
"""Lexicographic Win and Margin Evaluation Model (§9, §14, §23, V1.1).

Exposes explicit diagnostic terms (money, margin, route cost, dependency completion,
opponent pressure, weed asset value) and treats win probability strictly as an
uncalibrated development ranking heuristic rather than empirical probability.
Clearly separates realized counterfactual values from projected downstream values.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from aec.counterfactual.simulator import SimulationOutcome
from aec.evaluation.asset_value import DownstreamAssetEvaluator, WeedValuation
from aec.ir.economic_state import EconomicState
from aec.patches.patch import CoupledPatch


class LeadState(str, Enum):
    """Extension point for lead-aware endgame control (§28)."""
    AHEAD = "AHEAD"     # Net margin > +$1,000
    CLOSE = "CLOSE"     # Net margin in [-$1,000, +$1,000]
    BEHIND = "BEHIND"   # Net margin < -$1,000


@dataclass
class EvaluationResult:
    """Strategic evaluation output for a candidate patch with explicit diagnostic terms (§9)."""
    patch_id: str
    expected_p_win: float             # Note: Uncalibrated heuristic proxy for ranking
    terminal_margin_delta: float
    our_money_delta: float
    opponent_money_delta: float
    lead_state: LeadState
    temporary_sacrifice_accepted: bool
    is_superior: bool
    rationale: str

    # Explicit diagnostic components (§9, §14)
    delta_money: float = 0.0
    delta_margin: float = 0.0
    delta_route_cost: float = 0.0
    delta_dependency_completion: float = 0.0
    delta_opportunity_preservation: float = 0.0
    delta_opponent_pressure: float = 0.0
    weed_asset_value: float = 0.0
    weed_valuation: Optional[WeedValuation] = None

    # Realized vs Projected Value Separation (§5)
    delta_money_realized: float = 0.0
    delta_margin_realized: float = 0.0
    projected_asset_value: float = 0.0
    projected_asset_value_basis: str = ""
    projection_status: str = "REALIZED"
    spatial_consistency_ok: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "patch_id": self.patch_id,
            "p_win_heuristic": round(self.expected_p_win, 4),
            "margin_delta": round(self.terminal_margin_delta, 2),
            "our_money_delta": round(self.our_money_delta, 2),
            "opp_money_delta": round(self.opponent_money_delta, 2),
            "lead_state": self.lead_state.value,
            "sacrifice_accepted": self.temporary_sacrifice_accepted,
            "is_superior": self.is_superior,
            "rationale": self.rationale,
            "spatial_consistency_ok": self.spatial_consistency_ok,
            "realized": {
                "delta_money_realized": round(self.delta_money_realized, 2),
                "delta_margin_realized": round(self.delta_margin_realized, 2),
            },
            "projected": {
                "projected_asset_value": round(self.projected_asset_value, 2),
                "projected_asset_value_basis": self.projected_asset_value_basis,
                "projection_status": self.projection_status,
            },
            "diagnostics": {
                "delta_money": round(self.delta_money, 2),
                "delta_margin": round(self.delta_margin, 2),
                "delta_route_cost": round(self.delta_route_cost, 2),
                "delta_dependency_completion": self.delta_dependency_completion,
                "delta_opportunity_preservation": self.delta_opportunity_preservation,
                "delta_opponent_pressure": round(self.delta_opponent_pressure, 2),
                "weed_asset_value": round(self.weed_asset_value, 2),
            }
        }


class WinModel:
    """Evaluates candidate simulations under the AEC lexicographic hierarchy.

    IMPORTANT DEVELOPMENT GOVERNANCE:
    - estimate_p_win() produces an uncalibrated sigmoid-shaped strategic score
      used purely as a tie-breaking sort key among certified candidates.
    - It is NOT calibrated probability and MUST NOT be described as empirical P(WIN).
    """

    def __init__(self) -> None:
        self.asset_evaluator = DownstreamAssetEvaluator()

    @staticmethod
    def get_lead_state(our_cash: float, opp_cash: float) -> LeadState:
        gap = our_cash - opp_cash
        if gap > 1000.0:
            return LeadState.AHEAD
        elif gap < -1000.0:
            return LeadState.BEHIND
        else:
            return LeadState.CLOSE

    def estimate_p_win(self, current_gap: float, margin_delta: float) -> float:
        """Uncalibrated logistic strategic score given projected margin."""
        projected_margin = current_gap + margin_delta
        scale = 1000.0
        return 1.0 / (1.0 + math.exp(-projected_margin / scale))

    def evaluate(
        self,
        patch: CoupledPatch,
        outcome: SimulationOutcome,
        econ_state: EconomicState,
        continuation_trajectory: Optional[List[Dict[str, Any]]] = None,
        baseline_action: Optional[Dict[str, Any]] = None
    ) -> EvaluationResult:
        current_gap = econ_state.farm.cash - econ_state.opponent.observed_cash
        lead_state = self.get_lead_state(econ_state.farm.cash, econ_state.opponent.observed_cash)

        base_p_win = self.estimate_p_win(current_gap, 0.0)
        cand_p_win = self.estimate_p_win(current_gap, outcome.delta_terminal_margin)

        # Baseline diagnostics
        delta_money = outcome.delta_our_money
        delta_margin = outcome.delta_terminal_margin
        delta_opp_money = outcome.delta_opponent_money
        delta_opp_pressure = max(0.0, -outcome.delta_opponent_money)
        delta_route_cost = 0.0
        delta_dependency_completion = 0.0
        delta_opp_preservation = 0.0
        weed_asset_val = 0.0
        weed_val: Optional[WeedValuation] = None

        fam = getattr(patch, "mechanism_family", "")
        patch_id = patch.source_opportunity_id or patch.patch_id

        # ---------------------------------------------------------------------
        # Spatial Consistency Check (§7, §8)
        # ---------------------------------------------------------------------
        if not getattr(outcome, "spatial_consistency_ok", True):
            reason = getattr(outcome, "desynchronization_reason", "diverged worker position")
            return EvaluationResult(
                patch_id=patch.patch_id,
                expected_p_win=cand_p_win,
                terminal_margin_delta=delta_margin,
                our_money_delta=delta_money,
                opponent_money_delta=delta_opp_money,
                lead_state=lead_state,
                temporary_sacrifice_accepted=False,
                is_superior=False,
                rationale=f"Continuation spatial desynchronization: {reason}",
                delta_money=delta_money,
                delta_margin=delta_margin,
                delta_money_realized=delta_money,
                delta_margin_realized=delta_margin,
                projected_asset_value=0.0,
                projected_asset_value_basis="",
                projection_status="SPATIAL_DESYNCHRONIZED",
                spatial_consistency_ok=False,
            )

        # ---------------------------------------------------------------------
        # Mechanism-Specific Economic Valuation
        # ---------------------------------------------------------------------
        is_superior = False
        rationale = ""
        temp_sacrifice = False

        if fam == "LOCAL_WEED_DIG" or "WEED_DIG" in patch_id:
            worker_id = 0
            if patch.worker_mutations:
                worker_id = next(iter(patch.worker_mutations.keys()))
            worker = econ_state.workers.get_worker(worker_id)
            pos = worker.position if worker else (0, 0)

            base_worker_cmd = None
            if baseline_action:
                if worker_id == 0:
                    base_worker_cmd = baseline_action.get("farmer", ["PASS"])
                else:
                    h = baseline_action.get("hands", []) or []
                    if worker_id - 1 < len(h):
                        base_worker_cmd = h[worker_id - 1]

            weed_val = self.asset_evaluator.evaluate_weed_removal(
                tile=pos,
                worker_id=worker_id,
                econ_state=econ_state,
                continuation_actions=continuation_trajectory,
                baseline_worker_action=base_worker_cmd,
            )
            weed_asset_val = weed_val.net_projected_asset_value
            delta_dependency_completion = weed_val.delta_dependency_completion
            delta_route_cost = weed_val.delta_route_cost
            if weed_val.has_downstream_dependency:
                delta_opp_preservation = 1.0

            # A weed dig is certified superior iff measurable downstream benefit exceeds labor cost
            # and terminal margin does not regress beyond the initial action cost allowance
            if weed_val.projection_status.startswith("INFEASIBLE"):
                is_superior = False
                rationale = f"Weed dig infeasible: {weed_val.projection_status} ({weed_val.rationale})"
            elif weed_val.projection_status == "NO_DEPENDENCY" and weed_val.delta_route_cost <= 0.0:
                is_superior = False
                rationale = (
                    f"Insufficient weed removal benefit (net asset value ${weed_asset_val:.2f}, "
                    f"margin delta ${delta_margin:.1f})"
                )
            elif weed_asset_val > 0.0 and delta_margin >= -(weed_val.action_opportunity_cost + 5.0):
                is_superior = True
                temp_sacrifice = outcome.delta_our_money < 0.0
                rationale = (
                    f"Certified downstream weed clearance value +${weed_asset_val:.2f} "
                    f"({weed_val.rationale})"
                )
            else:
                is_superior = False
                rationale = (
                    f"Insufficient weed removal benefit (net asset value ${weed_asset_val:.2f}, "
                    f"margin delta ${delta_margin:.1f})"
                )

        elif fam in ("DEPENDENCY_AWARE_MARKET_TIMING", "FRONTLOAD_ORDERS") or "MARKET_TIMING" in patch_id or "FRONTLOAD" in patch_id:
            # Market timing is superior if it increases cash/margin under exact sequential pricing
            if delta_margin > 0.0 or delta_money > 0.0:
                is_superior = True
                rationale = f"Dependency-aware market timing yields positive delta: margin +${delta_margin:.1f}, cash +${delta_money:.1f}"
            else:
                is_superior = False
                rationale = f"Market timing produces non-positive monetary outcome: margin delta ${delta_margin:.1f}, cash delta ${delta_money:.1f}"

        elif fam == "TERMINAL_LIQUIDATION" or "TERMINAL_LIQUIDATE" in patch_id:
            if delta_money > 0.0 or delta_margin > 0.0:
                is_superior = True
                rationale = f"Terminal liquidation recovered +${delta_money:.1f} in unliquidated inventory"
            else:
                is_superior = False
                rationale = "Terminal inventory already fully liquidated; no delta"

        elif fam == "PHASE_SHUTDOWN" or "SHUTDOWN" in patch_id:
            if delta_money > 0.0 or delta_margin >= 0.0:
                is_superior = True
                rationale = f"Phase shutdown preserved +${delta_money:.1f} in avoided dead-crop seed expenditure"
            else:
                is_superior = False
                rationale = "No dead-crop seed expenditure detected in baseline"

        elif fam == "TERMINAL_HARVEST_SWEEP" or "TERMINAL_SWEEP" in patch_id:
            if delta_margin > 0.0 or (delta_money > 0.0 and delta_margin >= 0.0):
                is_superior = True
                rationale = f"Certified terminal sweep increases realizable terminal return: margin +${delta_margin:.1f}, cash +${delta_money:.1f}"
            else:
                is_superior = False
                rationale = f"Terminal sweep produces non-positive economic return: margin delta ${delta_margin:.1f}, cash delta ${delta_money:.1f}"

        elif fam == "ROUTE_COMPRESSION" or "RCOMP" in patch_id:
            if delta_margin > 0.0 or (delta_money > 0.0 and delta_margin >= 0.0):
                is_superior = True
                rationale = f"Certified route compression yields positive economic return: margin +${delta_margin:.1f}, cash +${delta_money:.1f}"
            else:
                is_superior = False
                rationale = f"Route compression produces non-positive economic return: margin delta ${delta_margin:.1f}, cash delta ${delta_money:.1f}"

        elif fam == "DYNAMIC_SHADOW_HARVEST" or "HARVEST" in patch_id:
            if delta_margin > 0.0 and delta_money >= 0.0:
                is_superior = True
                rationale = f"Certified dynamic harvest trajectory yields positive margin: margin +${delta_margin:.1f}, cash +${delta_money:.1f}"
            else:
                is_superior = False
                rationale = f"Dynamic harvest produces non-positive economic margin: delta margin ${delta_margin:.1f}, delta cash ${delta_money:.1f}"

        else:
            # Standard Lexicographic Hierarchy
            p_win_gain = cand_p_win - base_p_win
            temp_sacrifice = outcome.delta_our_money < 0.0 and outcome.delta_terminal_margin > 0.0

            if p_win_gain > 0.005:
                is_superior = True
                rationale = f"Improves heuristic score by +{p_win_gain*100:.2f}% (margin delta +${outcome.delta_terminal_margin:.1f})"
            elif outcome.delta_terminal_margin > 15.0:
                is_superior = True
                rationale = f"Positive margin delta: +${outcome.delta_terminal_margin:.1f}"
            elif outcome.delta_our_money > 20.0 and outcome.delta_terminal_margin >= 0.0:
                is_superior = True
                rationale = f"Net money gain +${outcome.delta_our_money:.1f} with non-negative margin delta"
            else:
                is_superior = False
                rationale = f"Insufficient strategic advantage (margin delta ${outcome.delta_terminal_margin:.1f}, money delta ${outcome.delta_our_money:.1f})"

        return EvaluationResult(
            patch_id=patch.patch_id,
            expected_p_win=cand_p_win,
            terminal_margin_delta=delta_margin,
            our_money_delta=delta_money,
            opponent_money_delta=delta_opp_money,
            lead_state=lead_state,
            temporary_sacrifice_accepted=temp_sacrifice,
            is_superior=is_superior,
            rationale=rationale,
            delta_money=delta_money,
            delta_margin=delta_margin,
            delta_route_cost=delta_route_cost,
            delta_dependency_completion=delta_dependency_completion,
            delta_opportunity_preservation=delta_opp_preservation,
            delta_opponent_pressure=delta_opp_pressure,
            weed_asset_value=weed_asset_val,
            weed_valuation=weed_val,
            delta_money_realized=delta_money,
            delta_margin_realized=delta_margin,
            projected_asset_value=weed_asset_val if weed_val else 0.0,
            projected_asset_value_basis=weed_val.projected_asset_value_basis if weed_val else "REALIZED_SIMULATION",
            projection_status=weed_val.projection_status if weed_val else "REALIZED",
            spatial_consistency_ok=getattr(outcome, "spatial_consistency_ok", True),
        )
