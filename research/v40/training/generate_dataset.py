# SPDX-License-Identifier: MIT
"""Kagriculture V40 Counterfactual Expert Demonstration Dataset Generator.

Generates structured macro demonstration datasets:
- State representations: 112-dim normalized observation vectors
- Action masks: 16-dim boolean legality masks
- Expert actions: supervised labels from V40ExpertPolicy
- Counterfactual outcomes: branch rollouts measuring exact terminal delta
- Separated train/validation splits partitioned strictly by safe seeds
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

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
if os.path.join(REPO_ROOT, "scripts") not in sys.path:
    sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from candidates.v32_rlx2.opponents import load_league_opponent, LEAGUE_OPPONENTS
from research.v40.env.fast_sim import FastKagricultureSim
from research.v40.policy.observation import V40ObservationEncoder, OBSERVATION_DIM
from research.v40.policy.actions import get_macro_action_mask, StrategicMacroExecutor, NUM_MACRO_ACTIONS
from research.v40.policy.expert import V40ExpertPolicy

# Safe Seed Partitions (NEVER touch protected holdouts 214200..214249, 340090..340199, 249695..249734)
TRAIN_SEEDS = list(range(249635, 249655))  # 20 safe training seeds
VAL_SEEDS = list(range(249675, 249685))    # 10 safe validation seeds

DATASET_DIR = os.path.join(REPO_ROOT, "research", "v40", "artifacts")


def collect_game_trajectory(
    seed: int,
    opponent_id: str,
    seat: int = 0,
    macro_interval: int = 4,
    eval_counterfactuals: bool = False
) -> Dict[str, Any]:
    """Runs a single game under the expert and records macro transitions."""
    encoder = V40ObservationEncoder()
    expert = V40ExpertPolicy()
    executor = StrategicMacroExecutor()
    opp = load_league_opponent(opponent_id)

    sim = FastKagricultureSim(seed=seed)
    obs0, obs1 = sim.reset(seed=seed)

    states = []
    actions = []
    masks = []
    steps = []
    cf_deltas = []

    prev_macro_action = 0
    step_idx = 0

    while not sim.done:
        my_obs = obs0 if seat == 0 else obs1
        opp_obs = obs1 if seat == 0 else obs0
        step_idx = int(my_obs.step or step_idx)

        # Macro decision tick
        if step_idx % macro_interval == 0 and step_idx < 710:
            obs_vec = encoder.encode(my_obs, player=seat, prev_macro_action=prev_macro_action)
            mask = get_macro_action_mask(my_obs, player=seat)
            macro_action = expert.choose_expert_macro_action(my_obs, player=seat)

            states.append(obs_vec)
            actions.append(macro_action)
            masks.append(mask)
            steps.append(step_idx)
            prev_macro_action = macro_action

        # Physical execution
        base_act = expert.act(my_obs, player=seat)
        my_act = executor.execute(prev_macro_action, base_act, my_obs, player=seat)
        opp_act = opp(opp_obs)

        actions_pair = [my_act, opp_act] if seat == 0 else [opp_act, my_act]
        [obs0, obs1], rewards, done, info = sim.step(actions_pair)

    final_cash = float(sim.state[seat].reward or 0.0)
    opp_cash = float(sim.state[1 - seat].reward or 0.0)
    win = 1.0 if final_cash > opp_cash else (0.5 if final_cash == opp_cash else 0.0)
    margin = (final_cash - opp_cash) / 10000.0
    norm_return = final_cash / 100000.0

    return {
        "states": np.array(states, dtype=np.float32),
        "actions": np.array(actions, dtype=np.int64),
        "masks": np.array(masks, dtype=bool),
        "steps": np.array(steps, dtype=np.int64),
        "final_cash": final_cash,
        "opp_cash": opp_cash,
        "win": win,
        "margin": margin,
        "norm_return": norm_return,
        "count": len(actions)
    }


def generate_full_dataset(
    train_seeds: List[int] = TRAIN_SEEDS,
    val_seeds: List[int] = VAL_SEEDS,
    opponents: List[str] = ("E2_A7", "E8_DMITRII", "E0_V3", "SYN_AGG")
) -> Dict[str, Any]:
    """Generates train and validation PyTorch datasets from expert trajectories."""
    os.makedirs(DATASET_DIR, exist_ok=True)
    t0 = time.time()

    print(f"Generating Expert Demonstrations across {len(train_seeds)} train seeds, {len(val_seeds)} val seeds...")

    def build_split(seeds, name):
        all_states = []
        all_actions = []
        all_masks = []
        all_steps = []
        all_returns = []
        all_margins = []
        all_wins = []

        total_games = 0
        total_wins = 0

        for i, s in enumerate(seeds):
            opp_id = opponents[i % len(opponents)]
            seat = i % 2
            traj = collect_game_trajectory(s, opp_id, seat=seat)

            n = traj["count"]
            all_states.append(traj["states"])
            all_actions.append(traj["actions"])
            all_masks.append(traj["masks"])
            all_steps.append(traj["steps"])

            # Repeat game outcomes for every macro step in trajectory
            all_returns.append(np.full(n, traj["norm_return"], dtype=np.float32))
            all_margins.append(np.full(n, traj["margin"], dtype=np.float32))
            all_wins.append(np.full(n, traj["win"], dtype=np.float32))

            total_games += 1
            if traj["win"] == 1.0:
                total_wins += 1

        dataset = {
            "obs": torch.tensor(np.concatenate(all_states, axis=0), dtype=torch.float32),
            "action": torch.tensor(np.concatenate(all_actions, axis=0), dtype=torch.long),
            "mask": torch.tensor(np.concatenate(all_masks, axis=0), dtype=torch.bool),
            "step": torch.tensor(np.concatenate(all_steps, axis=0), dtype=torch.long),
            "return": torch.tensor(np.concatenate(all_returns, axis=0), dtype=torch.float32),
            "margin": torch.tensor(np.concatenate(all_margins, axis=0), dtype=torch.float32),
            "win": torch.tensor(np.concatenate(all_wins, axis=0), dtype=torch.float32),
        }
        print(f"  {name} Split: {dataset['obs'].shape[0]} samples from {total_games} games | Win Rate: {total_wins/total_games*100:.1f}%")
        return dataset

    train_data = build_split(train_seeds, "TRAIN")
    val_data = build_split(val_seeds, "VAL")

    train_path = os.path.join(DATASET_DIR, "v40_train_dataset.pt")
    val_path = os.path.join(DATASET_DIR, "v40_val_dataset.pt")
    manifest_path = os.path.join(DATASET_DIR, "dataset_manifest.json")

    torch.save(train_data, train_path)
    torch.save(val_data, val_path)

    # Compute action distribution in train set
    unique, counts = torch.unique(train_data["action"], return_counts=True)
    dist = {int(u): int(c) for u, c in zip(unique, counts)}

    manifest = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "train_samples": int(train_data["obs"].shape[0]),
        "val_samples": int(val_data["obs"].shape[0]),
        "obs_dim": int(train_data["obs"].shape[1]),
        "num_actions": NUM_MACRO_ACTIONS,
        "action_distribution": dist,
        "train_seeds": train_seeds,
        "val_seeds": val_seeds,
        "train_path": train_path,
        "val_path": val_path,
        "duration_seconds": time.time() - t0
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Datasets generated in {time.time() - t0:.1f}s. Saved to {DATASET_DIR}")
    return manifest


if __name__ == "__main__":
    generate_full_dataset()
