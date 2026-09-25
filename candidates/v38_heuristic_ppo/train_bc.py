# SPDX-License-Identifier: MIT
"""Kagriculture V38 Behavioral Cloning (BC) Warm-Start Trainer.

Trains MacroActorCritic to imitate expert macro-option selections from counterfactual data.
Evaluates accuracy, calibration, and false-intervention rate.
"""

from __future__ import annotations
import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

try:
    from config import SCRATCH_DIR, NUM_MACRO_ACTIONS
    from dataset import load_dataset, DATASET_FILE
    from policy import MacroActorCritic
except ImportError:
    from candidates.v38_heuristic_ppo.config import SCRATCH_DIR, NUM_MACRO_ACTIONS
    from candidates.v38_heuristic_ppo.dataset import load_dataset, DATASET_FILE
    from candidates.v38_heuristic_ppo.policy import MacroActorCritic


BC_CHECKPOINT_PATH = os.path.join(SCRATCH_DIR, "bc_policy.pt")
BC_METRICS_PATH = os.path.join(SCRATCH_DIR, "bc_metrics.json")


def train_behavioral_cloning(
    dataset_path: str = DATASET_FILE,
    checkpoint_out: str = BC_CHECKPOINT_PATH,
    metrics_out: str = BC_METRICS_PATH,
    epochs: int = 50,
    lr: float = 1e-3,
    batch_size: int = 32
) -> Dict[str, Any]:
    data = load_dataset(dataset_path)
    records = data["records"]
    
    seeds = sorted(list(set(r["seed"] for r in records)))
    if len(seeds) > 1:
        val_seed = seeds[-1]
        train_records = [r for r in records if r["seed"] != val_seed]
        val_records = [r for r in records if r["seed"] == val_seed]
    else:
        # Fallback to random 80/20 split if single seed
        np.random.seed(42)
        idx = np.random.permutation(len(records))
        split = int(0.8 * len(records))
        train_records = [records[i] for i in idx[:split]]
        val_records = [records[i] for i in idx[split:]]
        
    print(f"BC Training: {len(train_records)} train records, {len(val_records)} validation records.")
    
    # Prepare tensors
    def prep_tensors(recs):
        obs = torch.tensor([r["state_vector"] for r in recs], dtype=torch.float32)
        masks = torch.tensor([r["action_mask"] for r in recs], dtype=torch.bool)
        targets = torch.tensor([r["best_option"] for r in recs], dtype=torch.long)
        values = torch.tensor([r["best_delta"] for r in recs], dtype=torch.float32)
        return obs, masks, targets, values
        
    train_obs, train_masks, train_targets, train_values = prep_tensors(train_records)
    val_obs, val_masks, val_targets, val_values = prep_tensors(val_records)
    
    train_dataset = TensorDataset(train_obs, train_masks, train_targets, train_values)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    
    model = MacroActorCritic()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    criterion_policy = nn.CrossEntropyLoss()
    criterion_value = nn.MSELoss()
    
    best_val_acc = -1.0
    history = []
    
    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        correct = 0
        total_samples = 0
        
        for b_obs, b_masks, b_targets, b_vals in train_loader:
            optimizer.zero_grad()
            logits, values = model(b_obs, b_masks)
            loss_pol = criterion_policy(logits, b_targets)
            loss_val = criterion_value(values, b_vals / 1000.0)  # Normalized scale
            loss = loss_pol + 0.1 * loss_val
            
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item() * len(b_obs)
            preds = torch.argmax(logits, dim=-1)
            correct += (preds == b_targets).sum().item()
            total_samples += len(b_obs)
            
        train_acc = correct / max(1, total_samples)
        
        # Validation
        model.eval()
        with torch.no_grad():
            v_logits, v_values = model(val_obs, val_masks)
            v_loss = criterion_policy(v_logits, val_targets).item()
            v_preds = torch.argmax(v_logits, dim=-1)
            val_acc = (v_preds == val_targets).sum().item() / max(1, len(val_targets))
            
            # Calibration / Confidence
            v_probs = F.softmax(v_logits, dim=-1)
            confidences = v_probs.gather(-1, v_preds.unsqueeze(-1)).squeeze(-1).numpy()
            mean_conf = float(np.mean(confidences))
            
            # Agreement on TRUST_HEURISTIC (action 0)
            h_mask = (val_targets == 0)
            if h_mask.sum().item() > 0:
                h_acc = (v_preds[h_mask] == 0).sum().item() / h_mask.sum().item()
            else:
                h_acc = 1.0
                
            # False intervention rate (predicted > 0 when target is 0)
            false_interventions = (v_preds[h_mask] > 0).sum().item() / max(1, h_mask.sum().item())
            
        history.append({
            "epoch": epoch,
            "train_loss": total_loss / total_samples,
            "train_acc": train_acc,
            "val_loss": v_loss,
            "val_acc": val_acc,
            "mean_conf": mean_conf,
            "heuristic_acc": h_acc,
            "false_intervention_rate": false_interventions
        })
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), checkpoint_out)
            
    final_metrics = {
        "best_val_acc": best_val_acc,
        "final_epoch": epochs,
        "train_samples": len(train_records),
        "val_samples": len(val_records),
        "final_train_acc": history[-1]["train_acc"],
        "final_val_acc": history[-1]["val_acc"],
        "final_heuristic_agreement": history[-1]["heuristic_acc"],
        "final_false_intervention_rate": history[-1]["false_intervention_rate"],
        "mean_confidence": history[-1]["mean_conf"],
        "checkpoint": checkpoint_out,
        "history": history
    }
    
    with open(metrics_out, "w", encoding="utf-8") as f:
        json.dump(final_metrics, f, indent=2)
        
    print(f"BC Training Complete! Best Val Acc: {best_val_acc*100:.2f}%. Saved to {checkpoint_out}")
    return final_metrics
