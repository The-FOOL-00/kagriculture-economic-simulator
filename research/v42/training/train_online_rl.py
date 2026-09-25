# SPDX-License-Identifier: MIT
"""Kagriculture V42 Online Recurrent RL Fine-Tuning.

Optimizes timing and sequencing of verified safe interventions:
- Initialized from offline alpha model checkpoint
- Teacher KL anchor to prevent policy drift
- Reward: Incremental Terminal Margin Delta with negative tail penalty
- Strict Zero-Touch on protected holdouts
- Saves champion to research/v42/checkpoints/v42_ppo_champion.pt
"""

import copy
import json
import os
import sys
import time
from typing import Any, Dict, List, Tuple
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from research.v42.executor.safe_executor import StateAwareExecutor, NUM_INTERVENTIONS, INTERVENTION_NAMES
from research.v42.policy.observation import V42ObservationEncoder
from research.v42.policy.alpha_model import V42TwoHeadAlphaModel
from candidates.v32_rlx2.opponents import load_league_opponent

TRAIN_SEEDS = [249635, 249636, 249637, 249638, 249640, 249644, 249648, 249650]
OPPONENTS = ["E8_DMITRII", "E2_A7", "E0_V3", "SYN_AGG"]

PROTECTED_RANGES = [
    (214200, 214249),
    (340090, 340199),
    (249695, 249734),
]


def assert_seed_safe(seed: int):
    for low, high in PROTECTED_RANGES:
        if low <= seed <= high:
            raise ValueError(f"FATAL: Attempted access to protected holdout seed {seed}!")


class OnlineRLTrainer:
    def __init__(self, lr: float = 3e-4, kl_coeff: float = 0.5):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.kl_coeff = kl_coeff

        # Learner policy
        self.policy = V42TwoHeadAlphaModel().to(self.device)
        ckpt_path = os.path.join(REPO_ROOT, "research", "v42", "checkpoints", "v42_alpha_model.pt")
        self.policy.load_state_dict(torch.load(ckpt_path, weights_only=False))

        # Teacher policy (frozen anchor)
        self.teacher = V42TwoHeadAlphaModel().to(self.device)
        self.teacher.load_state_dict(torch.load(ckpt_path, weights_only=False))
        self.teacher.eval()

        self.optimizer = torch.optim.AdamW(self.policy.parameters(), lr=lr, weight_decay=1e-4)
        self.encoder = V42ObservationEncoder()
        self.executor = StateAwareExecutor()
        self.opp_masters = {opp_id: load_league_opponent(opp_id) for opp_id in OPPONENTS}

    def train_iterations(self, num_iterations: int = 15):
        print("=" * 80)
        print("STARTING V42 ONLINE RL FINE-TUNING")
        print("=" * 80)

        history = []
        best_delta = -float("inf")
        t0 = time.perf_counter()

        for it in range(1, num_iterations + 1):
            seed = TRAIN_SEEDS[(it - 1) % len(TRAIN_SEEDS)]
            opp_id = OPPONENTS[(it - 1) % len(OPPONENTS)]
            assert_seed_safe(seed)

            # 1. Baseline rollout to get reference margin
            sim_base = FastKagricultureSim(seed=seed)
            v35_base = StateAwareExecutor()
            opp_b = copy.deepcopy(self.opp_masters[opp_id])
            ob0, ob1 = sim_base.reset(seed=seed)
            while not sim_base.done:
                [ob0, ob1], _, _, _ = sim_base.step([v35_base.execute(0, ob0, player=0), opp_b(ob1)])
            base_cash = ob0["farms"][0]["money"]
            base_margin = base_cash - ob1["farms"][1]["money"]
            base_win = base_margin > 0

            # 2. Online candidate rollout with policy sampling
            sim_cand = FastKagricultureSim(seed=seed)
            v35_cand = StateAwareExecutor()
            opp_c = copy.deepcopy(self.opp_masters[opp_id])
            self.encoder.reset()
            oc0, oc1 = sim_cand.reset(seed=seed)

            trajectory_obs = []
            trajectory_actions = []
            trajectory_masks = []
            prev_act = 0
            hx = None

            while not sim_cand.done:
                step = int(oc0.get("step", 0) or 0)
                mask = self.executor.get_safety_mask(oc0, player=0)

                # Restrict candidate actions strictly to verified safe actions (0, 1, 2, 8, 9)
                for a in (3, 4, 5, 6, 7):
                    mask[a] = False

                obs_vec = self.encoder.encode(oc0, player=0, prev_intervention=prev_act)

                # In near terminal window, sample action from LCB score distribution
                if (690 <= step <= 696) or (704 <= step <= 712):
                    obs_t = torch.tensor(obs_vec, dtype=torch.float32).unsqueeze(0).to(self.device)
                    act, score, diag, hx = self.policy.score_interventions(
                        obs=obs_t, mask=mask, hx=hx, beta=0.1, threshold=10.0
                    )
                    trajectory_obs.append(obs_vec)
                    trajectory_actions.append(act)
                    trajectory_masks.append(mask)
                    prev_act = act
                else:
                    act = 0
                    prev_act = 0

                act0 = v35_cand.execute(act, oc0, player=0)
                act1 = opp_c(oc1)
                [oc0, oc1], _, _, _ = sim_cand.step([act0, act1])

            cand_cash = oc0["farms"][0]["money"]
            cand_margin = cand_cash - oc1["farms"][1]["money"]
            cand_win = cand_margin > 0

            cash_delta = cand_cash - base_cash
            margin_delta = cand_margin - base_margin
            is_rescue = (not base_win) and cand_win
            is_cas = base_win and (not cand_win)

            # Reward formulation: Margin delta + rescue bonus - casualty penalty - negative tail penalty
            reward = margin_delta
            if is_rescue:
                reward += 500.0
            if is_cas:
                reward -= 2000.0
            if cash_delta < 0:
                reward -= abs(cash_delta) * 1.5

            # Policy update using policy gradient + Teacher KL penalty
            if trajectory_obs:
                obs_batch = torch.tensor(np.array(trajectory_obs), dtype=torch.float32).to(self.device)
                acts_batch = torch.tensor(trajectory_actions, dtype=torch.long).to(self.device)

                mu_cand, p_res, sig_cand, _ = self.policy(obs_batch)
                with torch.no_grad():
                    mu_teach, _, sig_teach, _ = self.teacher(obs_batch)

                # Advantage: reward / 100.0
                adv = torch.tensor(reward / 100.0, dtype=torch.float32).to(self.device)

                # Policy loss: push Q(s, a) toward realized reward
                pred_delta = mu_cand.gather(1, acts_batch.unsqueeze(1)).squeeze(1)
                policy_loss = F.mse_loss(pred_delta, adv.expand_as(pred_delta))

                # Teacher KL anchor on delta distribution: (mu_p - mu_t)^2 / (2 * sig_t^2)
                kl_loss = ((mu_cand - mu_teach) ** 2 / (2.0 * (sig_teach ** 2 + 1e-4))).mean()

                loss = policy_loss + self.kl_coeff * kl_loss

                self.optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.policy.parameters(), max_norm=1.0)
                self.optimizer.step()

                loss_val = loss.item()
            else:
                loss_val = 0.0

            history.append({
                "iteration": it,
                "seed": seed,
                "opp_id": opp_id,
                "reward": float(reward),
                "cash_delta": float(cash_delta),
                "margin_delta": float(margin_delta),
                "rescue": is_rescue,
                "casualty": is_cas,
                "loss": loss_val
            })

            print(f"Iter {it:2d}/{num_iterations} | Seed {seed} vs {opp_id:<10} | dCash: ${cash_delta:>+7.1f} | dMargin: ${margin_delta:>+7.1f} | Reward: ${reward:>+7.1f} | Res: {int(is_rescue)} | Cas: {int(is_cas)}")

            if cash_delta >= best_delta and not is_cas:
                best_delta = cash_delta
                champion_path = os.path.join(REPO_ROOT, "research", "v42", "checkpoints", "v42_ppo_champion.pt")
                torch.save(self.policy.state_dict(), champion_path)

        dur = time.perf_counter() - t0
        mean_delta = np.mean([h["cash_delta"] for h in history])
        total_rescues = sum(1 for h in history if h["rescue"])
        total_cas = sum(1 for h in history if h["casualty"])

        print(f"\nOnline RL Complete in {dur:.1f}s.")
        print(f"Mean Online Cash Delta: ${mean_delta:>+8.2f} | Rescues: {total_rescues} | Casualties: {total_cas}")
        print(f"Champion checkpoint saved to {champion_path}")

        # Save metrics artifact
        out_json = os.path.join(REPO_ROOT, "research", "v42", "artifacts", "online_rl_metrics.json")
        with open(out_json, "w") as f:
            json.dump(history, f, indent=2)

        return history


if __name__ == "__main__":
    trainer = OnlineRLTrainer()
    trainer.train_iterations(num_iterations=16)
