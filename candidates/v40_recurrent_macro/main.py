# SPDX-License-Identifier: MIT
"""Kagriculture V40 Recurrent Macro Strategic Controller (Competition Candidate).

Architecture:
1. Low-Level Execution: Deterministic A7 chore chassis + V35 25/25 opening capital wash.
2. High-Level Macro: Learned 112-dim observation -> 128-dim GRU recurrent state -> 16 macro actions.
3. Fail-Closed Resilience: Immediate fallback to V35 baseline on any exception.
"""

from __future__ import annotations
import copy
import os
import sys
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.v32_common import load_agent
from research.v40.policy.observation import V40ObservationEncoder, OBSERVATION_DIM
from research.v40.policy.actions import StrategicMacroExecutor, get_macro_action_mask, NUM_MACRO_ACTIONS
from research.v40.policy.expert import V40ExpertPolicy
from research.v40.policy.model import V40RecurrentActorCritic

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class V40RecurrentController:
    """Production competition controller combining recurrent macro RL with A7 chore chassis."""

    def __init__(
        self,
        weights_path: Optional[str] = None,
        macro_interval: int = 4,
        device: str = "cpu"
    ):
        self.macro_interval = macro_interval
        self.device = torch.device(device) if TORCH_AVAILABLE else None
        self.a7_agent = load_agent("E9_AST")
        self.encoder = V40ObservationEncoder()
        self.expert = V40ExpertPolicy()
        self.executor = StrategicMacroExecutor()

        self.model = None
        self.rnn_state = None
        self.prev_macro_action = 0
        self.initialized = False

        if TORCH_AVAILABLE:
            path = weights_path or os.path.join(os.path.dirname(__file__), "model_weights.pt")
            if os.path.exists(path):
                try:
                    self.model = V40RecurrentActorCritic(
                        obs_dim=OBSERVATION_DIM,
                        num_actions=NUM_MACRO_ACTIONS,
                        hidden_dim=128,
                        rnn_type="GRU"
                    ).to(self.device)

                    ckpt = torch.load(path, map_location=self.device, weights_only=True)
                    state_dict = ckpt["model_state_dict"] if "model_state_dict" in ckpt else ckpt
                    self.model.load_state_dict(state_dict)
                    self.model.eval()
                    self.rnn_state = self.model.initial_state(batch_size=1, device=self.device)
                    self.initialized = True
                except Exception as e:
                    self.model = None
                    self.initialized = False

    def reset(self):
        """Resets match-level state."""
        self.a7_agent = load_agent("E9_AST")
        self.encoder.reset()
        self.expert.reset()
        self.prev_macro_action = 0
        if self.initialized and self.model is not None:
            self.rnn_state = self.model.initial_state(batch_size=1, device=self.device)

    def act(self, observation: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Kaggle-compliant action execution with strict fail-closed safety."""
        try:
            step = int(observation.get("step", 0) or 0)
            player = int(observation.get("player", 0) or 0)

            if step <= 0:
                self.reset()

            # Base A7 action
            base_action = self.a7_agent.act(observation, configuration)

            # Step 0 Opening Optimization (V35 25/25 wheat wash)
            if step == 0:
                act = copy.deepcopy(base_action)
                act["market"] = [
                    ["BUY_PRODUCT", "WHEAT", 25],
                    ["SELL", "WHEAT", 25]
                ]
                return act

            # If neural model is not active, fallback directly to base A7
            if not self.initialized or self.model is None:
                return base_action

            # Macro decision interval
            if step % self.macro_interval == 0 and step < 710:
                obs_vec = self.encoder.encode(observation, player=player, prev_macro_action=self.prev_macro_action)
                mask = get_macro_action_mask(observation, player=player)

                obs_t = torch.tensor(obs_vec, dtype=torch.float32, device=self.device).unsqueeze(0)
                mask_t = torch.tensor(mask, dtype=torch.bool, device=self.device).unsqueeze(0)

                with torch.no_grad():
                    act_t, lp_t, ent_t, val_t, next_rnn, aux_t = self.model.forward_step(
                        obs_t, mask_t, self.rnn_state, deterministic=True
                    )

                self.prev_macro_action = act_t.item()
                self.rnn_state = next_rnn

            # Physical execution: Base expert action modified by macro decision
            return self.executor.execute(self.prev_macro_action, base_action, observation, player=player)

        except Exception:
            # Strict fail-closed fallback: return safe base A7 action or pass
            try:
                return self.a7_agent.act(observation, configuration)
            except Exception:
                return {"farmer": ["PASS"], "hands": [], "market": []}


_CONTROLLER: Optional[V40RecurrentController] = None


def agent(observation: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Official competition agent entrypoint."""
    global _CONTROLLER
    if _CONTROLLER is None:
        _CONTROLLER = V40RecurrentController()

    try:
        step = int(observation.get("step", 0) or 0)
    except Exception:
        step = -1

    if step <= 0:
        _CONTROLLER.reset()

    return _CONTROLLER.act(observation, configuration)
