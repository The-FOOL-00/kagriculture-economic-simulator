# SPDX-License-Identifier: MIT
"""R1 training loop: full-batch Adam + VAL early-stop + checkpoints."""

import json
import os
import time

import torch
import torch.nn as nn

from v32.router.models import build, param_count


def set_deterministic(seed):
    torch.manual_seed(seed)
    try:
        torch.use_deterministic_algorithms(True)
    except Exception:  # noqa: BLE001 - backend without full support
        pass


def soft_ce(logits, targets):
    logp = torch.log_softmax(logits, dim=1)
    return -(targets * logp).sum(dim=1).mean()


def train_model(Xtr, Ytr, Xva, Yva, model_name, seed=0, lr=1e-3, wd=1e-2,
                epochs=2000, patience=200, multitask=False, cash_tr=None,
                cash_mu=0.0, cash_sd=1.0, win_tr=None):
    """Returns (state_dict, history, best_val). Deterministic given seed."""
    set_deterministic(seed)
    d = Xtr.shape[1]
    model = build(model_name, d)
    Xt = torch.tensor(Xtr, dtype=torch.float32)
    Yt = torch.tensor(Ytr, dtype=torch.float32)
    Xv = torch.tensor(Xva, dtype=torch.float32)
    Yv = torch.tensor(Yva, dtype=torch.float32)
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=wd)
    best, best_state, since = float("inf"), None, 0
    hist = []
    mt = multitask and model_name == "small_mt"
    Ct = torch.tensor(cash_tr, dtype=torch.float32) if cash_tr is not None else None
    Wt = torch.tensor(win_tr, dtype=torch.float32) if win_tr is not None else None
    for ep in range(epochs):
        model.train()
        opt.zero_grad()
        if mt:
            logits, cash_p, win_p = model(Xt)
            loss = (soft_ce(logits, Yt)
                    + 0.1 * nn.functional.mse_loss(
                        cash_p, (Ct - cash_mu) / cash_sd)
                    + 0.1 * nn.functional.binary_cross_entropy_with_logits(
                        win_p, Wt))
        else:
            loss = soft_ce(model(Xt), Yt)
        loss.backward()
        opt.step()
        model.eval()
        with torch.no_grad():
            out = model(Xv)
            logits_v = out[0] if mt else out
            val = soft_ce(logits_v, Yv).item()
        hist.append({"epoch": ep, "train": loss.item(), "val": val})
        if val < best - 1e-12:
            best, since = val, 0
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        else:
            since += 1
            if since >= patience:
                break
    return best_state, hist, best, param_count(model)


def save_checkpoint(path, state, meta):
    import numpy as np
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    np.savez(path, **{k: v.numpy() for k, v in state.items()},
             meta=json.dumps(meta, sort_keys=True))
