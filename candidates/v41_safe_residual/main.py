# SPDX-License-Identifier: MIT
"""Kagriculture V41 Safe Residual Strategic Controller (Research Candidate).

Architecture:
1. Baseline: High-fidelity V35 opening (25/25 wheat wash) + A7 chore chassis.
2. Observation: Normalized 103-dim macroeconomic & temporal representation.
3. Policy: Temporal GRU strategic advantage model estimating Q(s, a) = Cash(a) - Cash(0).
4. Safety & Legality: Mechanical action masking preventing state desynchronization.
5. Fail-Closed Gating: Strictly defaults to V35 baseline on any error, exception,
   or if predicted advantage is below the confidence threshold.
"""

from __future__ import annotations
import copy
import os
import sys
from typing import Any, Dict, List, Optional
import numpy as np
import torch

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v35_a7_opening.main import V35OpeningController
from research.v41.executor.safe_executor import StateAwareExecutor, NUM_INTERVENTIONS
from research.v41.policy.observation import V41ObservationEncoder, OBSERVATION_DIM
from research.v41.policy.model import V41TemporalStrategicPolicy

_SAFE_ACTION = {"farmer": ["PASS"], "hands": [], "market": []}
MODEL_WEIGHTS_PATH = os.path.join(os.path.dirname(__file__), "model_weights.pt")


class V41SafeResidualController:
    """Production-grade safe residual controller."""

    def __init__(self, confidence_threshold: float = 30.0):
        self.conf_thresh = confidence_threshold
        self.executor = StateAwareExecutor()
        self.encoder = V41ObservationEncoder()
        self.policy: Optional[V41TemporalStrategicPolicy] = None
        self.hx: Optional[torch.Tensor] = None

        # Load weights if available
        if os.path.exists(MODEL_WEIGHTS_PATH):
            try:
                p = V41TemporalStrategicPolicy(
                    obs_dim=OBSERVATION_DIM,
                    hidden_dim=128,
                    num_actions=NUM_INTERVENTIONS
                )
                ckpt = torch.load(MODEL_WEIGHTS_PATH, map_location="cpu", weights_only=False)
                if "model_state_dict" in ckpt:
                    p.load_state_dict(ckpt["model_state_dict"])
                else:
                    p.load_state_dict(ckpt)
                p.eval()
                self.policy = p
            except Exception:
                self.policy = None

    def reset(self):
        self.executor.reset()
        self.encoder.reset()
        if self.policy is not None:
            self.hx = self.policy.init_hidden(1, device=torch.device("cpu"))
        else:
            self.hx = None

    def act(self, observation: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            step = int(observation.get("step", 0) or 0)
            if step <= 0:
                self.reset()

            action_idx = 0
            if self.policy is not None:
                try:
                    obs_vec = self.encoder.encode(observation, player=0)
                    mask = self.executor.get_safety_mask(observation, player=0)
                    action_idx, q_val, self.hx = self.policy.select_intervention(
                        obs_vec=obs_vec,
                        action_mask=mask,
                        hx=self.hx,
                        confidence_threshold=self.conf_thresh,
                        device="cpu"
                    )
                except Exception:
                    action_idx = 0  # Fail closed to baseline

            return self.executor.execute(action_idx, observation, configuration, player=0)

        except Exception:
            # Absolute fail-closed fallback
            return dict(_SAFE_ACTION)


_CONTROLLER = V41SafeResidualController()


def agent(observation: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Kaggle-compliant entry point."""
    global _CONTROLLER
    return _CONTROLLER.act(observation, configuration)
