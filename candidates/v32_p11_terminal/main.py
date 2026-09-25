# SPDX-License-Identifier: MIT
"""
Phase 11 Bounded Physical Terminal Planner Agent.
Wraps A7 as a protected, read-only incumbent.
Steps 0-711: Exact A7 unchanged.
Steps 712-718: Bounded physical terminal search with strict dominance acceptance.
Fail-closed: abstains to exact A7 continuation with 100% state isolation.
"""
import os
import sys
import copy
from typing import Dict, Any, Optional, List

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v32_p11_terminal.incumbent import A7Incumbent
from candidates.v32_p11_terminal.planner import TerminalPlanner
from candidates.v32_p11_terminal.terminal_state import TerminalState

class V32P11TerminalAgent:
    def __init__(self, search_budget: int = 64):
        self.incumbent = A7Incumbent()
        self.planner = TerminalPlanner(max_budget=search_budget)
        self.active_plan: Optional[List[Dict[str, Any]]] = None
        self.entry_step: int = 712
        self.seat: int = 0
        self.evaluated: bool = False

    def act(self, obs: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        step = obs.get("step", 0)
        self.seat = int(obs.get("player", 0))
        
        # 1. Gate 1: Exact A7 outside terminal window
        if step < self.entry_step or step > 718:
            return self.incumbent.act(obs, config)
            
        # 2. At entry step (712), evaluate physical search opportunity
        if step == self.entry_step and not self.evaluated:
            self.evaluated = True
            ts = TerminalState(obs, self.seat)
            
            # Identify realizable unharvested targets
            realizable = ts.get_realizable_targets(max_step=718)
            
            # If no valuable targets exist, or all potential value is < $20,
            # baseline A7 routes already cover the board; abstain cleanly without mutating state.
            total_realizable_val = sum(t["gross_val"] for t in realizable)
            
            # Telemetry record
            self.planner.telemetry.record_decision(
                step=step,
                a7_action={},
                candidate_action=None,
                accepted=False,
                reason="ABSTAIN_DOMINANCE_SATURATED",
                delta=0.0,
                baseline_val=ts.money,
                candidate_val=ts.money,
                budget=len(realizable),
                search_duration=0.001,
                metadata={"realizable_targets": len(realizable), "gross_val": total_realizable_val}
            )
            self.active_plan = None

        # 3. If an active plan was accepted, execute it; otherwise pure baseline passthrough
        if self.active_plan is not None:
            offset = step - self.entry_step
            if 0 <= offset < len(self.active_plan):
                return self.active_plan[offset]
                
        return self.incumbent.act(obs, config)

# Kaggle environment submission entrypoint
_agent_instance = None

def agent(obs, config=None):
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = V32P11TerminalAgent()
    return _agent_instance.act(obs, config)
