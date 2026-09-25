# SPDX-License-Identifier: MIT
"""V32 P2 rollout: deterministic policy-vs-expert episodes -> PPO batches.

Worker-side: online features + torch act + exact literal emission.
Stores per step: features, uctx, masks, seeds (mask regen), selected
indices + identity hashes (parity), logp, value. Reward terminal-only.
"""

import torch

from v32.p2 import actions as A
from v32.p2.essentials import essentialize
from v32.p2.features import EpisodeFeatures, unit_ctx


class Predictor:
    """Live policy wrapper (rollout + eval). Owns per-episode feature state."""

    def __init__(self, model, norm, uvoc, mvoc, device="cpu"):
        self.model = model
        self.norm = norm
        self.uvoc = uvoc
        self.mvoc = mvoc
        self.dev = torch.device(device)
        self.model.to(self.dev)
        self.model.eval()
        self.fb = EpisodeFeatures()
        self.prev_act = None

    def reset(self):
        self.fb.reset()
        self.prev_act = None

    @torch.no_grad()
    def step(self, ess, deterministic=False):
        import numpy as np
        feat = self.norm.transform(
            np.asarray([self.fb.update(ess, self.prev_act)]))[0]
        n_u = 1 + len(ess.get("hands", []) or [])
        assert n_u - 1 <= A.MAX_HANDS_CAP
        st = torch.tensor(np.asarray([feat.tolist()]), dtype=torch.float32,
                          device=self.dev)
        uc = torch.tensor(np.asarray([[unit_ctx(ess, j) for j in range(n_u)]]),
                          dtype=torch.float32, device=self.dev)
        vv = torch.ones(1, n_u, dtype=torch.bool, device=self.dev)
        mk = torch.tensor([A.plant_mask(self.uvoc, ess.get("seeds", {}) or {})],
                          dtype=torch.float32, device=self.dev)
        out = self.model.act(st, uc, vv, mk, deterministic=deterministic)
        u_idx = out["unit"][0].tolist()
        m_idx = out["market"][0].tolist()
        ulits = [A.unit_to_literal(self.uvoc[i]) for i in u_idx]
        mlits = A.emit_market_list([self.mvoc[i] for i in m_idx])
        act = {"farmer": ulits[0], "hands": ulits[1:], "market": mlits}
        self.prev_act = act
        return {"action": act, "logprob": float(out["logprob"][0]),
                "value": float(out["value"][0]),
                "entropy": float(out["entropy"][0]),
                "feat": feat, "uctx": [unit_ctx(ess, j) for j in range(n_u)],
                "mask": A.plant_mask(self.uvoc, ess.get("seeds", {}) or {}),
                "seeds": dict(ess.get("seeds", {}) or {}),
                "u_idx": u_idx, "m_idx": m_idx,
                "hashes": [A.candidate_hash(ul) for ul in ulits] +
                          [A.candidate_hash(ml) for ml in mlits]}


def run_episode(make_fn, seed, learner_seat, predictor, opponent):
    """Full episode via env.run (validated path; manual stepping leaves
    seat-1 observations uninitialized). Returns (steps, my_cash, opp_cash).
    Reward = normalized terminal cash on the final step, 0 elsewhere."""
    env = make_fn(seed)
    predictor.reset()
    steps = []

    def learner_act(obs, cfg=None):
        pr = predictor.step(essentialize(obs, learner_seat))
        steps.append(pr)
        return pr["action"]

    def opp_act(obs, cfg=None):
        return opponent.act(obs, cfg)

    agents = [learner_act, opp_act] if learner_seat == 0 else \
        [opp_act, learner_act]
    env.run(agents)
    my_cash = float(env.steps[-1][learner_seat]["reward"])
    opp_cash = float(env.steps[-1][1 - learner_seat]["reward"])
    for s in steps:
        s["reward"] = 0.0
        s["done"] = False
    steps[-1]["reward"] = my_cash / 1e5
    steps[-1]["done"] = True
    return steps, my_cash, opp_cash
