# SPDX-License-Identifier: MIT
"""Safety Invariant Verification Predicates (§14, §15, §26, Correction 0.2)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from aec.config import BOARD_SIZE, MAX_MARKET_ORDERS, MOVES, SHED_CAPACITY
from aec.counterfactual.simulator import SimulationOutcome
from aec.ir.economic_state import EconomicState
from aec.patches.patch import CoupledPatch


class SafetyChecker:
    """Verifies non-negotiable hard safety constraints before candidate admission."""

    def verify(
        self,
        patch: CoupledPatch,
        outcome: SimulationOutcome,
        econ_state: EconomicState,
        baseline_action: Dict[str, Any],
        future_trajectory: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[bool, Dict[str, bool], Optional[str]]:
        """Run complete hard safety check battery.
        
        Returns: (all_passed, check_dict, abstain_reason)
        """
        checks = {
            "legality_ok": True,
            "feasibility_ok": True,
            "overflow_ok": True,
            "obligation_ok": True,
            "solvency_ok": True,
            "terminal_feasible": True,
            "market_collision_ok": True,
            "determinism_ok": True,
            "spatial_consistency_ok": True,
            "fidelity_ok": True,
            "spatial_validity_ok": True,
            "timing_validity_ok": True,
            "route_continuity_ok": True,
            "worker_consistency_ok": True,
            "resource_consistency_ok": True,
            "obligation_consistency_ok": True,
            "market_consistency_ok": True,
            # Resource & Feed Security Invariants (§17, §18)
            "resource_conservation_ok": True,
            "negative_inventory_ok": True,
            "conversion_precondition_ok": True,
            "feed_security_ok": True,
            "capacity_consistency_ok": True,
            "cash_liquidity_ok": True,
            "temporal_availability_ok": True,
            "reservation_consistency_ok": True,
            "terminal_resource_ok": True,
            "terminal_purpose_ok": True,
        }

        # 0. Route Reconnection result verification (§15)
        reconnect_res = getattr(patch, "reconnect_result", None)
        if reconnect_res is not None:
            if not getattr(reconnect_res, "safety", True):
                checks["route_continuity_ok"] = False
                checks["spatial_validity_ok"] = False
                reason = getattr(reconnect_res, "rejection_reason", "Trajectory reconnection safety failure")
                return False, checks, f"Route reconnection failed safety audit: {reason}"

        # 1. Legality check
        if patch.market_mutations is not None:
            if len(patch.market_mutations) > MAX_MARKET_ORDERS:
                checks["legality_ok"] = False
                checks["market_consistency_ok"] = False
                return False, checks, f"Market order count {len(patch.market_mutations)} exceeds max {MAX_MARKET_ORDERS}"
            for order in patch.market_mutations:
                if not isinstance(order, (list, tuple)) or not order:
                    checks["legality_ok"] = False
                    checks["market_consistency_ok"] = False
                    return False, checks, "Malformed market order"
                if order[0] not in ("SELL", "BUY_PRODUCT", "BUY_SEED", "BUY_ANIMAL", "HIRE", "BUY_LAND"):
                    checks["legality_ok"] = False
                    checks["market_consistency_ok"] = False
                    return False, checks, f"Illegal market op {order[0]}"

        # 2. Feasibility of worker movements
        for worker_id, cmd in patch.worker_mutations.items():
            worker = econ_state.workers.get_worker(worker_id)
            if worker is None:
                checks["feasibility_ok"] = False
                checks["worker_consistency_ok"] = False
                return False, checks, f"Non-existent worker_id {worker_id}"
            if cmd and cmd[0] in MOVES:
                dx, dy = MOVES[cmd[0]]
                x, y = worker.position
                if not (0 <= x + dx < BOARD_SIZE and 0 <= y + dy < BOARD_SIZE):
                    checks["feasibility_ok"] = False
                    checks["spatial_validity_ok"] = False
                    checks["worker_consistency_ok"] = False
                    return False, checks, f"Worker {worker_id} move {cmd[0]} out of bounds from {(x, y)}"

        # 3. Overflow check: zero shed overflow discard in forward simulation
        if outcome.candidate_overflow_units > 0:
            checks["overflow_ok"] = False
            checks["resource_consistency_ok"] = False
            checks["capacity_consistency_ok"] = False
            return False, checks, f"Candidate caused {outcome.candidate_overflow_units} units of shed overflow"

        # 4. Solvency check: candidate money remains non-negative
        if outcome.candidate_final_money < 0.0:
            checks["solvency_ok"] = False
            checks["cash_liquidity_ok"] = False
            return False, checks, f"Negative cash balance (${outcome.candidate_final_money:.2f})"

        # 5. Obligation preservation / intermediate solvency check
        if not outcome.intermediate_solvency_ok:
            checks["obligation_ok"] = False
            checks["obligation_consistency_ok"] = False
            checks["solvency_ok"] = False
            return False, checks, "Failed intermediate market solvency (shed deficit on scheduled sell)"

        # 6. Terminal feasibility check: executable terminal state
        if outcome.candidate_final_money < 0:
            checks["terminal_feasible"] = False
            checks["terminal_resource_ok"] = False
            return False, checks, "Infeasible terminal money"

        # 7. Spatial continuation consistency check
        if not getattr(outcome, "spatial_consistency_ok", True):
            checks["spatial_consistency_ok"] = False
            checks["spatial_validity_ok"] = False
            checks["route_continuity_ok"] = False
            reason = getattr(outcome, "desynchronization_reason", "diverged position")
            return False, checks, f"Candidate caused spatial desynchronization in continuation: {reason}"

        # 8. Counterfactual fidelity certification check (§14)
        fidelity = getattr(outcome, "fidelity", "VERIFIED")
        if fidelity in ("FAILED", "UNKNOWN"):
            checks["fidelity_ok"] = False
            reasons = getattr(outcome, "fidelity_reasons", [])
            return False, checks, f"Counterfactual fidelity {fidelity}: {', '.join(reasons) or 'unverified simulation'}"

        # 9. Extended Resource Safety Invariants (§17, §18)
        # 9a. Feed Security Invariant
        if not getattr(outcome, "feed_security_ok", True) or getattr(outcome, "feed_deficit_units", 0) > 0:
            checks["feed_security_ok"] = False
            checks["obligation_consistency_ok"] = False
            return False, checks, f"Feed security invariant breached: {getattr(outcome, 'feed_deficit_units', 0)} deficit units"
        if patch.resource_changes.get("feed_security_breach"):
            checks["feed_security_ok"] = False
            return False, checks, "Candidate explicitly breaches livestock feed security obligation"

        # 9b. Negative Inventory Invariant
        if patch.resource_changes.get("negative_inventory"):
            checks["negative_inventory_ok"] = False
            return False, checks, "Candidate causes negative inventory stock"

        # 9c. Resource Conservation Invariant
        if patch.resource_changes.get("conservation_violation"):
            checks["resource_conservation_ok"] = False
            return False, checks, "Candidate violates strict resource conservation balance"

        # 9d. Capacity Consistency Invariant
        if patch.resource_changes.get("capacity_overflow") or outcome.candidate_overflow_units > 0:
            checks["capacity_consistency_ok"] = False
            return False, checks, "Candidate violates shed storage capacity limit (100 units)"

        # 9e. Cash Liquidity Invariant
        if patch.resource_changes.get("cash_deadlock"):
            checks["cash_liquidity_ok"] = False
            return False, checks, "Candidate creates intermediate cash liquidity deadlock"

        # 9f. Conversion Preconditions Invariant
        if patch.resource_changes.get("missing_prerequisites") or patch.conversion_metadata.get("is_feasible") is False:
            checks["conversion_precondition_ok"] = False
            reason = patch.conversion_metadata.get("infeasibility_reason", "missing conversion prerequisites")
            return False, checks, f"Conversion prerequisite failure: {reason}"

        # 9g. Temporal Availability Invariant
        if patch.resource_changes.get("delayed_arrival") or patch.resource_changes.get("temporal_violation"):
            checks["temporal_availability_ok"] = False
            return False, checks, "Candidate attempts consumption before resource arrival/maturation"

        # 9h. Reservation Consistency Invariant
        if patch.resource_changes.get("double_allocation") or patch.resource_changes.get("reservation_conflict"):
            checks["reservation_consistency_ok"] = False
            return False, checks, "Candidate double-allocates inventory unit to conflicting obligations"

        # 9i. Terminal Resource Usability Invariant
        if patch.resource_changes.get("terminal_infeasible") or patch.conversion_metadata.get("terminal_infeasible"):
            checks["terminal_resource_ok"] = False
            return False, checks, "Terminal conversion cannot complete before game ends"

        # 9j. Terminal Purpose Consistency Check (§10, §11, §15)
        if patch.mechanism_family == "EMERGENCY_FEED_PURCHASE":
            passed_tp, tp_reason = self.verify_terminal_purpose(
                patch, outcome, econ_state, baseline_action, future_trajectory
            )
            if not passed_tp:
                checks["terminal_purpose_ok"] = False
                checks["terminal_resource_ok"] = False
                return False, checks, f"Terminal purpose inconsistency: {tp_reason}"
        if patch.resource_changes.get("terminal_purpose_inconsistent"):
            checks["terminal_purpose_ok"] = False
            return False, checks, "Explicit terminal purpose inconsistency recorded on patch"

        return True, checks, None

    def verify_terminal_purpose(
        self,
        patch: CoupledPatch,
        outcome: SimulationOutcome,
        econ_state: EconomicState,
        baseline_action: Optional[Dict[str, Any]] = None,
        future_trajectory: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[bool, Optional[str]]:
        """Verifies that an emergency feed purchase has a realizable downstream purpose before terminal (§10, §11, §13, §15).
        
        Strictly uses exact, game-derived terminal obligation modeling.
        Arbitrary constants ($150 buffer, -$50 delta_terminal_margin) are completely removed.
        """
        from aec.terminal.obligations import TerminalObligationChecker
        checker = TerminalObligationChecker()
        is_safe, reason, details = checker.verify_candidate_safety(
            econ_state=econ_state,
            candidate_patch=patch,
            sim_outcome=outcome,
            baseline_action=baseline_action or {},
            future_trajectory=future_trajectory
        )
        if not is_safe:
            return False, reason

        return True, None
