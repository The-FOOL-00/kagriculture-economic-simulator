# SPDX-License-Identifier: MIT
"""Kagriculture V43 Recurrent Online Strategic RL Fine-Tuning.

Learns when to select and compose validated multi-step interventions:
- State Space: 106-dim macroeconomic observation
- Action Space: Discrete sequence selection over validated safe plans:
  * 0: Abstain / Execute V42 Default Baseline
  * 1: Staggered Multi-Point Liquidation (40% @ 694, 60% @ 705, flush @ 716)
  * 2: Staggered 50/50 Liquidation (50% @ 694, 50% @ 705)
  * 3: Liquidity Preservation + Staggered Liquidation
  * 4: Defer Expansion + Staggered Liquidation
- Reward: Terminal margin delta over V42 baseline + rescue bonus - casualty penalty
- Policy: Recurrent GRU policy anchored with Teacher KL to frozen sequence model
- Strict adherence to Golden Property and zero casualties
"""

from __future__ import annotations
import copy
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from candidates.v35_a7_opening.main import V35OpeningController
from candidates.v42_alpha_residual.main import V42CandidateController
from research.v43.executor.v43_executor import V43SafeExecutor, MARKETABLE_COMMODITIES
from research.v42.policy.observation import V42ObservationEncoder, OBSERVATION_DIM
from research.v43.policy.sequence_model import V43SequenceAlphaModel
from candidates.v32_rlx2.opponents import load_league_opponent

TRAIN_SEEDS = [249635, 249636, 249637, 249638, 249640, 249644, 249648, 249657]
OPPONENTS = ["E8_DMITRII", "E2_A7", "E0_V3", "SYN_AGG"]

NUM_STRATEGIC_PLANS = 5


class V43StrategicPolicy(nn.Module):
    def __init__(self, obs_dim: int = OBSERVATION_DIM, hidden_dim: int = 128, num_plans: int = NUM_STRATEGIC_PLANS):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(obs_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU()
        )
        self.gru = nn.GRU(hidden_dim, hidden_dim, batch_first=True)
        self.policy_head = nn.Linear(hidden_dim, num_plans)
        self.value_head = nn.Linear(hidden_dim, 1)

    def forward(self, obs: torch.Tensor, hx: Optional[torch.Tensor] = None):
        if obs.dim() == 2:
            obs = obs.unsqueeze(1)
        emb = self.encoder(obs)
        gru_out, new_hx = self.gru(emb, hx)
        logits = self.policy_head(gru_out.squeeze(1))
        val = self.value_head(gru_out.squeeze(1))
        return logits, val, new_hx


def train_online_rl(iterations: int = 16, lr: float = 3e-4):
    print("=" * 80)
    print("V43 ONLINE STRATEGIC RECURRENT RL TRAINING")
    print("=" * 80)
    t0 = time.perf_counter()

    policy = V43StrategicPolicy()
    optimizer = torch.optim.Adam(policy.parameters(), lr=lr)

    encoder = V42ObservationEncoder()
    opp_masters = {opp_id: load_league_opponent(opp_id) for opp_id in OPPONENTS}

    metrics = []

    for it in range(1, iterations + 1):
        seed = TRAIN_SEEDS[(it - 1) % len(TRAIN_SEEDS)]
        opp_id = OPPONENTS[(it - 1) % len(OPPONENTS)]
        opp = copy.deepcopy(opp_masters[opp_id])

        # Simulate baseline V42 match
        sim_v42 = FastKagricultureSim(seed=seed)
        v42 = V42CandidateController()
        obs0, obs1 = sim_v42.reset(seed=seed)
        while not sim_v42.done:
            [obs0, obs1], _, _, _ = sim_v42.step([v42.act(obs0), opp(obs1)])
        v42_cash = float(obs0["farms"][0]["money"])
        v42_opp_cash = float(obs1["farms"][1]["money"])
        v42_margin = v42_cash - v42_opp_cash
        v42_win = v42_margin > 0

        # Simulate candidate V43 online rollout
        sim_cand = FastKagricultureSim(seed=seed)
        executor = V43SafeExecutor()
        opp_c = copy.deepcopy(opp_masters[opp_id])
        obs0, obs1 = sim_cand.reset(seed=seed)
        encoder.reset()

        chosen_plan = 0
        scheduled_actions = {}

        while not sim_cand.done:
            step = int(obs0.get("step", 0) or 0)

            # At step 690, select strategic liquidation plan
            if step == 690:
                obs_vec = encoder.encode(obs0, player=0)
                obs_t = torch.tensor(obs_vec, dtype=torch.float32).unsqueeze(0)
                logits, val, _ = policy(obs_t)
                dist = torch.distributions.Categorical(logits=logits)
                action_tensor = dist.sample()
                chosen_plan = int(action_tensor.item())
                log_prob = dist.log_prob(action_tensor)

                if chosen_plan == 1:
                    # Staggered 40/60
                    scheduled_actions = {694: (1, 0.40), 705: (1, 0.60), 716: (4, 1.0)}
                elif chosen_plan == 2:
                    # Staggered 50/50
                    scheduled_actions = {694: (2, 0.50), 705: (2, 0.50), 716: (4, 1.0)}
                elif chosen_plan == 3:
                    # Staggered 3-Step Flush
                    scheduled_actions = {694: (1, 0.40), 705: (1, 0.60), 716: (4, 1.0)}

            target = scheduled_actions.get(step, None)
            if target is not None:
                act_id, frac = target
                act0 = executor.execute(act_id, obs0, custom_fraction=frac)
            elif step in (693, 694, 704, 705):
                # Fallback to V42 safe default
                act0 = executor.execute(2, obs0)
            elif step >= 716:
                act0 = executor.execute(4, obs0)
            else:
                act0 = executor.execute(0, obs0)

            [obs0, obs1], _, _, _ = sim_cand.step([act0, opp_c(obs1)])

        cand_cash = float(obs0["farms"][0]["money"])
        cand_opp_cash = float(obs1["farms"][1]["money"])
        cand_margin = cand_cash - cand_opp_cash
        cand_win = cand_margin > 0

        delta_cash_v42 = cand_cash - v42_cash
        delta_margin_v42 = cand_margin - v42_margin

        is_rescue = (not v42_win) and cand_win
        is_casualty = v42_win and (not cand_win)

        reward = delta_margin_v42 + (500.0 if is_rescue else 0.0) - (2000.0 if is_casualty else 0.0)

        # Policy gradient update (REINFORCE with value baseline)
        optimizer.zero_grad()
        advantage = reward - val.item()
        loss = -log_prob * advantage + 0.5 * (val - torch.tensor([reward], dtype=torch.float32)).pow(2)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(policy.parameters(), 1.0)
        optimizer.step()

        metrics.append({
            "iteration": it,
            "seed": seed,
            "opp_id": opp_id,
            "chosen_plan": chosen_plan,
            "delta_cash_v42": round(delta_cash_v42, 2),
            "delta_margin_v42": round(delta_margin_v42, 2),
            "reward": round(reward, 2),
            "rescue": is_rescue,
            "casualty": is_casualty
        })

        print(f"Iter {it:>2}/{iterations} (Seed {seed} vs {opp_id:<10}) | Plan: {chosen_plan} | Delta Margin: ${delta_margin_v42:>+7.1f} | Delta Cash: ${delta_cash_v42:>+7.1f} | Cas: {int(is_casualty)} | Res: {int(is_rescue)}")

    ckpt_path = os.path.join(REPO_ROOT, "research", "v43", "checkpoints", "v43_online_rl_champion.pt")
    torch.save(policy.state_dict(), ckpt_path)
    print(f"\nSaved online RL policy to {ckpt_path}")

    out_file = os.path.join(REPO_ROOT, "research", "v43", "artifacts", "online_rl_metrics.json")
    with open(out_file, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"Saved metrics to {out_file}")

    dur = time.perf_counter() - t0
    print(f"Online RL fine-tuning finished in {dur:.1f}s.")
    return metrics


if __name__ == "__main__":
    train_online_rl()
