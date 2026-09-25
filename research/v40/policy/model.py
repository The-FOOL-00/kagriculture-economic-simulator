# SPDX-License-Identifier: MIT
"""Kagriculture V40 Recurrent Strategic Actor-Critic Network.

Architecture:
1. Feature Preprocessing & MLP Encoder: 112 -> 128
2. Recurrent Temporal State Encoder: GRU / LSTM (hidden_size = 128)
3. Strategic Policy Head: 16 masked discrete action logits
4. Multi-Objective Critic & Auxiliary Heads:
   - Primary Value Head (scalar expected return)
   - Margin Prediction Head (expected terminal cash difference)
   - Win Probability Head (sigmoid P(win))
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions.categorical import Categorical

from research.v40.policy.observation import OBSERVATION_DIM
from research.v40.policy.actions import NUM_MACRO_ACTIONS


class V40RecurrentActorCritic(nn.Module):
    """Recurrent Strategic Actor-Critic Network for Kagriculture Macro Economics."""

    def __init__(
        self,
        obs_dim: int = OBSERVATION_DIM,
        num_actions: int = NUM_MACRO_ACTIONS,
        hidden_dim: int = 128,
        rnn_type: str = "GRU"
    ):
        super().__init__()
        self.obs_dim = obs_dim
        self.num_actions = num_actions
        self.hidden_dim = hidden_dim
        self.rnn_type = rnn_type.upper()

        # 1. MLP Observation Encoder
        self.encoder = nn.Sequential(
            nn.Linear(obs_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU()
        )

        # 2. Recurrent Core (GRU or LSTM)
        if self.rnn_type == "LSTM":
            self.rnn = nn.LSTM(hidden_dim, hidden_dim, batch_first=True)
        else:
            self.rnn = nn.GRU(hidden_dim, hidden_dim, batch_first=True)

        # 3. Policy Head (Masked Macro Action Categorical Logits)
        self.actor = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, num_actions)
        )

        # 4. Value Heads
        # Primary Return Value Head
        self.critic = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )

        # Auxiliary Margin Head (predicts terminal cash delta in $10k units)
        self.margin_head = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 1)
        )

        # Auxiliary Win Probability Head (predicts P(win))
        self.win_head = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 1)
        )

    def initial_state(self, batch_size: int = 1, device: Optional[torch.device] = None) -> Any:
        """Returns zero-initialized hidden state."""
        dev = device or next(self.parameters()).device
        if self.rnn_type == "LSTM":
            h = torch.zeros(1, batch_size, self.hidden_dim, device=dev)
            c = torch.zeros(1, batch_size, self.hidden_dim, device=dev)
            return (h, c)
        else:
            return torch.zeros(1, batch_size, self.hidden_dim, device=dev)

    def forward_step(
        self,
        obs: torch.Tensor,
        action_mask: torch.Tensor,
        rnn_state: Any,
        deterministic: bool = False
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, Any, Dict[str, torch.Tensor]]:
        """Single-step rollout forward pass.
        
        Args:
            obs: (B, obs_dim) float tensor
            action_mask: (B, num_actions) boolean tensor
            rnn_state: recurrent state
            deterministic: greedy argmax if True, else sample
            
        Returns:
            action: (B,) long tensor
            log_prob: (B,) float tensor
            entropy: (B,) float tensor
            value: (B,) float tensor
            next_rnn_state: updated recurrent state
            aux: dict of auxiliary predictions (p_win, margin)
        """
        # Encode features
        feats = self.encoder(obs)  # (B, H)
        feats_seq = feats.unsqueeze(1)  # (B, 1, H)

        # RNN Step
        rnn_out, next_rnn_state = self.rnn(feats_seq, rnn_state)
        core_out = rnn_out.squeeze(1)  # (B, H)

        # Compute masked logits
        raw_logits = self.actor(core_out)
        very_negative = -1e9
        masked_logits = torch.where(action_mask, raw_logits, torch.full_like(raw_logits, very_negative))

        dist = Categorical(logits=masked_logits)
        if deterministic:
            action = torch.argmax(masked_logits, dim=-1)
        else:
            action = dist.sample()

        log_prob = dist.log_prob(action)
        entropy = dist.entropy()

        # Critic and auxiliary heads
        value = self.critic(core_out).squeeze(-1)
        margin = self.margin_head(core_out).squeeze(-1)
        p_win = torch.sigmoid(self.win_head(core_out)).squeeze(-1)

        aux = {"margin": margin, "p_win": p_win}
        return action, log_prob, entropy, value, next_rnn_state, aux

    def evaluate_sequence(
        self,
        obs_seq: torch.Tensor,
        mask_seq: torch.Tensor,
        action_seq: torch.Tensor,
        initial_rnn_state: Any,
        dones_seq: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, Dict[str, torch.Tensor]]:
        """Evaluates batch of sequences for recurrent PPO loss computation.
        
        Args:
            obs_seq: (B, T, obs_dim)
            mask_seq: (B, T, num_actions)
            action_seq: (B, T)
            initial_rnn_state: initial recurrent state
            dones_seq: (B, T) boolean episode boundaries
            
        Returns:
            log_probs: (B, T)
            values: (B, T)
            entropy: (B, T)
            aux: dict of sequence predictions
        """
        B, T, _ = obs_seq.shape
        obs_flat = obs_seq.view(B * T, -1)
        feats_flat = self.encoder(obs_flat)
        feats_seq = feats_flat.view(B, T, -1)

        # In standard unrolled training without mid-batch reset:
        rnn_out, _ = self.rnn(feats_seq, initial_rnn_state)
        out_flat = rnn_out.contiguous().view(B * T, -1)

        raw_logits = self.actor(out_flat).view(B, T, self.num_actions)
        very_negative = -1e9
        masked_logits = torch.where(mask_seq, raw_logits, torch.full_like(raw_logits, very_negative))

        dist = Categorical(logits=masked_logits)
        log_probs = dist.log_prob(action_seq)
        entropy = dist.entropy()

        values = self.critic(out_flat).view(B, T)
        margin = self.margin_head(out_flat).view(B, T)
        p_win = torch.sigmoid(self.win_head(out_flat)).view(B, T)

        aux = {"margin": margin, "p_win": p_win}
        return log_probs, values, entropy, aux
