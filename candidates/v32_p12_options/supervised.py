# SPDX-License-Identifier: MIT
"""Kagriculture V32 P12 Supervised Option Selector.

Learns a high-confidence classifier:
  s_t (71-dim S2 feature vector) -> Option ID (0=FOLLOW_A7, 1..6 = Option)
Trained exclusively on search-derived target points with meaningful value gaps.
Enforces high confidence threshold and fail-closed default to FOLLOW_A7.
"""

from __future__ import annotations
import copy
import os
import sys
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

OPTION_INDEX_TO_ID = {
    0: "FOLLOW_A7",
    1: "O01",  # EXPAND_LAND
    2: "O02",  # CROP_EXPANSION_MELON
    3: "O03",  # LIQUIDATE_SURPLUS
    4: "O04",  # OPPORTUNISTIC_SELL
    5: "O05",  # PRESERVE_CASH
    6: "O06",  # SELECTIVE_PREEMPT_SELL
}

OPTION_ID_TO_INDEX = {v: k for k, v in OPTION_INDEX_TO_ID.items()}
MACRO_ACTION_TO_OPTION_IDX = {
    0: 0,
    9: 1,  # EXPAND_LAND -> O01
    4: 2,  # CROP_EXPANSION_MELON -> O02
    3: 3,  # LIQUIDATE_SURPLUS -> O03
    1: 4,  # OPPORTUNISTIC_SELL -> O04
    8: 5,  # PRESERVE_CASH -> O05
    2: 6,  # SELECTIVE_PREEMPT_SELL -> O06
}


class OptionClassifierNetwork(nn.Module):
    """Calibrated MLP classifier mapping 71-dim S2 economic features to discrete options."""
    def __init__(self, in_features: int = 71, num_classes: int = 7, hidden_dim: int = 128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_features, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, 64),
            nn.LayerNorm(64),
            nn.ReLU(),
            nn.Linear(64, num_classes)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class SupervisedOptionSelector:
    """Supervised decision maker selecting whether and which option to trigger."""
    def __init__(
        self,
        model_path: Optional[str] = None,
        confidence_threshold: float = 0.70,
        in_features: int = 71,
        num_classes: int = 7
    ):
        self.confidence_threshold = confidence_threshold
        self.model = OptionClassifierNetwork(in_features, num_classes)
        self.model.eval()
        if model_path and os.path.exists(model_path):
            self.load(model_path)

    def select_option(self, state_vector: np.ndarray) -> Tuple[int, float, str]:
        """Inference function: maps state_vector to (option_class_idx, confidence, reason).

        Fails closed to 0 (FOLLOW_A7) if confidence is below threshold.
        """
        with torch.no_grad():
            x = torch.as_tensor(state_vector, dtype=torch.float32).unsqueeze(0)
            logits = self.model(x)
            probs = torch.softmax(logits, dim=-1).squeeze(0).numpy()

        pred_idx = int(np.argmax(probs))
        confidence = float(probs[pred_idx])

        # Mandatory fail-closed rule: if class != 0 but confidence < threshold, revert to 0
        if pred_idx != 0 and confidence < self.confidence_threshold:
            return 0, float(probs[0]), f"CONFIDENCE_BELOW_THRESHOLD_{confidence:.2f}_REVERT_A7"

        opt_id = OPTION_INDEX_TO_ID.get(pred_idx, "FOLLOW_A7")
        return pred_idx, confidence, f"ACCEPTED_{opt_id}"

    def train_on_targets(
        self,
        dataset: List[Dict[str, Any]],
        epochs: int = 40,
        batch_size: int = 16,
        lr: float = 1e-3,
        min_value_gap: float = 100.0,
        save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Trains the classifier on search target records with meaningful advantage."""
        filtered = [
            d for d in dataset
            if d.get("terminal_delta", 0.0) >= min_value_gap or d.get("candidate", 0) == 0
        ]
        
        if not filtered:
            return {"status": "EMPTY_FILTERED_DATASET", "epochs": 0}

        X_list = []
        y_list = []
        w_list = []

        for item in filtered:
            vec = item.get("state_vector")
            if vec is None:
                # If state_vector not cached, generate dummy or pass
                continue
            cand_act = item.get("candidate", 0)
            target_class = MACRO_ACTION_TO_OPTION_IDX.get(cand_act, 0)
            delta = max(0.0, float(item.get("terminal_delta", 0.0)))
            
            # Weight: scale by advantage
            weight = 1.0 + min(10.0, delta / 1000.0)
            
            X_list.append(vec)
            y_list.append(target_class)
            w_list.append(weight)

        if not X_list:
            return {"status": "NO_VALID_FEATURE_VECTORS", "epochs": 0}

        X = torch.as_tensor(np.array(X_list), dtype=torch.float32)
        y = torch.as_tensor(np.array(y_list), dtype=torch.long)
        weights = torch.as_tensor(np.array(w_list), dtype=torch.float32)

        dataset_tensor = torch.utils.data.TensorDataset(X, y, weights)
        loader = torch.utils.data.DataLoader(dataset_tensor, batch_size=batch_size, shuffle=True)

        optimizer = optim.AdamW(self.model.parameters(), lr=lr, weight_decay=1e-4)
        criterion = nn.CrossEntropyLoss(reduction="none")

        self.model.train()
        loss_history = []

        for ep in range(epochs):
            total_loss = 0.0
            total_samples = 0
            for bx, by, bw in loader:
                optimizer.zero_grad()
                out = self.model(bx)
                raw_loss = criterion(out, by)
                loss = (raw_loss * bw).mean()
                loss.backward()
                optimizer.step()
                total_loss += float(loss.item()) * len(bx)
                total_samples += len(bx)
            mean_loss = total_loss / max(1, total_samples)
            loss_history.append(mean_loss)

        self.model.eval()

        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            torch.save(self.model.state_dict(), save_path)

        return {
            "status": "TRAINED",
            "samples": len(X_list),
            "final_loss": loss_history[-1] if loss_history else 0.0,
            "loss_history": loss_history
        }

    def save(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        torch.save(self.model.state_dict(), path)

    def load(self, path: str):
        self.model.load_state_dict(torch.load(path, map_location="cpu"))
        self.model.eval()
