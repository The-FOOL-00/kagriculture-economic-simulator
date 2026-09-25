# SPDX-License-Identifier: MIT
"""Kagriculture V42 Two-Head Uncertainty-Aware Economic Advantage Model.

Predicts:
- Head 1: Expected Terminal Cash Delta mu(s, a)
- Head 2: Probability of Match Rescue P(rescue | s, a)
- Uncertainty Head: Prediction standard deviation sigma(s, a)

Gating Mechanism:
Score(s, a) = mu(s, a) - beta * sigma(s, a) + lambda_res * P(rescue)
Intervention is accepted ONLY if max Score(s, a) > threshold > 0.
Otherwise fails closed to Baseline (Action 0).
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

from research.v42.executor.safe_executor import NUM_INTERVENTIONS
from research.v42.policy.observation import OBSERVATION_DIM


class V42TwoHeadAlphaModel(nn.Module):
    """Two-head recurrent economic advantage and uncertainty model."""

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

        # Recurrent temporal model
        self.gru = nn.GRU(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            batch_first=True
        )

        # Head 1: Terminal Cash Delta Mean Head
        self.delta_head = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Linear(64, num_actions)
        )

        # Head 2: Rescue Probability Head (Logits)
        self.rescue_head = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Linear(64, num_actions)
        )

        # Head 3: Uncertainty / Variance Head (Standard Deviation)
        self.sigma_head = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Linear(64, num_actions),
            nn.Softplus()  # Ensures strictly positive standard deviation
        )

    def forward(
        self,
        obs: torch.Tensor,
        hx: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """Forward pass.
        obs shape: [batch, seq_len, obs_dim] or [batch, obs_dim]
        Returns: (delta_mean, rescue_probs, sigma, new_hx)
        """
        is_2d = (obs.dim() == 2)
        if is_2d:
            obs = obs.unsqueeze(1)  # [batch, 1, obs_dim]

        emb = self.encoder(obs)
        gru_out, new_hx = self.gru(emb, hx)

        delta_mean = self.delta_head(gru_out)
        rescue_logits = self.rescue_head(gru_out)
        rescue_probs = torch.sigmoid(rescue_logits)
        sigma = self.sigma_head(gru_out) + 1e-3

        if is_2d:
            delta_mean = delta_mean.squeeze(1)
            rescue_probs = rescue_probs.squeeze(1)
            sigma = sigma.squeeze(1)

        return delta_mean, rescue_probs, sigma, new_hx

    def score_interventions(
        self,
        obs: torch.Tensor,
        mask: np.ndarray,
        hx: Optional[torch.Tensor] = None,
        beta: float = 1.0,
        threshold: float = 15.0,
        rescue_weight: float = 50.0
    ) -> Tuple[int, float, Dict[str, Any], torch.Tensor]:
        """Computes risk-gated action selection using Lower Confidence Bound.
        Returns: (selected_action, best_score, diagnostics, new_hx)
        """
        self.eval()
        with torch.no_grad():
            if not isinstance(obs, torch.Tensor):
                obs = torch.tensor(obs, dtype=torch.float32).unsqueeze(0)
            elif obs.dim() == 1:
                obs = obs.unsqueeze(0)

            delta_mean, rescue_probs, sigma, new_hx = self.forward(obs, hx)

            # Rescale predictions to dollars ($100 = 1.0 unit in training)
            mu = delta_mean.cpu().numpy()[0] * 100.0
            sig = sigma.cpu().numpy()[0] * 100.0
            p_res = rescue_probs.cpu().numpy()[0]

            # Lower Confidence Bound score: mu - beta * sigma + rescue_bonus
            lcb_score = mu - (beta * sig) + (rescue_weight * p_res)
            # Baseline (Action 0) is reference point with score 0.0
            lcb_score[0] = 0.0

            # Apply legality mask
            for a in range(self.num_actions):
                if not mask[a]:
                    lcb_score[a] = -99999.0

            best_a = int(np.argmax(lcb_score))
            best_score = float(lcb_score[best_a])

            # Gating condition: must exceed confidence threshold
            if best_a != 0 and best_score >= threshold:
                selected_action = best_a
            else:
                selected_action = 0  # Fallback to Baseline

            diag = {
                "mu": mu,
                "sigma": sig,
                "p_rescue": p_res,
                "lcb_scores": lcb_score,
                "selected": selected_action,
                "gated_score": best_score
            }

            return selected_action, best_score, diag, new_hx
