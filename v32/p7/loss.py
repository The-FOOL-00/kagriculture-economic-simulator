# SPDX-License-Identifier: MIT
"""V32 P7 prefix-window loss (Mode A, teacher-forced).

L_prefix(H) = mean over rows with step <= H of the per-row masked action
loss (unit u_op mean over that row's valid units + market m_op/m_item/m_qty
means over that row's slots, with target-op masking as in
v32.p3.metrics.head_losses).

ROW-uniform by construction: every qualifying timestep contributes exactly
1/N_window regardless of how many units it has. (A pooled-unit mean would
secretly weight steps 2-4 six times more than steps 0-1 — a hidden
step-weighting scheme. This formulation cannot do that.) No per-step weights,
no spikes, no schedule — covered by tests/test_v32_p7.py::test_04, which
verifies L(batch) == mean of per-row L.

No future-state access: the loss consumes only current-row logits and
current-row recorded targets. Rows with step > H are excluded via the mask.
"""

import torch

from v32.p3 import codec as C
from v32.p3.metrics import _op_mask
from v32.p3.models import M_ITEM_OPS


def prefix_window_mask(steps, H):
    """Bool mask of rows with step <= H. Pure function of step indices."""
    return torch.tensor([int(s) <= int(H) for s in steps], dtype=torch.bool)


def _row_loss(out, batch, i, ce):
    vv = batch["valid"][i]
    lu = ce(out["u_op"][i][vv], batch["u_op"][i][vv]).mean()
    lm_op = ce(out["m_op"][i], batch["m_op"][i]).mean()
    mm = _op_mask(batch["m_op"][i], M_ITEM_OPS)
    z = out["u_op"].sum() * 0.0
    lm_item = ce(out["m_item"][i][mm], batch["m_item"][i][mm]).mean() \
        if mm.any() else z
    lm_qty = ce(out["m_qty"][i][mm], batch["m_qty"][i][mm]).mean() \
        if mm.any() else z
    return lu + lm_op + lm_item + lm_qty


def prefix_loss(out, batch, steps, H, ce):
    """Row-uniform mean action loss over the 0..H window. Scalar tensor."""
    m = prefix_window_mask(steps, H)
    if not m.any():
        return out["u_op"].sum() * 0.0
    idx = torch.where(m)[0]
    return torch.stack([_row_loss(out, batch, int(i), ce) for i in idx]).mean()
