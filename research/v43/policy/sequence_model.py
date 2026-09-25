# SPDX-License-Identifier: MIT
"""Kagriculture V43 Multi-Step Sequence Value & Uncertainty Model.

Predicts economic outcomes for candidate action sequences:
- Architecture:
  * State Encoder: Linear(106 -> 128) + LayerNorm + ReLU + Linear(128 -> 128)
  * Sequence Embedding: Embedding(NUM_ACTIONS, 32) + GRU/Linear encoder for action sequence
  * Fused Latent Representation
  * Head 1: Expected Terminal Cash Delta mu(s, seq)
  * Head 2: Rescue Probability P(rescue | s, seq) (Sigmoid)
  * Head 3: Uncertainty / Variance sigma(s, seq) (Softplus)
- Risk-Gated Evaluation:
  Score(s, seq) = mu(s, seq) - beta * sigma(s, seq) + lambda_res * P(rescue)
  Accepts composite sequence only if Score >= Threshold > 0.
  Otherwise fails closed to Baseline.
"""

from __future__ import annotations
import os
import sys
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v42.policy.observation import OBSERVATION_DIM
from research.v43.executor.v43_executor import NUM_V43_INTERVENTIONS, V43_INTERVENTION_NAMES

MAX_SEQUENCE_LEN = 3


class V43SequenceAlphaModel(nn.Module):
    """Deep sequence advantage and uncertainty model."""

    def __init__(
        self,
        obs_dim: int = OBSERVATION_DIM,
        hidden_dim: int = 128,
        action_dim: int = NUM_V43_INTERVENTIONS,
        action_embed_dim: int = 32
    ):
        super().__init__()
        self.obs_dim = obs_dim
        self.hidden_dim = hidden_dim
        self.action_dim = action_dim
        self.action_embed_dim = action_embed_dim

        # State feature encoder
        self.state_encoder = nn.Sequential(
            nn.Linear(obs_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU()
        )

        # Action embedding layer
        self.action_embedding = nn.Embedding(action_dim, action_embed_dim)

        # Sequence encoder (combining action sequence tokens)
        self.seq_gru = nn.GRU(
            input_size=action_embed_dim,
            hidden_size=hidden_dim,
            batch_first=True
        )

        # Fusion layer combining state representation + sequence representation
        self.fusion = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU()
        )

        # Value Head 1: Expected Terminal Cash Delta ($100 units)
        self.delta_head = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 1)
        )

        # Value Head 2: Match Rescue Probability (Logits)
        self.rescue_head = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 1)
        )

        # Value Head 3: Prediction Standard Deviation (Uncertainty)
        self.sigma_head = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Softplus()
        )

    def forward(
        self,
        obs: torch.Tensor,
        action_seq: torch.Tensor  # [batch, seq_len]
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Forward pass predicting outcome of action_seq starting from obs.
        Returns: (delta_mean, rescue_prob, sigma)
        """
        # Encode state: [batch, hidden_dim]
        state_repr = self.state_encoder(obs)

        # Embed action sequence: [batch, seq_len, embed_dim]
        act_emb = self.action_embedding(action_seq)
        _, seq_h = self.seq_gru(act_emb)
        seq_repr = seq_h.squeeze(0)  # [batch, hidden_dim]

        # Fuse state and sequence: [batch, hidden_dim * 2] -> [batch, hidden_dim]
        fused = self.fusion(torch.cat([state_repr, seq_repr], dim=-1))

        delta_mean = self.delta_head(fused).squeeze(-1)
        rescue_logits = self.rescue_head(fused).squeeze(-1)
        rescue_prob = torch.sigmoid(rescue_logits)
        sigma = self.sigma_head(fused).squeeze(-1) + 1e-3

        return delta_mean, rescue_prob, sigma

    def score_sequence(
        self,
        obs_vec: np.ndarray,
        action_seq: List[int],
        beta: float = 1.0,
        threshold: float = 15.0,
        rescue_bonus: float = 50.0
    ) -> Tuple[float, float, float, float, bool]:
        """Scores candidate sequence under Lower Confidence Bound (LCB).
        Returns: (lcb_score, mu_dollars, sigma_dollars, p_rescue, is_accepted)
        """
        self.eval()
        with torch.no_grad():
            obs_t = torch.tensor(obs_vec, dtype=torch.float32).unsqueeze(0)
            seq_t = torch.tensor(action_seq, dtype=torch.long).unsqueeze(0)

            delta_norm, p_res, sig_norm = self.forward(obs_t, seq_t)

            mu = float(delta_norm.item()) * 100.0  # dollars
            sig = float(sig_norm.item()) * 100.0  # dollars
            p_rescue = float(p_res.item())

            # If pure baseline (all 0s), score is strictly 0.0
            if all(a == 0 for a in action_seq):
                return 0.0, 0.0, 0.0, 0.0, False

            lcb = mu - (beta * sig) + (rescue_bonus * p_rescue)
            accepted = (lcb >= threshold) and (mu > 0)

            return lcb, mu, sig, p_rescue, accepted
