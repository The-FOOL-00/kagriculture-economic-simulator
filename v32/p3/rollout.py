# SPDX-License-Identifier: MIT
"""V32 P3 rollout: deterministic policy-vs-expert episodes -> eval/BC batches.

Mirrors v32.p2.rollout (online features + torch act + exact literal emission)
with P3 native decode. Reward terminal-only (for future PPO reuse; P3 runs no
PPO — this module serves closed-loop BC evaluation).
"""

import torch

from v32.p2.features import EpisodeFeatures, unit_ctx
from v32.p2 import actions as A2  # candidate_hash only (literal hashing)
from v32.p3 import codec as C


class Predictor:
    """Live policy wrapper (rollout + eval). Owns per-episode feature state."""

    def __init__(self, model, norm, device="cpu"):
        self.model = model
        self.norm = norm
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
        assert n_u - 1 <= C.MAX_HANDS_CAP
        st = torch.tensor(np.asarray([feat.tolist()]), dtype=torch.float32,
                          device=self.dev)
        uc = torch.tensor(np.asarray([[unit_ctx(ess, j) for j in range(n_u)]]),
                          dtype=torch.float32, device=self.dev)
        vv = torch.ones(1, n_u, dtype=torch.bool, device=self.dev)
        out = self.model.act(st, uc, vv, deterministic=deterministic)
        u = [(o, a, q) for o, a, q in zip(
            out["u_op"][0].tolist(), out["u_arg"][0].tolist(),
            out["u_qty"][0].tolist())]
        m = [(o, i, q) for o, i, q in zip(
            out["m_op"][0].tolist(), out["m_item"][0].tolist(),
            out["m_qty"][0].tolist())]
        act = C.decode_action(u, m)
        ulits = [act["farmer"]] + act["hands"]
        self.prev_act = act
        return {"action": act, "logprob": float(out["logprob"][0]),
                "value": float(out["value"][0]),
                "entropy": float(out["entropy"][0]),
                "u": u, "m": m,
                "hashes": [A2.candidate_hash(x) for x in ulits + act["market"]]}


def run_episode(make_fn, seed, learner_seat, predictor, opponent):
    """Full episode via env.run (validated path; manual stepping leaves
    seat-1 observations uninitialized). Returns (steps, my_cash, opp_cash).
    Reward = normalized terminal cash on the final step, 0 elsewhere."""
    env = make_fn(seed)
    predictor.reset()
    steps = []
    from v32.p2.essentials import essentialize

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
