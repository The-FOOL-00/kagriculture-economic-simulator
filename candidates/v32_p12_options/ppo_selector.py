# SPDX-License-Identifier: MIT
"""Kagriculture V32 P12 PPO Option Selector.

Learns WHEN to select a search-validated sparse option vs WHEN to follow A7.
Operates exclusively over high-level discrete option IDs (0=FOLLOW_A7, 1..6=Options).
Does NOT control physical actions or low-level chores.
"""

from __future__ import annotations
import copy
import os
import sys
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import torch
import torch.nn as nn
from torch.distributions.categorical import Categorical

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


class OptionActorCritic(nn.Module):
    """Discrete Actor-Critic network for sparse option selection."""
    def __init__(self, in_features: int = 71, num_actions: int = 7, hidden_dim: int = 128):
        super().__init__()
        self.actor = nn.Sequential(
            nn.Linear(in_features, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 64),
            nn.LayerNorm(64),
            nn.Tanh(),
            nn.Linear(64, num_actions)
        )
        self.critic = nn.Sequential(
            nn.Linear(in_features, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 64),
            nn.LayerNorm(64),
            nn.Tanh(),
            nn.Linear(64, 1)
        )

    def get_action_and_value(
        self,
        x: torch.Tensor,
        action: Optional[torch.Tensor] = None,
        action_mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        logits = self.actor(x)
        if action_mask is not None:
            # Mask out illegal options with large negative logit
            logits = torch.where(action_mask, logits, torch.tensor(-1e9, device=x.device))
            
        dist = Categorical(logits=logits)
        if action is None:
            action = dist.sample()
        return action, dist.log_prob(action), dist.entropy(), self.critic(x)

    def get_value(self, x: torch.Tensor) -> torch.Tensor:
        return self.critic(x)


class PPOOptionSelector:
    """PPO agent selecting discrete option interventions."""
    def __init__(
        self,
        in_features: int = 71,
        num_actions: int = 7,
        lr: float = 3e-4,
        clip_eps: float = 0.2,
        ent_coef: float = 0.01,
        vf_coef: float = 0.5
    ):
        self.ac = OptionActorCritic(in_features, num_actions)
        self.optimizer = torch.optim.Adam(self.ac.parameters(), lr=lr)
        self.clip_eps = clip_eps
        self.ent_coef = ent_coef
        self.vf_coef = vf_coef

    def select_action(
        self,
        state_vector: np.ndarray,
        action_mask: Optional[np.ndarray] = None,
        deterministic: bool = False
    ) -> Tuple[int, float]:
        with torch.no_grad():
            x = torch.as_tensor(state_vector, dtype=torch.float32).unsqueeze(0)
            mask_t = torch.as_tensor(action_mask, dtype=torch.bool).unsqueeze(0) if action_mask is not None else None
            logits = self.ac.actor(x)
            if mask_t is not None:
                logits = torch.where(mask_t, logits, torch.tensor(-1e9))
            if deterministic:
                act = int(torch.argmax(logits, dim=-1).item())
                val = float(self.ac.get_value(x).item())
                return act, val
            dist = Categorical(logits=logits)
            act = int(dist.sample().item())
            val = float(self.ac.get_value(x).item())
            return act, val

    def save(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        torch.save(self.ac.state_dict(), path)

    def load(self, path: str):
        self.ac.load_state_dict(torch.load(path, map_location="cpu"))
        self.ac.eval()
