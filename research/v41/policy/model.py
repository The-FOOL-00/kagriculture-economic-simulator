# SPDX-License-Identifier: MIT
"""Kagriculture V41 Temporal Recurrent Strategic Policy & Economic Value Model.

Architecture:
- MLP Feature Encoder (103 -> 128)
- Recurrent Temporal Core (GRU 128 hidden)
- Multi-Head Output:
  1. Advantage / Q-Head (128 -> 11): Predicts expected cash delta Q(s, a) = Cash(a) - Cash(0)
  2. Policy / Proposal Head (128 -> 11): Normalized action selection distribution
- Conservative Residual Gating: Defaults to 0 (baseline) unless predicted advantage > tau
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from research.v41.policy.observation import OBSERVATION_DIM
from research.v41.executor.safe_executor import NUM_INTERVENTIONS


class V41TemporalStrategicPolicy(nn.Module):
    """Temporal Recurrent Policy and Economic Advantage Value Estimator."""

    def __init__(
        self,
        obs_dim: int = OBSERVATION_DIM,
        hidden_dim: int = 128,
        num_actions: int = NUM_INTERVENTIONS
    ):
        super().__init__()
        self.obs_dim = obs_dim
        self.hidden_dim = hidden_dim
        self.num_actions = num_actions

        # Feature encoder
        self.encoder = nn.Sequential(
            nn.Linear(obs_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
        )

        # Recurrent temporal core
        self.gru = nn.GRU(hidden_dim, hidden_dim, batch_first=True)

        # Multi-Head Outputs
        # 1. Economic Advantage Head: Q(s, a) predicting cash delta relative to baseline
        self.q_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, num_actions)
        )

        # 2. Policy Head: proposal distribution over safe actions
        self.policy_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, num_actions)
        )

        # Baseline value V(s) head
        self.value_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )

    def init_hidden(self, batch_size: int = 1, device: Optional[torch.device] = None) -> torch.Tensor:
        dev = device if device is not None else next(self.parameters()).device
        return torch.zeros(1, batch_size, self.hidden_dim, device=dev)

    def forward(
        self,
        x: torch.Tensor,
        hx: Optional[torch.Tensor] = None,
        action_mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """Forward pass.
        Returns:
            q_values: [B, num_actions] (predicted cash deltas)
            logits: [B, num_actions] (masked policy logits)
            v_val: [B, 1] (baseline state value)
            hx: [1, B, hidden_dim] (updated recurrent hidden state)
        """
        # Ensure 3D tensor: [Batch, SeqLen, ObsDim]
        if x.dim() == 2:
            x = x.unsqueeze(1)

        batch_size = x.size(0)
        if hx is None:
            hx = self.init_hidden(batch_size, device=x.device)

        feat = self.encoder(x)
        out, hx = self.gru(feat, hx)
        last_out = out[:, -1, :]  # Take last sequence step

        q_vals = self.q_head(last_out)
        logits = self.policy_head(last_out)
        v_val = self.value_head(last_out)

        # Masking: illegal actions get -1e9 in logits and -9999 in Q
        if action_mask is not None:
            if action_mask.dim() == 1:
                action_mask = action_mask.unsqueeze(0)
            inv_mask = ~action_mask.bool()
            logits = logits.masked_fill(inv_mask, -1e9)
            q_vals = q_vals.masked_fill(inv_mask, -9999.0)

        return q_vals, logits, v_val, hx

    @torch.no_grad()
    def select_intervention(
        self,
        obs_vec: np.ndarray,
        action_mask: np.ndarray,
        hx: Optional[torch.Tensor] = None,
        confidence_threshold: float = 50.0,
        device: str = "cpu"
    ) -> Tuple[int, float, torch.Tensor]:
        """Conservative Residual Decision Rule:
        1. Predicts Q(s, a) for all legal safe actions.
        2. Action 0 (Golden Baseline) is default.
        3. Only selects a > 0 if Q(s, a) > confidence_threshold and action is safe.
        Returns: (selected_action, predicted_advantage, new_hx)
        """
        self.eval()
        t_obs = torch.tensor(obs_vec, dtype=torch.float32, device=device).unsqueeze(0).unsqueeze(0)
        t_mask = torch.tensor(action_mask, dtype=torch.bool, device=device).unsqueeze(0)

        q_vals, logits, _, new_hx = self.forward(t_obs, hx, action_mask=t_mask)
        q_np = q_vals.squeeze(0).cpu().numpy()

        # Find best candidate action a > 0
        best_a = 0
        best_q = 0.0

        for a_idx in range(1, self.num_actions):
            if action_mask[a_idx] and q_np[a_idx] > best_q:
                best_q = float(q_np[a_idx])
                best_a = a_idx

        # Residual gating: RL must earn the right to deviate
        if best_q >= confidence_threshold and best_a != 0:
            return best_a, best_q, new_hx
        else:
            return 0, 0.0, new_hx
