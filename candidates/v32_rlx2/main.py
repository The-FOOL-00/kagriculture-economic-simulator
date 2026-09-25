# SPDX-License-Identifier: MIT
"""Kagriculture V32 RL-X2 Standalone Submission Candidate.

Integrates learned strategic policy, deterministic executor, legality filter,
and fail-closed A7 baseline fallback.
"""

from __future__ import annotations
import copy
import os
import sys
from typing import Any, Dict, Optional
import numpy as np

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from candidates.v32_rlx2.action_space import ACTION_SPACE_SIZE, get_action_mask
from candidates.v32_rlx2.rlx2_config import RLX2Config
from candidates.v32_rlx2.executor import StrategicExecutor
from candidates.v32_rlx2.policy import StrategicActor
from candidates.v32_rlx2.safety import SafetyEnforcer
from candidates.v32_rlx2.state import extract_economic_features, get_feature_dim, vectorize_features
from scripts.v32_common import load_agent


class RLX2SubmissionAgent:
    """Production competition agent integrating RL-X2 strategic policy."""
    
    def __init__(
        self,
        checkpoint_path: Optional[str] = None,
        state_tier: str = "S2",
        macro_interval: int = 4
    ):
        self.state_tier = state_tier
        self.macro_interval = macro_interval
        self.executor = StrategicExecutor()
        self.safety = SafetyEnforcer()
        
        self.a7_baseline = load_agent("E9_AST")
        self.actor: Optional[StrategicActor] = None
        
        state_dim = get_feature_dim(tier=state_tier)
        if HAS_TORCH:
            self.actor = StrategicActor(state_dim=state_dim, action_dim=ACTION_SPACE_SIZE)
            if checkpoint_path and os.path.exists(checkpoint_path):
                try:
                    self.actor.load_state_dict(torch.load(checkpoint_path, map_location="cpu"))
                    self.actor.eval()
                except Exception as e:
                    print(f"[WARN] Failed to load checkpoint {checkpoint_path}: {e}")
                    
        self.current_macro_action = 0
        self.step_counter = 0
        
    def act(self, observation: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Main agent entrypoint called by Kaggle competition environment."""
        # 1. Base A7 action (Protected baseline fallback)
        try:
            base_a7 = self.a7_baseline.act(observation, configuration)
        except Exception:
            base_a7 = {"farmer": ["PASS"], "hands": [], "market": []}
            
        step = int(observation.get("step", self.step_counter) or self.step_counter)
        self.step_counter = step + 1
        player = int(observation.get("player", 0) or 0)
        
        # 2. Strategic decision at macro intervals
        if step % self.macro_interval == 0:
            try:
                features = extract_economic_features(observation, player=player)
                mask = get_action_mask(features)
                if self.actor is not None:
                    vec = vectorize_features(features, tier=self.state_tier)
                    self.current_macro_action, _, _ = self.actor.get_action(vec, mask, deterministic=True)
                else:
                    self.current_macro_action = 0
            except Exception:
                self.current_macro_action = 0  # Fail-closed to FOLLOW_A7
                
        # 3. Deterministic execution
        try:
            features = extract_economic_features(observation, player=player)
            candidate = self.executor.execute(
                macro_action=self.current_macro_action,
                observation=observation,
                features=features,
                base_a7_action=base_a7
            )
            return self.safety.sanitize_action(candidate, base_a7, observation)
        except Exception:
            return copy.deepcopy(base_a7)


# Global persistent instance for Kaggle runner
_GLOBAL_AGENT: Optional[RLX2SubmissionAgent] = None


def agent(observation: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    global _GLOBAL_AGENT
    if _GLOBAL_AGENT is None:
        ckpt = os.path.join(os.path.dirname(__file__), "reports", "RLX2-F2_seed42_actor.pt")
        _GLOBAL_AGENT = RLX2SubmissionAgent(checkpoint_path=ckpt if os.path.exists(ckpt) else None)
    return _GLOBAL_AGENT.act(observation, configuration)
