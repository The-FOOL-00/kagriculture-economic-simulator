# SPDX-License-Identifier: MIT
"""V32 P2 locked network: shared 3x256 Tanh trunk + pointer heads + critic.

Per-slot independent pointer heads (NOT autoregressive): farmer + each hand
share ONE unit head over UNIT_VOCAB; each of the M=10 market slots has its
own query (state + learned slot embedding) over MARKET_VOCAB. All slots
sample in parallel given the state. Logprob/entropy = sums over slots.
"""

import math

import torch
import torch.nn as nn

D_STATE = 256
D_CAND = 256
D_SLOT = 16


def param_count(mod):
    return sum(p.numel() for p in mod.parameters())


class CandidateEncoder(nn.Module):
    """§18: categorical embeddings + scalars -> 128 -> Tanh -> 256."""

    def __init__(self, n_ops, n_items):
        super().__init__()
        self.op_emb = nn.Embedding(n_ops, 16)
        self.item_emb = nn.Embedding(n_items + 1, 8)  # index n_items = None
        self.mlp = nn.Sequential(nn.Linear(16 + 8 + 3, 128), nn.Tanh(),
                                 nn.Linear(128, D_CAND))
        self.n_items = n_items

    def forward(self, op_idx, item_idx, scalars):
        x = torch.cat([self.op_emb(op_idx), self.item_emb(item_idx),
                       scalars], dim=-1)
        return self.mlp(x)


class P2Policy(nn.Module):
    def __init__(self, state_dim, uctx_dim, unit_vocab, market_vocab,
                 op_list, item_list):
        super().__init__()
        self.trunk = nn.Sequential(nn.Linear(state_dim, D_STATE), nn.Tanh(),
                                   nn.Linear(D_STATE, D_STATE), nn.Tanh(),
                                   nn.Linear(D_STATE, D_STATE), nn.Tanh())
        self.unit_vocab = list(unit_vocab)
        self.market_vocab = list(market_vocab)
        self.op_id = {o: i for i, o in enumerate(op_list)}
        self.item_id = {t: i for i, t in enumerate(item_list)}
        self.cand_enc = CandidateEncoder(len(op_list), len(item_list))
        self.q_unit = nn.Linear(D_STATE + uctx_dim, D_CAND)
        self.k_unit = nn.Linear(D_CAND, D_CAND)
        self.slot_emb = nn.Embedding(10, D_SLOT)
        self.q_mkt = nn.Linear(D_STATE + D_SLOT, D_CAND)
        self.k_mkt = nn.Linear(D_CAND, D_CAND)
        self.critic = nn.Sequential(nn.Linear(D_STATE, D_STATE), nn.Tanh(),
                                    nn.Linear(D_STATE, 1))

    def _cand_tensors(self, vocab, device):
        op = torch.tensor([self.op_id[c[0]] for c in vocab],
                          dtype=torch.long, device=device)
        item = torch.tensor([self.item_id.get(c[1], len(self.item_id))
                             for c in vocab], dtype=torch.long, device=device)
        sc = torch.tensor([[((c[2] or 0) / 1000.0) if c[2] is not None else 0.0,
                            1.0 if c[2] is not None else 0.0,
                            1.0 if c[1] is not None else 0.0] for c in vocab],
                          dtype=torch.float32, device=device)
        return op, item, sc

    def forward(self, state, uctx, unit_valid, unit_mask):
        """state [B,d], uctx [B,U,du], unit_valid [B,U] bool,
        unit_mask [B,Cu] (1=masked). Returns dict with unit_logits [B,U,Cu],
        market_logits [B,M,Cm], value [B]."""
        dev = state.device
        h = self.trunk(state)
        uop, uitem, usc = self._cand_tensors(self.unit_vocab, dev)
        mop, mitem, msc = self._cand_tensors(self.market_vocab, dev)
        Eu = self.cand_enc(uop, uitem, usc)      # [Cu,256]
        Em = self.cand_enc(mop, mitem, msc)      # [Cm,256]
        Ku = self.k_unit(Eu)                     # [Cu,256]
        Km = self.k_mkt(Em)
        B, U, _ = uctx.shape
        qu = self.q_unit(torch.cat([h.unsqueeze(1).expand(B, U, D_STATE),
                                    uctx], dim=-1))       # [B,U,256]
        ulog = qu @ Ku.T / math.sqrt(D_CAND)              # [B,U,Cu]
        ulog = ulog + unit_mask.unsqueeze(1) * -1e9
        M = 10
        se = self.slot_emb.weight.unsqueeze(0).expand(B, M, D_SLOT)
        qm = self.q_mkt(torch.cat([h.unsqueeze(1).expand(B, M, D_STATE),
                                   se], dim=-1))           # [B,M,256]
        mlog = qm @ Km.T / math.sqrt(D_CAND)              # [B,M,Cm]
        value = self.critic(h).squeeze(-1)
        return {"unit_logits": ulog, "market_logits": mlog, "value": value,
                "unit_valid": unit_valid}

    @torch.no_grad()
    def act(self, state, uctx, unit_valid, unit_mask, deterministic=False):
        out = self.forward(state, uctx, unit_valid, unit_mask)
        ulog, mlog = out["unit_logits"], out["market_logits"]
        if deterministic:
            u = ulog.argmax(-1)
            m = mlog.argmax(-1)
        else:
            u = torch.distributions.Categorical(logits=ulog).sample()
            m = torch.distributions.Categorical(logits=mlog).sample()
        lp_u = torch.log_softmax(ulog, -1).gather(-1, u.unsqueeze(-1)).squeeze(-1)
        lp_m = torch.log_softmax(mlog, -1).gather(-1, m.unsqueeze(-1)).squeeze(-1)
        lp_u = lp_u * unit_valid.float()
        logprob = lp_u.sum(-1) + lp_m.sum(-1)
        ent_u = torch.distributions.Categorical(logits=ulog).entropy() * \
            unit_valid.float()
        ent_m = torch.distributions.Categorical(logits=mlog).entropy()
        return {"unit": u, "market": m, "logprob": logprob,
                "entropy": ent_u.sum(-1) + ent_m.sum(-1),
                "value": out["value"]}
