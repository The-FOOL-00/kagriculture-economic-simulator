# SPDX-License-Identifier: MIT
"""Kagriculture V32 RL-X2 Value Network (Critic).

Estimates state value V(s) with LayerNorm and orthogonal initialization.
"""

from __future__ import annotations
import torch
import torch.nn as nn
import numpy as np


class StrategicCritic(nn.Module):
    """Feedforward strategic state-value critic."""
    
    def __init__(self, state_dim: int, hidden_dim: int = 256):
        super().__init__()
        self.state_dim = state_dim
        
        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.LayerNorm(hidden_dim // 2),
            nn.Tanh(),
            nn.Linear(hidden_dim // 2, 1),
        )
        
        self._init_weights()
        
    def _init_weights(self):
        for m in self.net.modules():
            if isinstance(m, nn.Linear):
                nn.init.orthogonal_(m.weight, gain=np.sqrt(2))
                nn.init.constant_(m.bias, 0.0)
        final_layer = self.net[-1]
        nn.init.orthogonal_(final_layer.weight, gain=1.0)
        
    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """Estimates scalar state value V(s)."""
        return self.net(state).squeeze(-1)
        
    def get_value(self, state: np.ndarray) -> float:
        """Inference helper for single numpy state."""
        self.eval()
        with torch.no_grad():
            s_tensor = torch.from_numpy(state).float().unsqueeze(0)
            val = self.forward(s_tensor).item()
        return float(val)
