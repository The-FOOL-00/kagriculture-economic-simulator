# SPDX-License-Identifier: MIT
"""
Bounded Physical Terminal Planner.
Performs exact bounded forward search over legal worker paths in steps 712-718.
"""
import copy
import time
from typing import Dict, List, Any, Optional, Tuple

from candidates.v32_p11_terminal.terminal_state import TerminalState
from candidates.v32_p11_terminal.target_generator import TargetGenerator, TargetAssignment
from candidates.v32_p11_terminal.path_generator import build_worker_plan
from candidates.v32_p11_terminal.simulator import ShadowSimulator
from candidates.v32_p11_terminal.acceptance import AcceptanceEvaluator
from candidates.v32_p11_terminal.telemetry import TerminalTelemetry

class TerminalPlanner:
    def __init__(
        self,
        max_budget: int = 64,
        max_step: int = 718,
        protect_cargo: bool = True
    ):
        self.max_budget = max_budget
        self.max_step = max_step
        self.protect_cargo = protect_cargo
        self.simulator = ShadowSimulator()
        self.evaluator = AcceptanceEvaluator()
        self.telemetry = TerminalTelemetry()

    def plan(
        self,
        obs: Dict[str, Any],
        baseline_schedule: List[Dict[str, Any]],
        seat: int = 0
    ) -> Tuple[Optional[List[Dict[str, Any]]], str, float]:
        """
        Executes bounded physical search:
        1. Simulates baseline schedule.
        2. Generates feasible physical target candidates.
        3. Evaluates candidates under search budget.
        4. Returns best accepted schedule or (None, reason, 0.0)
        """
        t0 = time.time()
        ts = TerminalState(obs, seat)
        horizon = len(baseline_schedule)
        
        # 1. Simulate baseline continuation
        base_sim = self.simulator.simulate_schedule(obs, baseline_schedule, seat)
        base_cash = base_sim["final_money"]
        
        # 2. Generate candidate target assignments
        tg = TargetGenerator(ts, self.max_step)
        assignments = tg.generate_assignments(protect_cargo=self.protect_cargo)
        
        if not assignments:
            dur = time.time() - t0
            self.telemetry.record_decision(
                step=ts.step,
                a7_action=baseline_schedule[0],
                candidate_action=None,
                accepted=False,
                reason="NO_FEASIBLE_TARGETS",
                delta=0.0,
                baseline_val=base_cash,
                candidate_val=base_cash,
                budget=0,
                search_duration=dur
            )
            return None, "NO_FEASIBLE_TARGETS", 0.0

        best_schedule = None
        best_delta = 0.0
        best_reason = "ABSTAIN_DOMINANCE"
        eval_count = 0
        
        # Bounded evaluation budget
        candidate_pool = assignments[:self.max_budget]
        for assign in candidate_pool:
            eval_count += 1
            w_idx = assign.worker_idx
            target = assign.target
            w_pos = ts.worker_positions[w_idx]
            
            # Generate worker action sequence
            w_plan = build_worker_plan(w_pos, target["pos"], target["op"], horizon)
            
            # Splice into candidate schedule
            cand_schedule = copy.deepcopy(baseline_schedule)
            for t_offset in range(horizon):
                step_act = cand_schedule[t_offset]
                if w_idx == 0:
                    step_act["farmer"] = w_plan[t_offset]
                else:
                    h_idx = w_idx - 1
                    while len(step_act.get("hands", [])) <= h_idx:
                        step_act.setdefault("hands", []).append(["PASS"])
                    step_act["hands"][h_idx] = w_plan[t_offset]
                    
            # Terminal market liquidation for the newly collected item at step 718
            # Ensure step 718 sells the collected item if dropped
            last_offset = horizon - 1
            cand_last_act = cand_schedule[last_offset]
            mkt_orders = cand_last_act.get("market", [])
            item_sold = target["item"]
            # Check if order already exists
            has_item_order = any(o[0] == "SELL" and o[1] == item_sold for o in mkt_orders if len(o) >= 2)
            if not has_item_order and len(mkt_orders) < 10:
                mkt_orders.append(["SELL", item_sold, 1000])
                cand_last_act["market"] = mkt_orders
                
            # Simulate candidate
            cand_sim = self.simulator.simulate_schedule(obs, cand_schedule, seat)
            accepted, reason, delta = self.evaluator.evaluate(base_sim, cand_sim, cand_schedule)
            
            if accepted and delta > best_delta:
                best_delta = delta
                best_schedule = cand_schedule
                best_reason = reason
                
        dur = time.time() - t0
        accepted_final = best_schedule is not None
        self.telemetry.record_decision(
            step=ts.step,
            a7_action=baseline_schedule[0],
            candidate_action=best_schedule[0] if best_schedule else None,
            accepted=accepted_final,
            reason=best_reason if not accepted_final else "OK_ACTIVATED",
            delta=best_delta,
            baseline_val=base_cash,
            candidate_val=base_cash + best_delta,
            budget=eval_count,
            search_duration=dur
        )
        
        return best_schedule, best_reason, best_delta
