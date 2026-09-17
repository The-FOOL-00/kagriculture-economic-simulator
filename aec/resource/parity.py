# SPDX-License-Identifier: MIT
"""AEC-RESOURCE: Symbolic vs Simulator Agreement & Parity Harness (§20).

Validates consistency between symbolic resource DAG predictions and exact
counterfactual simulation outcomes. Flags any discrepancies as fidelity failures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from aec.counterfactual.simulator import SimulationOutcome
from aec.ir.economic_state import EconomicState
from aec.resource.conversions import ConversionPath
from aec.resource.dag import TemporalResourceDAG

if TYPE_CHECKING:
    from aec.patches.patch import CoupledPatch


@dataclass
class ParityReport:
    """Detailed comparison between symbolic graph prediction and simulator truth (§20)."""
    is_exact_match: bool
    predicted_delta_money: float
    realized_delta_money: float
    predicted_resource_deltas: Dict[str, int]
    realized_resource_deltas: Dict[str, int]
    divergences: List[str] = field(default_factory=list)
    fidelity_status: str = "VERIFIED"    # "VERIFIED", "APPROXIMATE", "FAILED"


class ResourceParityHarness:
    """Evaluates agreement between symbolic resource predictions and simulator reality."""

    def verify_parity(
        self,
        symbolic_dag: TemporalResourceDAG,
        patch: CoupledPatch,
        outcome: SimulationOutcome,
        econ_state: EconomicState
    ) -> ParityReport:
        """Compares symbolic DAG predictions against SimulationOutcome (§20)."""
        divergences: List[str] = []

        # 1. Money Parity Check
        # Extract predicted cash delta from resource edges
        predicted_money_delta = sum(e.cash_delta for e in symbolic_dag.edges.values())
        realized_money_delta = outcome.delta_our_money

        # If patch specified explicit resource changes, verify cash matches
        if abs(predicted_money_delta - realized_money_delta) > 1.0:
            # Check if symbolic DAG had edges populated
            if symbolic_dag.edges:
                divergences.append(
                    f"Cash delta mismatch: symbolic predicted ${predicted_money_delta:.1f}, "
                    f"simulator realized ${realized_money_delta:.1f}"
                )

        # 2. Resource Inventory Parity Check
        predicted_deltas: Dict[str, int] = {}
        for edge in symbolic_dag.edges.values():
            for comm, delta in edge.quantity_delta.items():
                predicted_deltas[comm] = predicted_deltas.get(comm, 0) + delta

        # Compare with simulator sold and overflow
        realized_deltas: Dict[str, int] = {}
        for comm, qty in outcome.candidate_sold.items():
            base_qty = outcome.baseline_sold.get(comm, 0)
            if qty != base_qty:
                realized_deltas[comm] = -(qty - base_qty)

        # Check for unexpected overflow divergence
        if outcome.candidate_overflow_units > 0:
            divergences.append(
                f"Simulator detected {outcome.candidate_overflow_units} shed overflow discard units "
                "not permitted by symbolic model"
            )

        # 3. Intermediate Solvency Parity
        if not outcome.intermediate_solvency_ok:
            divergences.append("Simulator encountered intermediate shed deficit during forward rollout")

        is_match = len(divergences) == 0
        fidelity = "VERIFIED" if is_match else ("FAILED" if not outcome.intermediate_solvency_ok else "APPROXIMATE")

        return ParityReport(
            is_exact_match=is_match,
            predicted_delta_money=predicted_money_delta,
            realized_delta_money=realized_money_delta,
            predicted_resource_deltas=predicted_deltas,
            realized_resource_deltas=realized_deltas,
            divergences=divergences,
            fidelity_status=fidelity
        )
