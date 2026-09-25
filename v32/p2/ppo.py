# SPDX-License-Identifier: MIT
"""V32 P2 masked multi-head PPO: GAE + clipped update + parity tripwire.

One PPO step = forward over stored per-step features; joint logprob = sum
of per-slot logprobs; entropy = sum over valid slots. Candidate parity
(§25 option A): masks + selected-candidate identity hashes regenerated
from stored essentials (seeds) and asserted equal every update batch.
"""

import torch
import torch.nn as nn

from v32.p2 import actions as A


def compute_gae(rewards, values, dones, gamma=1.0, lam=0.95):
    """rewards/values/dones: [T] tensors, single episode (done[-1]=True).
    Returns (advantages, returns)."""
    T = len(rewards)
    adv = torch.zeros(T, dtype=torch.float32)
    last = 0.0
    for t in range(T - 1, -1, -1):
        mask = 0.0 if dones[t] else 1.0
        nxt = 0.0 if dones[t] else values[t + 1] if t + 1 < T else 0.0
        delta = rewards[t] + gamma * mask * nxt - values[t]
        last = delta + gamma * lam * mask * last
        adv[t] = last
    return adv, adv + values


def check_parity(batch, uvoc, mvoc):
    """Regenerate masks + selected identity hashes from stored seeds;
    assert equality with rollout-time values. Raises on mismatch."""
    uidx = {c: i for i, c in enumerate(uvoc)}
    midx = {c: i for i, c in enumerate(mvoc)}
    for i in range(len(batch["seeds"])):
        seeds = batch["seeds"][i]
        regen_mask = A.plant_mask(uvoc, seeds)
        assert regen_mask == batch["mask"][i], "mask regen mismatch @%d" % i
        usel = [uvoc[j] for j in batch["u_idx"][i]]
        msel = [mvoc[j] for j in batch["m_idx"][i]]
        ulits = [A.unit_to_literal(c) for c in usel]
        mlits = A.emit_market_list(msel)
        regen = [A.candidate_hash(x) for x in ulits + mlits]
        assert regen == batch["hashes"][i], "identity regen mismatch @%d" % i
    return True


def ppo_update(model, opt, batch, uidx_len, midx_len, uvoc, mvoc,
               clip=0.2, vf_coef=0.5, ent_coef=0.01, epochs=4,
               minibatch=2048, max_grad_norm=0.5):
    """batch dict of lists over steps (padded U). Returns stats dict."""
    import numpy as np
    check_parity(batch, uvoc, mvoc)
    N = len(batch["feat"])
    F = torch.tensor(np.asarray(batch["feat"]), dtype=torch.float32)
    U = max(len(u) for u in batch["uctx"])
    uc = torch.zeros(N, U, 12)
    vv = torch.zeros(N, U, dtype=torch.bool)
    ut = torch.zeros(N, U, dtype=torch.long)
    for i in range(N):
        u = len(batch["uctx"][i])
        uc[i, :u] = torch.tensor(np.asarray(batch["uctx"][i]),
                                 dtype=torch.float32)
        vv[i, :u] = True
        ut[i, :u] = torch.tensor(batch["u_idx"][i], dtype=torch.long)
    mt = torch.tensor(np.asarray(batch["m_idx"]), dtype=torch.long)
    mk = torch.tensor(np.asarray(batch["mask"]), dtype=torch.float32)
    old_lp = torch.tensor(np.asarray(batch["logprob"]), dtype=torch.float32)
    adv = torch.tensor(np.asarray(batch["adv"]), dtype=torch.float32)
    ret = torch.tensor(np.asarray(batch["ret"]), dtype=torch.float32)
    adv = (adv - adv.mean()) / (adv.std() + 1e-8)
    stats = {"clip_frac": [], "pg_loss": [], "v_loss": [], "ent": []}
    idx = np.arange(N)
    for _ in range(epochs):
        np.random.shuffle(idx)
        for a in range(0, N, minibatch):
            mb = idx[a:a + minibatch]
            out = model(F[mb], uc[mb], vv[mb], mk[mb])
            lp_u = torch.log_softmax(out["unit_logits"], -1).gather(
                -1, ut[mb].unsqueeze(-1)).squeeze(-1) * vv[mb].float()
            lp_m = torch.log_softmax(out["market_logits"], -1).gather(
                -1, mt[mb].unsqueeze(-1)).squeeze(-1)
            new_lp = lp_u.sum(-1) + lp_m.sum(-1)
            ratio = torch.exp(new_lp - old_lp[mb])
            pg1 = ratio * adv[mb]
            pg2 = torch.clamp(ratio, 1 - clip, 1 + clip) * adv[mb]
            pg_loss = -torch.min(pg1, pg2).mean()
            v_loss = nn.functional.mse_loss(out["value"], ret[mb])
            ent = (torch.distributions.Categorical(
                logits=out["unit_logits"]).entropy() * vv[mb].float()).sum(-1) \
                + torch.distributions.Categorical(
                    logits=out["market_logits"]).entropy().sum(-1)
            loss = pg_loss + vf_coef * v_loss - ent_coef * ent.mean()
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_grad_norm)
            opt.step()
            stats["clip_frac"].append(float(
                ((ratio - 1).abs() > clip).float().mean()))
            stats["pg_loss"].append(float(pg_loss.detach()))
            stats["v_loss"].append(float(v_loss.detach()))
            stats["ent"].append(float(ent.mean().detach()))
    return {k: sum(v) / len(v) for k, v in stats.items()}
