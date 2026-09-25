# SPDX-License-Identifier: MIT
"""V32 P3 native factorized policy (v32p3-a1): shared trunk + linear slot heads.

Retains the P2 state encoder (157-dim structured-temporal features) and trunk
shape (3x256 Tanh). Replaces the pointer head with independent per-slot linear
classifiers exactly matching the simulator-native factorization
(V32_P3_ACTION_SCHEMA.md): per unit slot U_OP(18)/U_ARG(12)/U_QTY(17); per
market slot M_OP(7)/M_ITEM(12)/M_QTY(77). No masking, no autoregression.
"""

import torch
import torch.nn as nn

from v32.p3 import codec as C

D_STATE = 256
D_SLOT = 16

U_ARG_OPS = {C._U_OP_ID[o] for o in ("PLANT", "PICKUP", "PLACE")}
U_QTY_OPS = {C._U_OP_ID[o] for o in ("PICKUP", "PLACE")}
M_ITEM_OPS = {C._M_OP_ID[o] for o in ("BUY_SEED", "BUY_PRODUCT",
                                      "BUY_ANIMAL", "SELL")}


def param_count(mod):
    return sum(p.numel() for p in mod.parameters())


class P3Policy(nn.Module):
    def __init__(self, state_dim=157, uctx_dim=12):
        super().__init__()
        self.trunk = nn.Sequential(nn.Linear(state_dim, D_STATE), nn.Tanh(),
                                   nn.Linear(D_STATE, D_STATE), nn.Tanh(),
                                   nn.Linear(D_STATE, D_STATE), nn.Tanh())
        du = D_STATE + uctx_dim
        self.u_op = nn.Linear(du, len(C.U_OP))
        self.u_arg = nn.Linear(du, len(C.U_ARG))
        self.u_qty = nn.Linear(du, len(C.U_QTY))
        self.slot_emb = nn.Embedding(C.M_MARKET_SLOTS, D_SLOT)
        dm = D_STATE + D_SLOT
        self.m_op = nn.Linear(dm, len(C.M_OP))
        self.m_item = nn.Linear(dm, len(C.M_ITEM))
        self.m_qty = nn.Linear(dm, len(C.M_QTY))
        self.critic = nn.Sequential(nn.Linear(D_STATE, D_STATE), nn.Tanh(),
                                    nn.Linear(D_STATE, 1))

    def forward(self, state, uctx, unit_valid):
        """state [B,d], uctx [B,U,du], unit_valid [B,U] bool.

        Returns per-head logits ([B,U,.] unit, [B,M,.] market) + value [B].
        """
        h = self.trunk(state)
        B, U, _ = uctx.shape
        qu = torch.cat([h.unsqueeze(1).expand(B, U, D_STATE), uctx], dim=-1)
        M = C.M_MARKET_SLOTS
        se = self.slot_emb.weight.unsqueeze(0).expand(B, M, D_SLOT)
        qm = torch.cat([h.unsqueeze(1).expand(B, M, D_STATE), se], dim=-1)
        return {"u_op": self.u_op(qu), "u_arg": self.u_arg(qu),
                "u_qty": self.u_qty(qu), "m_op": self.m_op(qm),
                "m_item": self.m_item(qm), "m_qty": self.m_qty(qm),
                "value": self.critic(h).squeeze(-1),
                "unit_valid": unit_valid}

    @torch.no_grad()
    def act(self, state, uctx, unit_valid, deterministic=False):
        out = self.forward(state, uctx, unit_valid)
        pics = {}
        for k in ("u_op", "u_arg", "u_qty", "m_op", "m_item", "m_qty"):
            lg = out[k]
            pics[k] = lg.argmax(-1) if deterministic else \
                torch.distributions.Categorical(logits=lg).sample()
        lp = torch.zeros(state.shape[0], device=state.device)
        ent = torch.zeros(state.shape[0], device=state.device)
        vf = unit_valid.float()
        for k, targ in (("u_op", pics["u_op"]),):
            lp = lp + torch.log_softmax(out[k], -1).gather(
                -1, targ.unsqueeze(-1)).squeeze(-1).mul(vf).sum(-1)
            ent = ent + torch.distributions.Categorical(
                logits=out[k]).entropy().mul(vf).sum(-1)
        # arg/qty contribute only where the sampled op uses them (decode
        # ignores don't-care heads, so they are not executed decisions).
        uo = pics["u_op"]
        use_arg = torch.zeros_like(uo, dtype=torch.bool)
        use_qty = torch.zeros_like(uo, dtype=torch.bool)
        for c in U_ARG_OPS:
            use_arg = use_arg | (uo == c)
        for c in U_QTY_OPS:
            use_qty = use_qty | (uo == c)
        for k, gate in (("u_arg", use_arg), ("u_qty", use_qty)):
            g = (gate & unit_valid).float()
            lp = lp + torch.log_softmax(out[k], -1).gather(
                -1, pics[k].unsqueeze(-1)).squeeze(-1).mul(g).sum(-1)
            ent = ent + torch.distributions.Categorical(
                logits=out[k]).entropy().mul(g).sum(-1)
        mo = pics["m_op"]
        use_m = torch.zeros_like(mo, dtype=torch.bool)
        for c in M_ITEM_OPS:
            use_m = use_m | (mo == c)
        for k in ("m_op",):
            lp = lp + torch.log_softmax(out[k], -1).gather(
                -1, pics[k].unsqueeze(-1)).squeeze(-1).sum(-1)
            ent = ent + torch.distributions.Categorical(
                logits=out[k]).entropy().sum(-1)
        for k in ("m_item", "m_qty"):
            g = use_m.float()
            lp = lp + torch.log_softmax(out[k], -1).gather(
                -1, pics[k].unsqueeze(-1)).squeeze(-1).mul(g).sum(-1)
            ent = ent + torch.distributions.Categorical(
                logits=out[k]).entropy().mul(g).sum(-1)
        return {"u_op": pics["u_op"], "u_arg": pics["u_arg"],
                "u_qty": pics["u_qty"], "m_op": pics["m_op"],
                "m_item": pics["m_item"], "m_qty": pics["m_qty"],
                "logprob": lp, "entropy": ent, "value": out["value"]}


class LinearControl(nn.Module):
    """Linear probe on the same head inputs (no trunk, fixed slot one-hot).

    Answers: is the 400-sample subset learnable at all from these features?
    (P2 precedent: linear control hit 100% by ep75 on identical features.)
    """

    def __init__(self, state_dim=157, uctx_dim=12):
        super().__init__()
        du = state_dim + uctx_dim
        self.u_op = nn.Linear(du, len(C.U_OP))
        self.u_arg = nn.Linear(du, len(C.U_ARG))
        self.u_qty = nn.Linear(du, len(C.U_QTY))
        dm = state_dim + C.M_MARKET_SLOTS
        self.m_op = nn.Linear(dm, len(C.M_OP))
        self.m_item = nn.Linear(dm, len(C.M_ITEM))
        self.m_qty = nn.Linear(dm, len(C.M_QTY))

    def forward(self, state, uctx, unit_valid):
        B, U, _ = uctx.shape
        qu = torch.cat([state.unsqueeze(1).expand(B, U, state.shape[1]),
                        uctx], dim=-1)
        M = C.M_MARKET_SLOTS
        onehot = torch.eye(M, device=state.device).unsqueeze(0).expand(
            B, M, M)
        qm = torch.cat([state.unsqueeze(1).expand(B, M, state.shape[1]),
                        onehot], dim=-1)
        return {"u_op": self.u_op(qu), "u_arg": self.u_arg(qu),
                "u_qty": self.u_qty(qu), "m_op": self.m_op(qm),
                "m_item": self.m_item(qm), "m_qty": self.m_qty(qm),
                "value": torch.zeros(B, device=state.device),
                "unit_valid": unit_valid}
