# SPDX-License-Identifier: MIT
"""Kagriculture V32 RL-X2 Policy Network (Actor).

Discrete categorical policy with action masking, LayerNorm, orthogonal
initialization, and temperature control.
"""

from __future__ import annotations
from typing import Dict, Optional, Tuple
import torch
import torch.nn as nn
import torch.distributions as D
import numpy as np


class StrategicActor(nn.Module):
    """Feedforward strategic macro policy."""
    
    def __init__(self, state_dim: int, action_dim: int = 10, hidden_dim: int = 256):
        super().__init__()
        self.state_dim = state_dim
        self.action_dim = action_dim
        
        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.LayerNorm(hidden_dim // 2),
            nn.Tanh(),
            nn.Linear(hidden_dim // 2, action_dim),
        )
        
        self._init_weights()
        
    def _init_weights(self):
        for m in self.net.modules():
            if isinstance(m, nn.Linear):
                nn.init.orthogonal_(m.weight, gain=np.sqrt(2))
                nn.init.constant_(m.bias, 0.0)
        # Final layer smaller gain for uniform initial exploration
        final_layer = self.net[-1]
        nn.init.orthogonal_(final_layer.weight, gain=0.01)
        
    def forward(
        self,
        state: torch.Tensor,
        action_mask: Optional[torch.Tensor] = None
    ) -> D.Categorical:
        """Computes action distribution conditioned on state and legality mask."""
        logits = self.net(state)
        if action_mask is not None:
            # Mask out illegal actions with a large negative number
            mask_bool = action_mask.bool()
            logits = torch.where(mask_bool, logits, torch.tensor(-1e9, device=logits.device))
        return D.Categorical(logits=logits)
        
    def get_action(
        self,
        state: np.ndarray,
        action_mask: Optional[np.ndarray] = None,
        deterministic: bool = False
    ) -> Tuple[int, float, float]:
        """Inference helper for numpy inputs. Returns (action, log_prob, entropy)."""
        self.eval()
        with torch.no_grad():
            s_tensor = torch.from_numpy(state).float().unsqueeze(0)
            m_tensor = torch.from_numpy(action_mask).unsqueeze(0) if action_mask is not None else None
            dist = self.forward(s_tensor, m_tensor)
            if deterministic:
                action = int(torch.argmax(dist.logits, dim=-1).item())
            else:
                action = int(dist.sample().item())
            log_prob = float(dist.log_prob(torch.tensor([action])).item())
            entropy = float(dist.entropy().item())
        return action, log_prob, entropy
        
    def evaluate_actions(
        self,
        states: torch.Tensor,
        actions: torch.Tensor,
        masks: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Evaluates batch of actions. Returns (log_probs, entropy)."""
        dist = self.forward(states, masks)
        log_probs = dist.log_prob(actions)
        entropy = dist.entropy()
        return log_probs, entropy
