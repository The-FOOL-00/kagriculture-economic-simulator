# SPDX-License-Identifier: MIT
"""R1 torch models: logistic, small/medium MLPs, multitask variant.

Runs on system python3 (torch CPU). Deterministic: seeded init, fixed
row order, deterministic algorithms where available.
"""

import torch
import torch.nn as nn

N_CLASSES = 5


def param_count(mod):
    return sum(p.numel() for p in mod.parameters())


class Logistic(nn.Module):
    def __init__(self, d):
        super().__init__()
        self.lin = nn.Linear(d, N_CLASSES)

    def forward(self, x):
        return self.lin(x)


class SmallMLP(nn.Module):
    """R1-small: d -> 64 -> 32 -> 5."""

    def __init__(self, d):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(d, 64), nn.ReLU(),
                                 nn.Linear(64, 32), nn.ReLU())
        self.head = nn.Linear(32, N_CLASSES)

    def forward(self, x):
        return self.head(self.net(x))


class MediumMLP(nn.Module):
    """R1-medium: d -> 128 -> 64 -> 32 -> 5."""

    def __init__(self, d):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(d, 128), nn.ReLU(),
                                 nn.Linear(128, 64), nn.ReLU(),
                                 nn.Linear(64, 32), nn.ReLU())
        self.head = nn.Linear(32, N_CLASSES)

    def forward(self, x):
        return self.head(self.net(x))


class SmallMultitask(SmallMLP):
    """MODEL C: expert logits + cash + winprob heads (shared trunk)."""

    def __init__(self, d):
        super().__init__(d)
        self.cash_head = nn.Linear(32, N_CLASSES)
        self.win_head = nn.Linear(32, N_CLASSES)

    def forward(self, x):
        h = self.net(x)
        return self.head(h), self.cash_head(h), self.win_head(h)


def build(name, d):
    return {"logistic": Logistic, "small": SmallMLP, "medium": MediumMLP,
            "small_mt": SmallMultitask}[name](d)
