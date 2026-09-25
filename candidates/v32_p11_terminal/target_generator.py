# SPDX-License-Identifier: MIT
"""
Target Generator for Terminal Physical Search.
Matches available workers to reachable harvest/collection targets under strict time & cargo constraints.
"""
from typing import List, Dict, Any, Tuple
from candidates.v32_p11_terminal.terminal_state import (
    TerminalState, manhattan_dist, dist_to_shed, nearest_shed_tile, is_shed_adjacent
)

class TargetAssignment:
    def __init__(self, worker_idx: int, target: Dict[str, Any], path_cost: int, net_value: float):
        self.worker_idx = worker_idx
        self.target = target
        self.path_cost = path_cost
        self.net_value = net_value

class TargetGenerator:
    def __init__(self, terminal_state: TerminalState, max_step: int = 718):
        self.ts = terminal_state
        self.max_step = max_step
        self.remaining_horizon = max_step - self.ts.step
        
    def generate_assignments(self, protect_cargo: bool = True) -> List[TargetAssignment]:
        """
        Generates feasible (worker, target) pairings.
        Strictly enforces:
        1. worker must be able to reach target, perform action, reach shed, and DROP at or before max_step.
        2. if worker carries cargo, any detour must not cause carried cargo to be stranded at max_step.
        """
        if self.remaining_horizon <= 1:
            return []
            
        all_targets = self.ts.get_realizable_targets(self.max_step)
        if not all_targets:
            return []
            
        assignments = []
        for w_idx, w_pos in enumerate(self.ts.worker_positions):
            has_cargo = self.ts.worker_has_cargo(w_idx)
            cargo_val = self.ts.worker_cargo_value(w_idx)
            
            # If cargo protection is enabled and worker holds cargo with value >= 10,
            # prioritize immediate return to shed rather than risky detours.
            if protect_cargo and cargo_val >= 10.0:
                continue
                
            for target in all_targets:
                t_pos = target["pos"]
                d_to_target = manhattan_dist(w_pos, t_pos)
                act_cost = 1  # 1 step to HARVEST or COLLECT_FERTILIZER
                d_target_to_shed = target["dist_to_shed"]
                drop_cost = 1  # 1 step to DROP
                
                total_steps_needed = d_to_target + act_cost + d_target_to_shed + drop_cost
                
                # Strict feasibility check: must finish DROP before or on max_step
                if self.ts.step + total_steps_needed > self.max_step:
                    continue
                    
                net_val = target["gross_val"]
                assignments.append(TargetAssignment(
                    worker_idx=w_idx,
                    target=target,
                    path_cost=total_steps_needed,
                    net_value=net_val
                ))
                
        # Sort assignments by net_value descending, then path_cost ascending
        assignments.sort(key=lambda a: (-a.net_value, a.path_cost))
        return assignments
