# SPDX-License-Identifier: MIT
"""Kagriculture V41 Offline Strategic Advantage & Policy Learner.

Trains V41TemporalStrategicPolicy on exact counterfactual simulation data:
1. Q-Head: learns exact expected cash deltas Q(s, a) = Cash(a) - Cash(0)
2. Policy-Head: learns advantageous action proposals via Advantage-Weighted Regression
3. Evaluates oracle agreement, regret, and false-positive intervention rates
"""

from __future__ import annotations
import json
import os
import sys
import time
from typing import Any, Dict, List, Tuple
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v41.policy.model import V41TemporalStrategicPolicy
from research.v41.policy.observation import OBSERVATION_DIM
from research.v41.executor.safe_executor import NUM_INTERVENTIONS, INTERVENTION_NAMES


class CounterfactualDataset(Dataset):
    def __init__(self, data: List[Dict[str, Any]]):
        self.data = data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        obs = torch.tensor(item["obs"], dtype=torch.float32)
        mask = torch.tensor(item["mask"], dtype=torch.bool)
        deltas = torch.tensor(item["deltas"], dtype=torch.float32)
        best_a = torch.tensor(item["best_action"], dtype=torch.long)
        best_d = torch.tensor(item["best_delta"], dtype=torch.float32)
        return obs, mask, deltas, best_a, best_d


def train_offline_policy(
    dataset_path: str,
    epochs: int = 35,
    batch_size: int = 32,
    lr: float = 1e-3,
    device: str = "cpu"
) -> Dict[str, Any]:
    print(f"Loading counterfactual dataset from {dataset_path}...")
    raw_data = torch.load(dataset_path, map_location="cpu", weights_only=False)
    print(f"Loaded {len(raw_data)} transitions.")

    # Train / Val split (80 / 20)
    n_val = max(10, int(len(raw_data) * 0.20))
    n_train = len(raw_data) - n_val
    train_data = raw_data[:n_train]
    val_data = raw_data[n_train:]

    train_loader = DataLoader(CounterfactualDataset(train_data), batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(CounterfactualDataset(val_data), batch_size=batch_size, shuffle=False)

    model = V41TemporalStrategicPolicy(
        obs_dim=OBSERVATION_DIM,
        hidden_dim=128,
        num_actions=NUM_INTERVENTIONS
    ).to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    q_criterion = nn.SmoothL1Loss(beta=100.0)

    best_val_loss = float("inf")
    best_oracle_acc = 0.0
    checkpoint_dir = os.path.join(REPO_ROOT, "research", "v41", "checkpoints")
    os.makedirs(checkpoint_dir, exist_ok=True)
    best_model_path = os.path.join(checkpoint_dir, "v41_offline_model.pt")

    history = []

    print("\n--- Training V41 Strategic Value & Policy Model ---")
    for epoch in range(1, epochs + 1):
        model.train()
        train_q_loss = 0.0
        train_pi_loss = 0.0
        correct_proposals = 0
        total_train = 0

        for obs, mask, deltas, best_a, best_d in train_loader:
            obs = obs.to(device)
            mask = mask.to(device)
            deltas = deltas.to(device)
            best_a = best_a.to(device)
            best_d = best_d.to(device)

            optimizer.zero_grad()
            q_vals, logits, _, _ = model(obs, action_mask=mask)

            # 1. Q-loss on legal actions
            # Scale deltas to hundreds for balanced gradients
            legal_mask = mask.float()
            scaled_target = torch.clamp(deltas / 100.0, -50.0, 50.0)
            scaled_pred = q_vals / 100.0

            q_loss = (q_criterion(scaled_pred, scaled_target) * legal_mask).sum() / torch.clamp(legal_mask.sum(), min=1.0)

            # 2. Advantage-Weighted Policy Loss
            # Weight cross-entropy by positive advantage
            adv_weights = torch.clamp(best_d / 500.0, min=0.1, max=10.0)
            pi_loss = (F.cross_entropy(logits, best_a, reduction='none') * adv_weights).mean()

            total_loss = q_loss + 0.5 * pi_loss
            total_loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

            train_q_loss += q_loss.item() * len(obs)
            train_pi_loss += pi_loss.item() * len(obs)
            pred_a = logits.argmax(dim=-1)
            correct_proposals += (pred_a == best_a).sum().item()
            total_train += len(obs)

        train_q_loss /= max(1, total_train)
        train_pi_loss /= max(1, total_train)
        train_acc = correct_proposals / max(1, total_train)

        # Validation
        model.eval()
        val_q_loss = 0.0
        val_correct = 0
        val_total = 0
        total_regret = 0.0

        with torch.no_grad():
            for obs, mask, deltas, best_a, best_d in val_loader:
                obs = obs.to(device)
                mask = mask.to(device)
                deltas = deltas.to(device)
                best_a = best_a.to(device)
                best_d = best_d.to(device)

                q_vals, logits, _, _ = model(obs, action_mask=mask)
                legal_mask = mask.float()
                scaled_target = torch.clamp(deltas / 100.0, -50.0, 50.0)
                scaled_pred = q_vals / 100.0

                q_loss = (q_criterion(scaled_pred, scaled_target) * legal_mask).sum() / torch.clamp(legal_mask.sum(), min=1.0)
                val_q_loss += q_loss.item() * len(obs)

                pred_a = logits.argmax(dim=-1)
                val_correct += (pred_a == best_a).sum().item()
                val_total += len(obs)

                # Economic regret = outcome(best safe) - outcome(pred)
                batch_deltas = deltas.cpu().numpy()
                for b_i in range(len(obs)):
                    opt_delta = float(batch_deltas[b_i, best_a[b_i].item()])
                    chosen_a = pred_a[b_i].item()
                    chosen_delta = float(batch_deltas[b_i, chosen_a]) if mask[b_i, chosen_a] else 0.0
                    regret = max(0.0, opt_delta - chosen_delta)
                    total_regret += regret

        val_q_loss /= max(1, val_total)
        val_acc = val_correct / max(1, val_total)
        mean_regret = total_regret / max(1, val_total)

        if epoch % 5 == 0 or epoch == epochs or val_acc > best_oracle_acc:
            print(f"Epoch {epoch:02d} | Train Q-Loss: {train_q_loss:.4f} | Val Q-Loss: {val_q_loss:.4f} | Val Oracle Acc: {val_acc*100:.1f}% | Mean Regret: ${mean_regret:.1f}")

        if val_acc > best_oracle_acc or (val_acc == best_oracle_acc and val_q_loss < best_val_loss):
            best_oracle_acc = val_acc
            best_val_loss = val_q_loss
            torch.save({
                "model_state_dict": model.state_dict(),
                "epoch": epoch,
                "val_acc": val_acc,
                "val_q_loss": val_q_loss,
                "mean_regret": mean_regret
            }, best_model_path)

        history.append({
            "epoch": epoch,
            "train_q_loss": train_q_loss,
            "val_q_loss": val_q_loss,
            "val_oracle_acc": val_acc,
            "mean_regret": mean_regret
        })

    print(f"\nBest Validation Oracle Accuracy: {best_oracle_acc*100:.1f}%")
    print(f"Saved champion offline model to: {best_model_path}")

    return {
        "best_model_path": best_model_path,
        "best_oracle_acc": best_oracle_acc,
        "best_val_loss": best_val_loss,
        "history": history
    }


if __name__ == "__main__":
    ds_path = os.path.join(REPO_ROOT, "research", "v41", "artifacts", "counterfactual_dataset.pt")
    if os.path.exists(ds_path):
        train_offline_policy(ds_path)
    else:
        print(f"Waiting for dataset at {ds_path}...")
