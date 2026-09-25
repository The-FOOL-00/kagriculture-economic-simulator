# SPDX-License-Identifier: MIT
"""Kagriculture V38 Neural Policy: Masked Discrete Macro Actor-Critic."""

from __future__ import annotations
import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Categorical

try:
    from config import NUM_MACRO_ACTIONS
    from state_features import ECONOMIC_FEATURE_DIM
except ImportError:
    from candidates.v38_heuristic_ppo.config import NUM_MACRO_ACTIONS
    from candidates.v38_heuristic_ppo.state_features import ECONOMIC_FEATURE_DIM


class MacroActorCritic(nn.Module):
    """Hierarchical Macro Actor-Critic network with action masking."""
    
    def __init__(
        self,
        obs_dim: int = ECONOMIC_FEATURE_DIM,
        act_dim: int = NUM_MACRO_ACTIONS,
        hidden_dim: int = 128
    ):
        super().__init__()
        self.obs_dim = obs_dim
        self.act_dim = act_dim
        
        # Shared trunk or separate actor/critic towers
        self.actor_net = nn.Sequential(
            nn.Linear(obs_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, act_dim)
        )
        
        self.critic_net = nn.Sequential(
            nn.Linear(obs_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1)
        )
        
        self._init_weights()
        
    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.orthogonal_(m.weight, gain=np.sqrt(2))
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0.0)
        # Small weights for final policy layer to encourage uniform prior initially
        nn.init.orthogonal_(self.actor_net[-1].weight, gain=0.01)

    def forward(
        self,
        obs: torch.Tensor,
        action_mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Returns (masked_logits, value)."""
        logits = self.actor_net(obs)
        if action_mask is not None:
            # Mask illegal actions with large negative value
            huge_neg = -1e8
            logits = torch.where(action_mask.bool(), logits, torch.tensor(huge_neg, device=logits.device))
        value = self.critic_net(obs).squeeze(-1)
        return logits, value

    def get_action_and_value(
        self,
        obs: torch.Tensor,
        action_mask: Optional[torch.Tensor] = None,
        action: Optional[torch.Tensor] = None,
        deterministic: bool = False
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """Samples or evaluates an action.
        
        Returns:
            (action, log_prob, entropy, value, confidence)
        """
        logits, value = self.forward(obs, action_mask)
        probs = F.softmax(logits, dim=-1)
        dist = Categorical(probs=probs)
        
        if action is None:
            if deterministic:
                action = torch.argmax(probs, dim=-1)
            else:
                action = dist.sample()
                
        confidence = probs.gather(-1, action.unsqueeze(-1)).squeeze(-1)
        log_prob = dist.log_prob(action)
        entropy = dist.entropy()
        
        return action, log_prob, entropy, value, confidence
