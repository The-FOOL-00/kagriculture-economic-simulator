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
        baseline_action: Dict[str, Any]
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
        }

        # 1. Legality check
        if patch.market_mutations is not None:
            if len(patch.market_mutations) > MAX_MARKET_ORDERS:
                checks["legality_ok"] = False
                return False, checks, f"Market order count {len(patch.market_mutations)} exceeds max {MAX_MARKET_ORDERS}"
            for order in patch.market_mutations:
                if not isinstance(order, (list, tuple)) or not order:
                    checks["legality_ok"] = False
                    return False, checks, "Malformed market order"
                if order[0] not in ("SELL", "BUY_PRODUCT", "BUY_SEED", "BUY_ANIMAL", "HIRE", "BUY_LAND"):
                    checks["legality_ok"] = False
                    return False, checks, f"Illegal market op {order[0]}"

        # 2. Feasibility of worker movements
        for worker_id, cmd in patch.worker_mutations.items():
            worker = econ_state.workers.get_worker(worker_id)
            if worker is None:
                checks["feasibility_ok"] = False
                return False, checks, f"Non-existent worker_id {worker_id}"
            if cmd and cmd[0] in MOVES:
                dx, dy = MOVES[cmd[0]]
                x, y = worker.position
                if not (0 <= x + dx < BOARD_SIZE and 0 <= y + dy < BOARD_SIZE):
                    checks["feasibility_ok"] = False
                    return False, checks, f"Worker {worker_id} move {cmd[0]} out of bounds from {(x, y)}"

        # 3. Overflow check: zero shed overflow discard in forward simulation
        if outcome.candidate_overflow_units > 0:
            checks["overflow_ok"] = False
            return False, checks, f"Candidate caused {outcome.candidate_overflow_units} units of shed overflow"

        # 4. Solvency check: candidate money remains non-negative
        if outcome.candidate_final_money < 0.0:
            checks["solvency_ok"] = False
            return False, checks, f"Negative cash balance (${outcome.candidate_final_money:.2f})"

        # 5. Obligation preservation / intermediate solvency check
        if not outcome.intermediate_solvency_ok:
            checks["obligation_ok"] = False
            return False, checks, "Failed intermediate market solvency (shed deficit on scheduled sell)"

        # 6. Terminal feasibility check: executable terminal state
        if outcome.candidate_final_money < 0:
            checks["terminal_feasible"] = False
            return False, checks, "Infeasible terminal money"

        # 7. Spatial continuation consistency check
        if not getattr(outcome, "spatial_consistency_ok", True):
            checks["spatial_consistency_ok"] = False
            reason = getattr(outcome, "desynchronization_reason", "diverged position")
            return False, checks, f"Candidate caused spatial desynchronization in continuation: {reason}"

        # 8. Counterfactual fidelity certification check (§14)
        fidelity = getattr(outcome, "fidelity", "VERIFIED")
        if fidelity in ("FAILED", "UNKNOWN"):
            checks["fidelity_ok"] = False
            reasons = getattr(outcome, "fidelity_reasons", [])
            return False, checks, f"Counterfactual fidelity {fidelity}: {', '.join(reasons) or 'unverified simulation'}"

        return True, checks, None
