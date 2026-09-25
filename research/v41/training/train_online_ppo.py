# SPDX-License-Identifier: MIT
"""Kagriculture V41 Online Recurrent PPO with Baseline Anchor & Safety Masking.

Trains strategic intervention policy online against league population:
- Bootstraps from offline value & policy checkpoint
- Action execution strictly via StateAwareExecutor (Golden Property guaranteed)
- Dynamic legality & safety masking at every step
- Baseline KL regularization preventing catastrophic deviation
"""

from __future__ import annotations
import copy
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from research.v41.executor.safe_executor import StateAwareExecutor, NUM_INTERVENTIONS, INTERVENTION_NAMES
from research.v41.policy.observation import V41ObservationEncoder, OBSERVATION_DIM
from research.v41.policy.model import V41TemporalStrategicPolicy
from candidates.v32_rlx2.opponents import load_league_opponent

TRAIN_SEEDS = list(range(249635, 249655))
LEAGUE_OPPONENTS = ["E8_DMITRII", "E2_A7", "E0_V3", "SYN_AGG"]


class V41OnlinePPOTrainer:
    def __init__(
        self,
        checkpoint_path: Optional[str] = None,
        lr: float = 3e-4,
        gamma: float = 0.99,
        clip_ratio: float = 0.2,
        teacher_kl_coeff: float = 0.1,
        device: str = "cpu"
    ):
        self.device = device
        self.gamma = gamma
        self.clip_ratio = clip_ratio
        self.teacher_kl_coeff = teacher_kl_coeff

        self.policy = V41TemporalStrategicPolicy(
            obs_dim=OBSERVATION_DIM,
            hidden_dim=128,
            num_actions=NUM_INTERVENTIONS
        ).to(device)

        if checkpoint_path and os.path.exists(checkpoint_path):
            ckpt = torch.load(checkpoint_path, map_location=device)
            if "model_state_dict" in ckpt:
                self.policy.load_state_dict(ckpt["model_state_dict"])
            else:
                self.policy.load_state_dict(ckpt)
            print(f"Loaded online starting weights from {checkpoint_path}")

        # Frozen anchor model for KL regularization
        self.anchor_model = copy.deepcopy(self.policy).to(device)
        self.anchor_model.eval()

        self.optimizer = torch.optim.AdamW(self.policy.parameters(), lr=lr, weight_decay=1e-4)

    def train_iteration(
        self,
        seeds: List[int],
        opponents: List[str],
        ppo_epochs: int = 3
    ) -> Dict[str, float]:
        self.policy.eval()
        trajectories = []
        encoder = V41ObservationEncoder()
        executor = StateAwareExecutor()

        total_reward = 0.0
        total_episodes = 0
        total_interventions = 0

        # Rollout collection
        for seed in seeds:
            for opp_id in opponents:
                sim = FastKagricultureSim(seed=seed)
                opp = load_league_opponent(opp_id)
                encoder.reset()
                executor.reset()

                obs0, obs1 = sim.reset(seed=seed)
                hx = self.policy.init_hidden(1, device=self.device)

                ep_obs = []
                ep_masks = []
                ep_actions = []
                ep_logprobs = []
                ep_qvals = []

                while not sim.done:
                    step = int(obs0.get("step", 0) or 0)
                    obs_vec = encoder.encode(obs0, player=0)
                    mask = executor.get_safety_mask(obs0, player=0)

                    t_obs = torch.tensor(obs_vec, dtype=torch.float32, device=self.device).unsqueeze(0).unsqueeze(0)
                    t_mask = torch.tensor(mask, dtype=torch.bool, device=self.device).unsqueeze(0)

                    with torch.no_grad():
                        q_vals, logits, _, hx = self.policy(t_obs, hx, action_mask=t_mask)
                        probs = F.softmax(logits, dim=-1)
                        dist = torch.distributions.Categorical(probs)
                        action = dist.sample()
                        logprob = dist.log_prob(action)

                    act_idx = action.item()
                    if act_idx > 0:
                        total_interventions += 1

                    ep_obs.append(obs_vec)
                    ep_masks.append(mask)
                    ep_actions.append(act_idx)
                    ep_logprobs.append(logprob.item())
                    ep_qvals.append(q_vals.squeeze(0).cpu().numpy())

                    # Safe execution
                    act0 = executor.execute(act_idx, obs0, player=0)
                    act1 = opp(obs1)
                    [obs0, obs1], _, _, _ = sim.step([act0, act1])

                # Terminal episode payoff
                r0 = float(sim.state[0].reward or 0.0)
                r1 = float(sim.state[1].reward or 0.0)
                margin = r0 - r1
                total_reward += r0
                total_episodes += 1

                # Normalized return
                scaled_ret = margin / 20000.0

                trajectories.append({
                    "obs": np.array(ep_obs, dtype=np.float32),
                    "masks": np.array(ep_masks, dtype=bool),
                    "actions": np.array(ep_actions, dtype=np.int64),
                    "old_logprobs": np.array(ep_logprobs, dtype=np.float32),
                    "return": scaled_ret
                })

        # PPO Update
        self.policy.train()
        total_loss = 0.0

        for _ in range(ppo_epochs):
            for traj in trajectories:
                t_obs = torch.tensor(traj["obs"], dtype=torch.float32, device=self.device).unsqueeze(0)
                t_masks = torch.tensor(traj["masks"], dtype=torch.bool, device=self.device).unsqueeze(0)
                t_acts = torch.tensor(traj["actions"], dtype=torch.long, device=self.device)
                t_old_lp = torch.tensor(traj["old_logprobs"], dtype=torch.float32, device=self.device)
                ret = traj["return"]

                # Flatten sequence
                batch_obs = t_obs.squeeze(0)
                batch_masks = t_masks.squeeze(0)

                q_vals, logits, v_pred, _ = self.policy(batch_obs.unsqueeze(1), action_mask=batch_masks)
                probs = F.softmax(logits, dim=-1)
                dist = torch.distributions.Categorical(probs)
                new_lp = dist.log_prob(t_acts)

                # Ratio
                ratio = torch.exp(new_lp - t_old_lp)
                adv = ret  # episodic scalar advantage
                surr1 = ratio * adv
                surr2 = torch.clamp(ratio, 1.0 - self.clip_ratio, 1.0 + self.clip_ratio) * adv
                pi_loss = -torch.min(surr1, surr2).mean()

                # Teacher KL loss
                with torch.no_grad():
                    _, anchor_logits, _, _ = self.anchor_model(batch_obs.unsqueeze(1), action_mask=batch_masks)
                    anchor_probs = F.softmax(anchor_logits, dim=-1)

                kl_loss = F.kl_div(torch.log(probs + 1e-8), anchor_probs, reduction='batchmean')

                loss = pi_loss + self.teacher_kl_coeff * kl_loss

                self.optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.policy.parameters(), 1.0)
                self.optimizer.step()
                total_loss += loss.item()

        return {
            "mean_reward": total_reward / max(1, total_episodes),
            "total_interventions": total_interventions,
            "loss": total_loss / max(1, len(trajectories))
        }
