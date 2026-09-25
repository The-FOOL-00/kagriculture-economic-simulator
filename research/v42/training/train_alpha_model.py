# SPDX-License-Identifier: MIT
"""Kagriculture V42 - Calibrated Training Script for Two-Head Uncertainty-Aware Alpha Model.

Trains:
- delta_head: Calibrated Gaussian NLL loss on scaled cash deltas (scale = $100)
- rescue_head: Binary Cross Entropy for match rescue probability
- Strict complete-game train/val partition (12 train seeds, 4 val seeds)
- Saves checkpoint to research/v42/checkpoints/v42_alpha_model.pt
"""

import os
import sys
import time
import json
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v42.policy.alpha_model import V42TwoHeadAlphaModel
from research.v42.executor.safe_executor import NUM_INTERVENTIONS, INTERVENTION_NAMES

# Complete-game partition: 12 training seeds, 4 validation seeds
VAL_SEEDS = [249647, 249648, 249649, 249650]
DELTA_SCALE = 100.0  # $100 = 1.0 unit for stable regression


class AlphaDataset(Dataset):
    def __init__(self, samples):
        self.samples = samples

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        s = self.samples[idx]
        return {
            "obs": torch.tensor(s["obs"], dtype=torch.float32),
            "mask": torch.tensor(s["mask"], dtype=torch.bool),
            "delta_cash": torch.tensor(s["delta_cash"], dtype=torch.float32),
            "rescue": torch.tensor(s["rescue"], dtype=torch.float32),
            "best_action": s["best_action"],
            "seed": s["seed"]
        }


def train_model(epochs: int = 40, batch_size: int = 64, lr: float = 1e-3):
    print("=" * 80)
    print("TRAINING V42 TWO-HEAD UNCERTAINTY-AWARE ALPHA MODEL (CALIBRATED)")
    print("=" * 80)

    dataset_path = os.path.join(REPO_ROOT, "research", "v42", "artifacts", "v42_alpha_dataset.pt")
    data = torch.load(dataset_path, weights_only=False)

    train_samples = [s for s in data if s["seed"] not in VAL_SEEDS]
    val_samples = [s for s in data if s["seed"] in VAL_SEEDS]

    print(f"Loaded {len(data)} total samples: {len(train_samples)} Train, {len(val_samples)} Validation (Complete-Game Split)")

    train_loader = DataLoader(AlphaDataset(train_samples), batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(AlphaDataset(val_samples), batch_size=batch_size, shuffle=False)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    model = V42TwoHeadAlphaModel().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    bce_loss_fn = nn.BCELoss()

    best_val_regret = float("inf")
    best_agreement = 0.0
    history = []

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        total_delta_loss = 0.0
        total_rescue_loss = 0.0

        for batch in train_loader:
            obs = batch["obs"].to(device)
            mask = batch["mask"].to(device)
            delta_target = batch["delta_cash"].to(device)
            rescue_target = batch["rescue"].to(device)

            delta_mean, rescue_probs, sigma, _ = model(obs)

            # Scale target cash delta: delta / 100.0
            scaled_target = delta_target / DELTA_SCALE
            # Valid mask: legal and delta > -9000
            valid_mask = (delta_target > -9000) & mask

            # Gaussian NLL on scaled delta
            var = torch.clamp(sigma ** 2, min=0.01, max=100.0)
            diff = scaled_target - delta_mean
            nll_element = 0.5 * (diff ** 2) / var + 0.5 * torch.log(var)
            delta_loss = (nll_element * valid_mask.float()).sum() / torch.clamp(valid_mask.float().sum(), min=1.0)

            # BCE loss for rescue prediction
            rescue_loss = bce_loss_fn(rescue_probs, rescue_target)

            loss = delta_loss + 5.0 * rescue_loss

            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

            total_loss += loss.item()
            total_delta_loss += delta_loss.item()
            total_rescue_loss += rescue_loss.item()

        scheduler.step()

        # Validation loop
        model.eval()
        val_agreements = 0
        val_regrets = []
        val_false_pos = 0
        val_rescues_detected = 0
        total_val = 0

        with torch.no_grad():
            for batch in val_loader:
                obs = batch["obs"].to(device)
                mask = batch["mask"].to(device)
                delta_target = batch["delta_cash"].to(device)
                best_actions = batch["best_action"].numpy()
                rescue_target = batch["rescue"].numpy()

                delta_mean, rescue_probs, sigma, _ = model(obs)

                # Rescale predictions back to dollars: mu * 100, sigma * 100
                mu = delta_mean.cpu().numpy() * DELTA_SCALE
                sig = sigma.cpu().numpy() * DELTA_SCALE
                p_res = rescue_probs.cpu().numpy()
                masks = mask.cpu().numpy()
                targets = delta_target.cpu().numpy()

                for i in range(len(best_actions)):
                    total_val += 1
                    # Gated scoring: mu - 1.0 * sig + 50.0 * p_res
                    scores = mu[i] - 1.0 * sig[i] + 50.0 * p_res[i]
                    scores[0] = 0.0  # baseline is 0
                    for a in range(NUM_INTERVENTIONS):
                        if not masks[i, a]:
                            scores[a] = -99999.0

                    best_a = int(np.argmax(scores))
                    # LCB gate: must exceed threshold 15.0
                    selected = best_a if (best_a != 0 and scores[best_a] >= 15.0) else 0

                    oracle_a = best_actions[i]
                    if selected == oracle_a:
                        val_agreements += 1

                    oracle_best_delta = max(0.0, float(targets[i, oracle_a]))
                    selected_delta = float(targets[i, selected]) if selected < NUM_INTERVENTIONS else 0.0
                    regret = max(0.0, oracle_best_delta - selected_delta)
                    val_regrets.append(regret)

                    if selected != 0 and selected_delta < 0:
                        val_false_pos += 1
                    if selected != 0 and rescue_target[i, selected] > 0.5:
                        val_rescues_detected += 1

        val_agr_rate = val_agreements / max(1, total_val) * 100.0
        val_mean_regret = float(np.mean(val_regrets)) if val_regrets else 0.0
        val_fp_rate = val_false_pos / max(1, total_val) * 100.0

        history.append({
            "epoch": epoch,
            "train_loss": total_loss / len(train_loader),
            "val_agreement": val_agr_rate,
            "val_regret": val_mean_regret,
            "val_fp_rate": val_fp_rate,
            "val_rescues": val_rescues_detected
        })

        if epoch % 5 == 0 or epoch == epochs:
            print(f"Epoch {epoch:2d}/{epochs} | Train Loss: {total_loss / len(train_loader):.3f} | Val Oracle Agr: {val_agr_rate:.1f}% | Mean Regret: ${val_mean_regret:.2f} | FP Rate: {val_fp_rate:.1f}% | Rescues: {val_rescues_detected}")

        if val_mean_regret < best_val_regret and epoch >= 5:
            best_val_regret = val_mean_regret
            best_agreement = val_agr_rate
            ckpt_path = os.path.join(REPO_ROOT, "research", "v42", "checkpoints", "v42_alpha_model.pt")
            torch.save(model.state_dict(), ckpt_path)

    print(f"\nTraining Complete. Best Validation Regret: ${best_val_regret:.2f} (Oracle Agreement: {best_agreement:.1f}%)")
    print(f"Checkpoint saved to: {ckpt_path}")

    metrics_path = os.path.join(REPO_ROOT, "research", "v42", "artifacts", "alpha_model_train_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(history, f, indent=2)

    return {
        "best_val_regret": best_val_regret,
        "best_agreement": best_agreement,
        "ckpt_path": ckpt_path,
        "history": history
    }


if __name__ == "__main__":
    train_model(epochs=35, batch_size=64, lr=1e-3)
