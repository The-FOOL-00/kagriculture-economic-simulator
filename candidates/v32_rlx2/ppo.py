# SPDX-License-Identifier: MIT
"""Kagriculture V32 RL-X2 Proximal Policy Optimization (PPO) Engine.

Production-grade PPO with Generalized Advantage Estimation (GAE),
advantage normalization, clipped surrogate objective, value loss clipping,
entropy control, and comprehensive training diagnostics.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np

try:
    from rlx2_config import RLX2Config
    from policy import StrategicActor
    from value import StrategicCritic
except ImportError:
    from candidates.v32_rlx2.rlx2_config import RLX2Config
    from candidates.v32_rlx2.policy import StrategicActor
    from candidates.v32_rlx2.value import StrategicCritic


@dataclass
class RolloutBatch:
    states: np.ndarray        # [N, state_dim]
    actions: np.ndarray       # [N]
    log_probs: np.ndarray     # [N]
    rewards: np.ndarray       # [N]
    values: np.ndarray        # [N]
    dones: np.ndarray         # [N]
    masks: np.ndarray         # [N, action_dim]
    advantages: Optional[np.ndarray] = None
    returns: Optional[np.ndarray] = None


def compute_gae(
    rewards: np.ndarray,
    values: np.ndarray,
    dones: np.ndarray,
    next_value: float = 0.0,
    gamma: float = 0.99,
    lam: float = 0.95
) -> Tuple[np.ndarray, np.ndarray]:
    """Computes Generalized Advantage Estimation (GAE) and returns."""
    T = len(rewards)
    advantages = np.zeros(T, dtype=np.float32)
    last_gae = 0.0
    
    for t in reversed(range(T)):
        if t == T - 1:
            next_non_terminal = 1.0 - float(dones[t])
            next_val = next_value
        else:
            next_non_terminal = 1.0 - float(dones[t])
            next_val = values[t + 1]
            
        delta = rewards[t] + gamma * next_val * next_non_terminal - values[t]
        last_gae = delta + gamma * lam * next_non_terminal * last_gae
        advantages[t] = last_gae
        
    returns = advantages + values
    return advantages, returns


def explained_variance(y_pred: np.ndarray, y_true: np.ndarray) -> float:
    """Computes fraction of variance explained by value predictions: 1 - Var(y - y_hat) / Var(y)."""
    var_y = np.var(y_true)
    return float(np.nan if var_y == 0 else 1 - np.var(y_true - y_pred) / var_y)


class StrategicPPO:
    """Proximal Policy Optimization trainer for RL-X2."""
    
    def __init__(
        self,
        actor: StrategicActor,
        critic: StrategicCritic,
        config: Optional[RLX2Config] = None,
        lr: float = 3e-4
    ):
        self.cfg = config or RLX2Config()
        self.actor = actor
        self.critic = critic
        self.device = torch.device(self.cfg.device)
        
        self.actor.to(self.device)
        self.critic.to(self.device)
        
        self.actor_optimizer = optim.Adam(self.actor.parameters(), lr=lr, eps=1e-5)
        self.critic_optimizer = optim.Adam(self.critic.parameters(), lr=lr * 2.0, eps=1e-5)
        
    def train_step(
        self,
        batch: RolloutBatch,
        epochs: int = 4,
        minibatch_size: int = 64,
        clip_eps: Optional[float] = None,
        vf_coef: Optional[float] = None,
        ent_coef: Optional[float] = None
    ) -> Dict[str, float]:
        """Performs PPO update epochs over rollout batch."""
        clip_eps = clip_eps or self.cfg.clip_epsilon
        vf_coef = vf_coef or self.cfg.vf_coef
        ent_coef = ent_coef or self.cfg.ent_coef
        
        # Tensor conversion
        b_states = torch.from_numpy(batch.states).float().to(self.device)
        b_actions = torch.from_numpy(batch.actions).long().to(self.device)
        b_old_log_probs = torch.from_numpy(batch.log_probs).float().to(self.device)
        b_masks = torch.from_numpy(batch.masks).to(self.device)
        b_returns = torch.from_numpy(batch.returns).float().to(self.device)
        b_adv = torch.from_numpy(batch.advantages).float().to(self.device)
        
        # Advantage normalization
        b_adv = (b_adv - b_adv.mean()) / (b_adv.std() + 1e-8)
        
        N = len(batch.states)
        clip_fractions = []
        approx_kls = []
        pg_losses = []
        v_losses = []
        entropies = []
        
        self.actor.train()
        self.critic.train()
        
        for epoch in range(epochs):
            indices = np.random.permutation(N)
            for start in range(0, N, minibatch_size):
                end = min(start + minibatch_size, N)
                mb_idx = indices[start:end]
                
                mb_s = b_states[mb_idx]
                mb_a = b_actions[mb_idx]
                mb_old_lp = b_old_log_probs[mb_idx]
                mb_m = b_masks[mb_idx]
                mb_ret = b_returns[mb_idx]
                mb_adv = b_adv[mb_idx]
                
                # 1. Actor loss
                new_lp, entropy = self.actor.evaluate_actions(mb_s, mb_a, mb_m)
                ratio = torch.exp(new_lp - mb_old_lp)
                
                surr1 = ratio * mb_adv
                surr2 = torch.clamp(ratio, 1.0 - clip_eps, 1.0 + clip_eps) * mb_adv
                pg_loss = -torch.min(surr1, surr2).mean()
                
                # 2. Critic loss
                new_val = self.critic(mb_s)
                v_loss = nn.functional.mse_loss(new_val, mb_ret)
                
                # 3. Total Loss & Optimization
                total_loss = pg_loss + vf_coef * v_loss - ent_coef * entropy.mean()
                
                self.actor_optimizer.zero_grad()
                self.critic_optimizer.zero_grad()
                total_loss.backward()
                
                nn.utils.clip_grad_norm_(self.actor.parameters(), self.cfg.max_grad_norm)
                nn.utils.clip_grad_norm_(self.critic.parameters(), self.cfg.max_grad_norm)
                
                self.actor_optimizer.step()
                self.critic_optimizer.step()
                
                # Telemetry
                with torch.no_grad():
                    clip_frac = float(((ratio - 1.0).abs() > clip_eps).float().mean().item())
                    approx_kl = float(((ratio - 1.0) - torch.log(ratio)).mean().item())
                    clip_fractions.append(clip_frac)
                    approx_kls.append(approx_kl)
                    pg_losses.append(float(pg_loss.item()))
                    v_losses.append(float(v_loss.item()))
                    entropies.append(float(entropy.mean().item()))
                    
        exp_var = explained_variance(batch.values, batch.returns)
        
        return {
            "pg_loss": float(np.mean(pg_losses)),
            "v_loss": float(np.mean(v_losses)),
            "entropy": float(np.mean(entropies)),
            "clip_fraction": float(np.mean(clip_fractions)),
            "approx_kl": float(np.mean(approx_kls)),
            "explained_variance": exp_var
        }
