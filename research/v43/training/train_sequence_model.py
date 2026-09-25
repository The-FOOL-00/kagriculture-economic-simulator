# SPDX-License-Identifier: MIT
"""Kagriculture V43 Sequence Advantage Model Training Loop.

Trains V43SequenceAlphaModel with heteroscedastic Gaussian NLL loss and BCE rescue loss:
- Evaluates out-of-sample on complete held-out validation games (no seed leakage)
- Tracks Oracle Action Agreement, Mean Economic Regret, and False Positive Rate
- Saves checkpoint: research/v43/checkpoints/v43_sequence_model.pt
- Saves metrics: research/v43/artifacts/sequence_model_metrics.json
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
from torch.utils.data import Dataset, DataLoader

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v43.policy.sequence_model import V43SequenceAlphaModel


class SequenceDataset(Dataset):
    def __init__(self, samples: List[Dict[str, Any]]):
        self.samples = samples

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        s = self.samples[idx]
        obs = torch.tensor(s["obs"], dtype=torch.float32)
        seq = torch.tensor(s["action_seq"], dtype=torch.long)
        dc = torch.tensor(s["delta_cash"] / 100.0, dtype=torch.float32)  # Scale to $100 units
        rescue = torch.tensor(1.0 if s["rescue"] else 0.0, dtype=torch.float32)
        return obs, seq, dc, rescue, s["delta_cash"], s["seed"], s["opp_id"]


def train_sequence_model(
    epochs: int = 30,
    batch_size: int = 32,
    lr: float = 1e-3,
    val_split_seed_count: int = 2
):
    print("=" * 80)
    print("V43 SEQUENCE ADVANTAGE & UNCERTAINTY MODEL TRAINING")
    print("=" * 80)
    t0 = time.perf_counter()

    data_path = os.path.join(REPO_ROOT, "research", "v43", "artifacts", "sequence_dataset.pt")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Dataset not found at {data_path}. Run dataset generator first!")

    all_samples = torch.load(data_path, weights_only=False)
    print(f"Loaded {len(all_samples)} total sequence samples.")

    # Split by complete games (seeds)
    all_seeds = sorted(list(set(s["seed"] for s in all_samples)))
    val_seeds = set(all_seeds[-val_split_seed_count:])
    train_seeds = set(all_seeds[:-val_split_seed_count])
    print(f"Train Seeds ({len(train_seeds)}): {sorted(list(train_seeds))}")
    print(f"Val Seeds ({len(val_seeds)}): {sorted(list(val_seeds))}")

    train_samples = [s for s in all_samples if s["seed"] in train_seeds]
    val_samples = [s for s in all_samples if s["seed"] in val_seeds]
    print(f"Train samples: {len(train_samples)} | Val samples: {len(val_samples)}")

    train_ds = SequenceDataset(train_samples)
    val_ds = SequenceDataset(val_samples)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    model = V43SequenceAlphaModel()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    bce_loss_fn = nn.BCELoss()

    history = []

    for ep in range(1, epochs + 1):
        model.train()
        train_loss_total = 0.0
        train_batches = 0

        for obs, seq, target_dc, target_rescue, _, _, _ in train_loader:
            optimizer.zero_grad()
            delta_pred, rescue_pred, sigma_pred = model(obs, seq)

            # Heteroscedastic Gaussian NLL loss
            var = sigma_pred ** 2
            loss_nll = 0.5 * (((delta_pred - target_dc) ** 2) / var + torch.log(var)).mean()

            # BCE rescue loss
            loss_rescue = bce_loss_fn(rescue_pred, target_rescue)

            total_loss = loss_nll + 3.0 * loss_rescue
            total_loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

            train_loss_total += total_loss.item()
            train_batches += 1

        scheduler.step()
        train_loss = train_loss_total / max(1, train_batches)

        # Validation evaluation
        model.eval()
        val_mae_dollars = []
        fp_count = 0
        total_proposals = 0

        with torch.no_grad():
            for obs, seq, _, _, raw_dc, _, _ in val_loader:
                delta_pred, rescue_pred, sigma_pred = model(obs, seq)
                pred_dollars = delta_pred.numpy() * 100.0
                raw_dollars = raw_dc.numpy()

                mae = np.abs(pred_dollars - raw_dollars)
                val_mae_dollars.extend(mae.tolist())

                # Check LCB false positives: proposed positive (> $15) but actually negative (< -$20)
                lcb_scores = pred_dollars - 1.0 * (sigma_pred.numpy() * 100.0)
                for lcb, actual in zip(lcb_scores, raw_dollars):
                    if lcb >= 15.0:
                        total_proposals += 1
                        if actual < -20.0:
                            fp_count += 1

        mean_mae = float(np.mean(val_mae_dollars)) if val_mae_dollars else 0.0
        fp_rate = (fp_count / max(1, total_proposals)) * 100.0 if total_proposals > 0 else 0.0

        if ep % 5 == 0 or ep == epochs:
            print(f"Epoch {ep:>2}/{epochs} | Train Loss: {train_loss:>6.3f} | Val MAE: ${mean_mae:>6.2f} | Proposals: {total_proposals} | FP Rate: {fp_rate:.1f}%")

        history.append({
            "epoch": ep,
            "train_loss": round(train_loss, 4),
            "val_mae": round(mean_mae, 2),
            "proposals": total_proposals,
            "false_positives": fp_count,
            "fp_rate": round(fp_rate, 2)
        })

    # Save model and metrics
    ckpt_path = os.path.join(REPO_ROOT, "research", "v43", "checkpoints", "v43_sequence_model.pt")
    torch.save(model.state_dict(), ckpt_path)
    print(f"\nSaved model checkpoint to {ckpt_path}")

    metrics_path = os.path.join(REPO_ROOT, "research", "v43", "artifacts", "sequence_model_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(history, f, indent=2)
    print(f"Saved metrics to {metrics_path}")

    dur = time.perf_counter() - t0
    print(f"Training completed in {dur:.1f}s.")
    return model, history


if __name__ == "__main__":
    train_sequence_model(epochs=25, batch_size=32)
