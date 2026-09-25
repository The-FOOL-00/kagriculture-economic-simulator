# SPDX-License-Identifier: MIT
"""Kagriculture V32 P12 Sparse Option Controller & Policy.

Orchestrates the P12 architecture:
  Observation -> A7 Base Action -> Opportunity Detector
    -> (No Event -> A7)
    -> (Event -> Candidate Evaluation -> Option Gate)
        -> (Accepted -> Execute Option H=4 -> Mandatory Return -> Resync -> A7)
        -> (Rejected -> Fail-Closed A7)
"""

from __future__ import annotations
import copy
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import torch

try:
    from incumbent import A7Incumbent
    from option_library import OPTION_LIBRARY, OptionContract
    from option_executor import OptionExecutor
    from opportunity_detector import OpportunityDetector, DetectionResult
    from acceptance import OptionAcceptanceGate, AcceptanceDecision
    from resync import ResyncState, SyncStatus, evaluate_resync
    from candidates.v32_rlx2.state import EconomicFeatures, extract_economic_features
except ImportError:
    from candidates.v32_p12_options.incumbent import A7Incumbent
    from candidates.v32_p12_options.option_library import OPTION_LIBRARY, OptionContract
    from candidates.v32_p12_options.option_executor import OptionExecutor
    from candidates.v32_p12_options.opportunity_detector import OpportunityDetector, DetectionResult
    from candidates.v32_p12_options.acceptance import OptionAcceptanceGate, AcceptanceDecision
    from candidates.v32_p12_options.resync import ResyncState, SyncStatus, evaluate_resync
    from candidates.v32_rlx2.state import EconomicFeatures, extract_economic_features


@dataclass
class OptionControllerConfig:
    max_options_per_episode: int = 1        # F1 baseline (ablation: F0, F1, F2, F3)
    min_separation_ticks: int = 24          # Minimum cooldown ticks
    option_horizon: int = 4                 # Initial horizon H = 4
    require_full_sync: bool = True          # Only allow option when SYNCED
    mode: str = "oracle_search"             # "oracle_search", "supervised", "ppo", "passthrough_a7"
    supervised_model_path: Optional[str] = None
    ppo_model_path: Optional[str] = None


class SparseOptionController:
    """The central P12 Controller managing A7 execution with sparse, bounded options."""
    def __init__(self, config: Optional[OptionControllerConfig] = None):
        self.cfg = config or OptionControllerConfig()
        self.incumbent = A7Incumbent()
        self.detector = OpportunityDetector()
        self.executor = OptionExecutor()
        self.acceptance_gate = OptionAcceptanceGate()
        
        # State tracking
        self.options_executed_this_episode: int = 0
        self.last_option_end_step: int = -999
        self.history_decisions: List[Dict[str, Any]] = []
        self.current_resync_state: Optional[ResyncState] = None
        self.current_step: int = 0

        # Optional learned selector
        self.supervised_selector = None
        self.ppo_selector = None
        if self.cfg.mode == "supervised":
            try:
                from candidates.v32_p12_options.supervised import SupervisedOptionSelector
                ckpt = self.cfg.supervised_model_path or os.path.join(REPO_ROOT, "candidates/v32_p12_options/checkpoints/supervised_selector_seed_42.pt")
                self.supervised_selector = SupervisedOptionSelector(model_path=ckpt)
            except Exception as e:
                print(f"Warning: Failed to load supervised selector: {e}")
        elif self.cfg.mode == "ppo":
            try:
                from candidates.v32_p12_options.ppo_selector import PPOOptionSelector
                self.ppo_selector = PPOOptionSelector()
                ckpt = self.cfg.ppo_model_path or os.path.join(REPO_ROOT, "candidates/v32_p12_options/checkpoints/ppo_option_selector.pt")
                if os.path.exists(ckpt):
                    self.ppo_selector.ac.load_state_dict(torch.load(ckpt, map_location="cpu"))
            except Exception as e:
                print(f"Warning: Failed to load PPO selector: {e}")

    def reset(self):
        """Resets controller state for a new episode."""
        self.incumbent.reset()
        self.executor.reset()
        self.options_executed_this_episode = 0
        self.last_option_end_step = -999
        self.history_decisions = []
        self.current_resync_state = None
        self.current_step = 0

    def act(self, observation: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Main step function called every simulation tick."""
        player = int(observation.get("player", 0) or 0)
        farms = observation.get("farms", [{}, {}])
        self.current_step = int(observation.get("step", self.current_step) or self.current_step)

        # 1. Generate base A7 action (Protected Default)
        base_a7_action = self.incumbent.act(observation, configuration)

        # If mode is pure passthrough (F0), return A7 unconditionally
        if self.cfg.mode == "passthrough_a7" or self.cfg.max_options_per_episode == 0:
            return base_a7_action

        # Extract observable features
        features = extract_economic_features(observation, player=player)

        # 2. If an option is currently active, execute it
        if self.executor.is_active:
            action, status = self.executor.execute_step(
                observation=observation,
                features=features,
                base_a7_action=base_a7_action,
                resync_state=self.current_resync_state
            )
            if not status.is_active:
                # Option just finished! Enforce mandatory return to A7
                self.options_executed_this_episode += 1
                self.last_option_end_step = self.current_step
            return action

        # 3. Check Option Invariants (Sections 6, 8, 18, 20)
        # Check max options budget
        if self.options_executed_this_episode >= self.cfg.max_options_per_episode:
            return base_a7_action

        # Check spacing interval
        if (self.current_step - self.last_option_end_step) < self.cfg.min_separation_ticks:
            return base_a7_action

        # Check physical synchronization gate
        if self.cfg.require_full_sync and self.current_resync_state:
            if self.current_resync_state.status != SyncStatus.SYNCED:
                # Displaced worker or chore lag -> A7-only recovery!
                return base_a7_action

        # 4. Opportunity Detector (Section 11)
        detection = self.detector.detect(features, self.current_step)
        if not detection.detected or not detection.candidate_options:
            return base_a7_action

        # 5. Candidate Selection & Acceptance
        chosen_option = None
        if self.cfg.mode == "supervised" and self.supervised_selector is not None:
            from candidates.v32_rlx2.state import vectorize_features
            from candidates.v32_p12_options.supervised import OPTION_INDEX_TO_ID
            vec = vectorize_features(features, tier="S2")
            pred_idx, conf, reason = self.supervised_selector.select_option(vec)
            if pred_idx != 0:
                opt_id = OPTION_INDEX_TO_ID.get(pred_idx)
                if opt_id and opt_id in OPTION_LIBRARY:
                    candidate = OPTION_LIBRARY[opt_id]
                    if candidate.expected_delta > 0:
                        chosen_option = candidate
        elif self.cfg.mode == "ppo" and self.ppo_selector is not None:
            from candidates.v32_rlx2.state import vectorize_features
            from candidates.v32_p12_options.supervised import OPTION_INDEX_TO_ID
            vec = vectorize_features(features, tier="S2")
            act_idx, _ = self.ppo_selector.select_action(vec, deterministic=True)
            if act_idx != 0:
                opt_id = OPTION_INDEX_TO_ID.get(act_idx)
                if opt_id and opt_id in OPTION_LIBRARY:
                    candidate = OPTION_LIBRARY[opt_id]
                    if candidate.expected_delta > 0:
                        chosen_option = candidate
        else:
            # Oracle search / deterministic gating mode
            for candidate in detection.candidate_options:
                if candidate.expected_delta > 0:
                    chosen_option = candidate
                    break

        if chosen_option is None:
            return base_a7_action

        # 6. Launch Option (H = 4 ticks)
        started = self.executor.start_option(chosen_option, self.current_step)
        if not started:
            return base_a7_action

        # Execute first tick of the accepted option
        action, _ = self.executor.execute_step(
            observation=observation,
            features=features,
            base_a7_action=base_a7_action,
            resync_state=self.current_resync_state
        )
        return action
