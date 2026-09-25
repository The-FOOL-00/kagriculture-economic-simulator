# SPDX-License-Identifier: MIT
"""Kagriculture V32 P12 Option Executor & Lifecycle Manager.

Manages execution, invariant checking, early termination, and fail-closed
resumption of the A7 incumbent for active options.
"""

from __future__ import annotations
import copy
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

try:
    from option_library import OptionContract
    from resync import ResyncState, SyncStatus
    from candidates.v32_rlx2.executor import StrategicExecutor
    from candidates.v32_rlx2.state import EconomicFeatures, extract_economic_features
except ImportError:
    from candidates.v32_p12_options.option_library import OptionContract
    from candidates.v32_p12_options.resync import ResyncState, SyncStatus
    from candidates.v32_rlx2.executor import StrategicExecutor
    from candidates.v32_rlx2.state import EconomicFeatures, extract_economic_features


@dataclass
class OptionExecutionStatus:
    is_active: bool
    option_id: Optional[str]
    ticks_elapsed: int
    terminated_early: bool
    termination_reason: str = ""


class OptionExecutor:
    """Controls the lifecycle of a single active option."""
    def __init__(self):
        self.underlying_executor = StrategicExecutor()
        self.active_option: Optional[OptionContract] = None
        self.start_step: int = -1
        self.ticks_elapsed: int = 0
        self.terminated_early: bool = False
        self.termination_reason: str = ""
        self.total_options_executed: int = 0
        self.early_terminations_count: int = 0

    @property
    def is_active(self) -> bool:
        return self.active_option is not None

    def start_option(self, option: OptionContract, current_step: int) -> bool:
        """Starts executing a new option if no option is currently active."""
        if self.is_active:
            # Hard non-stacking invariant: cannot start option while another is active
            return False
            
        self.active_option = option
        self.start_step = current_step
        self.ticks_elapsed = 0
        self.terminated_early = False
        self.termination_reason = ""
        self.total_options_executed += 1
        return True

    def execute_step(
        self,
        observation: Dict[str, Any],
        features: EconomicFeatures,
        base_a7_action: Dict[str, Any],
        resync_state: Optional[ResyncState] = None
    ) -> Tuple[Dict[str, Any], OptionExecutionStatus]:
        """Executes one simulation tick under the active option.

        Checks termination invariants and returns to A7 when complete.
        """
        if not self.is_active or self.active_option is None:
            status = OptionExecutionStatus(
                is_active=False,
                option_id=None,
                ticks_elapsed=0,
                terminated_early=False
            )
            return copy.deepcopy(base_a7_action), status

        current_step = getattr(features, "step", 0)
        
        # 1. Early Termination Checks (Section 17)
        # Check cash safety
        if features.cash < 50.0 and self.active_option.candidate_action in (4, 5, 6, 7, 9):
            self.terminate_option(reason="CASH_SAFETY_BREACH")
            status = self._get_status()
            return copy.deepcopy(base_a7_action), status
            
        # Check physical desync
        if resync_state and resync_state.status == SyncStatus.DESYNCED:
            self.terminate_option(reason="PHYSICAL_DESYNC_DETECTED")
            status = self._get_status()
            return copy.deepcopy(base_a7_action), status

        # 2. Execute Option Action
        try:
            action = self.underlying_executor.execute(
                macro_action=self.active_option.candidate_action,
                observation=observation,
                features=features,
                base_a7_action=base_a7_action
            )
        except Exception as e:
            self.terminate_option(reason=f"EXECUTION_EXCEPTION_{e}")
            status = self._get_status()
            return copy.deepcopy(base_a7_action), status

        self.ticks_elapsed += 1
        
        # 3. Check Duration Completion (Section 5: H = 4 ticks default)
        if self.ticks_elapsed >= self.active_option.duration:
            self.terminate_option(reason="DURATION_EXPIRED_MANDATORY_RETURN")
            
        status = self._get_status()
        return action, status

    def terminate_option(self, reason: str = "COMPLETED"):
        """Terminates the active option and resets state for mandatory A7 return."""
        if not self.is_active:
            return
            
        if reason != "DURATION_EXPIRED_MANDATORY_RETURN":
            self.terminated_early = True
            self.early_terminations_count += 1
            
        self.termination_reason = reason
        self.active_option = None
        self.start_step = -1

    def _get_status(self) -> OptionExecutionStatus:
        return OptionExecutionStatus(
            is_active=self.is_active,
            option_id=self.active_option.option_id if self.active_option else None,
            ticks_elapsed=self.ticks_elapsed,
            terminated_early=self.terminated_early,
            termination_reason=self.termination_reason
        )

    def reset(self):
        self.active_option = None
        self.start_step = -1
        self.ticks_elapsed = 0
        self.terminated_early = False
        self.termination_reason = ""
