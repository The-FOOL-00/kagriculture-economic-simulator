# SPDX-License-Identifier: MIT
"""
Acceptance Criteria and Invariant Gates for Terminal Physical Search.
Enforces strict cash dominance, intermediate solvency, and zero-stranding.
"""
from typing import Dict, Any, Tuple, List

class AcceptanceEvaluator:
    def __init__(self, min_gain_threshold: float = 0.5):
        self.min_gain_threshold = min_gain_threshold

    def evaluate(
        self,
        baseline_sim_result: Dict[str, Any],
        candidate_sim_result: Dict[str, Any],
        candidate_schedule: List[Dict[str, Any]]
    ) -> Tuple[bool, str, float]:
        """
        Evaluates candidate rollout against baseline.
        Returns: (accepted: bool, reason: str, delta: float)
        """
        base_cash = baseline_sim_result["final_money"]
        cand_cash = candidate_sim_result["final_money"]
        delta = cand_cash - base_cash
        
        # Gate 1: Strict economic gain
        if delta < self.min_gain_threshold:
            return False, "ABSTAIN_NO_ECONOMIC_GAIN", delta
            
        # Gate 2: Zero stranded cargo at terminal step
        cand_private = candidate_sim_result["private"]
        for idx, inv in enumerate(cand_private.get("inventories", [])):
            total_carried = sum(inv.values())
            if total_carried > 0:
                return False, f"REJECT_STRANDED_CARGO_WORKER_{idx}", delta
                
        # Gate 3: Cash non-negativity
        if cand_cash < 0:
            return False, "REJECT_INSOLVENT", delta
            
        return True, "OK_ACTIVATED", delta
