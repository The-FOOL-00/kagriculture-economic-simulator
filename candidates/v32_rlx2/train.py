# SPDX-License-Identifier: MIT
"""Kagriculture V32 RL-X2 Main Training Pipeline.

Orchestrates PPO training, search-target pretraining, and iterative hybrid loops.
"""

from __future__ import annotations
import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import torch

try:
    from action_space import ACTION_SPACE_SIZE
    from rlx2_config import REPO_ROOT, RLX2Config, V32_DEV_HIST, V32_TRAIN
    from env import RLX2Env
    from opponents import OpponentSampler
    from policy import StrategicActor
    from ppo import RolloutBatch, StrategicPPO, compute_gae
    from state import get_feature_dim
    from value import StrategicCritic
except ImportError:
    from candidates.v32_rlx2.action_space import ACTION_SPACE_SIZE
    from candidates.v32_rlx2.rlx2_config import REPO_ROOT, RLX2Config, V32_DEV_HIST, V32_TRAIN
    from candidates.v32_rlx2.env import RLX2Env
    from candidates.v32_rlx2.opponents import OpponentSampler
    from candidates.v32_rlx2.policy import StrategicActor
    from candidates.v32_rlx2.ppo import RolloutBatch, StrategicPPO, compute_gae
    from candidates.v32_rlx2.state import get_feature_dim
    from candidates.v32_rlx2.value import StrategicCritic


def collect_rollouts(
    actor: StrategicActor,
    critic: StrategicCritic,
    config: RLX2Config,
    num_episodes: int,
    sampler: OpponentSampler,
    seed_offset: int = 0
) -> RolloutBatch:
    """Collects rollout batch across multiple episodes."""
    env = RLX2Env(config=config)
    
    b_states = []
    b_actions = []
    b_log_probs = []
    b_rewards = []
    b_values = []
    b_dones = []
    b_masks = []
    
    train_seed_base = V32_TRAIN[0]
    train_seed_count = V32_TRAIN[1] - V32_TRAIN[0] + 1
    
    for ep in range(num_episodes):
        ep_seed = train_seed_base + ((seed_offset + ep) % train_seed_count)
        opp_id = sampler.sample()
        seat = ep % 2
        
        obs, mask = env.reset(seed=ep_seed, opponent_id=opp_id, seat=seat)
        done = False
        
        ep_states = []
        ep_actions = []
        ep_log_probs = []
        ep_rewards = []
        ep_values = []
        ep_dones = []
        ep_masks = []
        
        while not done:
            action, log_prob, _ = actor.get_action(obs, mask)
            val = critic.get_value(obs)
            
            next_obs, reward, done, info = env.step(action)
            next_mask = info["action_mask"]
            
            ep_states.append(obs)
            ep_actions.append(action)
            ep_log_probs.append(log_prob)
            ep_rewards.append(reward)
            ep_values.append(val)
            ep_dones.append(done)
            ep_masks.append(mask)
            
            obs = next_obs
            mask = next_mask
            
        b_states.extend(ep_states)
        b_actions.extend(ep_actions)
        b_log_probs.extend(ep_log_probs)
        b_rewards.extend(ep_rewards)
        b_values.extend(ep_values)
        b_dones.extend(ep_dones)
        b_masks.extend(ep_masks)
        
    states_arr = np.asarray(b_states, dtype=np.float32)
    actions_arr = np.asarray(b_actions, dtype=np.int64)
    log_probs_arr = np.asarray(b_log_probs, dtype=np.float32)
    rewards_arr = np.asarray(b_rewards, dtype=np.float32)
    values_arr = np.asarray(b_values, dtype=np.float32)
    dones_arr = np.asarray(b_dones, dtype=np.bool_)
    masks_arr = np.asarray(b_masks, dtype=np.bool_)
    
    advs, returns = compute_gae(
        rewards=rewards_arr,
        values=values_arr,
        dones=dones_arr,
        next_value=0.0,
        gamma=config.gamma,
        lam=config.gae_lambda
    )
    
    return RolloutBatch(
        states=states_arr,
        actions=actions_arr,
        log_probs=log_probs_arr,
        rewards=rewards_arr,
        values=values_arr,
        dones=dones_arr,
        masks=masks_arr,
        advantages=advs,
        returns=returns
    )


def pretrain_from_targets(
    actor: StrategicActor,
    targets_file: str,
    epochs: int = 10,
    lr: float = 1e-3,
    min_delta: float = 0.0
) -> float:
    """Supervised pretraining of actor policy on search targets (RLX2-F7)."""
    if not os.path.exists(targets_file):
        print(f"Targets file {targets_file} not found; skipping pretraining.")
        return 0.0
        
    states = []
    actions = []
    masks = []
    weights = []
    
    with open(targets_file, "r") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            delta = rec.get("best_delta", 0.0)
            if delta >= min_delta:
                states.append(rec["state_vector"])
                actions.append(rec["best_action"])
                masks.append(rec["action_mask"])
                weights.append(max(1.0, float(delta) / 100.0))
                
    if not states:
        print("No positive targets found in file.")
        return 0.0
        
    s_tensor = torch.tensor(np.asarray(states), dtype=torch.float32)
    a_tensor = torch.tensor(np.asarray(actions), dtype=torch.long)
    m_tensor = torch.tensor(np.asarray(masks), dtype=torch.bool)
    w_tensor = torch.tensor(np.asarray(weights), dtype=torch.float32)
    
    optimizer = torch.optim.Adam(actor.parameters(), lr=lr)
    loss_fn = torch.nn.CrossEntropyLoss(reduction="none")
    
    actor.train()
    final_loss = 0.0
    for ep in range(epochs):
        dist = actor.forward(s_tensor, m_tensor)
        loss = (loss_fn(dist.logits, a_tensor) * w_tensor).mean()
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        final_loss = float(loss.item())
        
    print(f"[SUPERVISED PRETRAIN] {len(states)} targets trained over {epochs} epochs. Final Loss: {final_loss:.4f}")
    return final_loss


def evaluate_policy_dev(
    actor: StrategicActor,
    config: RLX2Config,
    num_eval_seeds: int = 5
) -> Dict[str, float]:
    """Fast validation on dev cohort vs A7."""
    env = RLX2Env(config=config)
    eval_seeds = list(range(V32_DEV_HIST[0], V32_DEV_HIST[0] + num_eval_seeds))
    deltas = []
    cashes = []
    
    for s in eval_seeds:
        for seat in (0, 1):
            obs, mask = env.reset(seed=s, opponent_id="E2_A7", seat=seat)
            done = False
            while not done:
                action, _, _ = actor.get_action(obs, mask, deterministic=True)
                obs, r, done, info = env.step(action)
            cashes.append(info["final_cash"])
            
    return {
        "mean_cash": float(np.mean(cashes)),
        "median_cash": float(np.median(cashes)),
        "min_cash": float(np.min(cashes)),
    }


def train_ppo(
    seed: int = 42,
    state_tier: str = "S2",
    reward_mode: str = "R1",
    total_iterations: int = 10,
    episodes_per_iter: int = 4,
    pretrain_targets_path: Optional[str] = None,
    experiment_id: str = "RLX2-F2"
) -> Dict[str, Any]:
    """Runs complete PPO training cycle with evaluation telemetry."""
    np.random.seed(seed)
    torch.manual_seed(seed)
    
    cfg = RLX2Config(
        state_tier=state_tier,
        reward_mode=reward_mode,
        macro_interval=4
    )
    
    state_dim = get_feature_dim(tier=state_tier)
    action_dim = ACTION_SPACE_SIZE
    
    actor = StrategicActor(state_dim=state_dim, action_dim=action_dim)
    critic = StrategicCritic(state_dim=state_dim)
    ppo = StrategicPPO(actor=actor, critic=critic, config=cfg)
    sampler = OpponentSampler(mode="uniform")
    
    # Optional search pretraining
    if pretrain_targets_path:
        pretrain_from_targets(actor, pretrain_targets_path)
        
    history = []
    best_eval = -1e9
    
    print(f"\n=======================================================")
    print(f"Starting {experiment_id} Training (Seed: {seed}, Tier: {state_tier}, Reward: {reward_mode})")
    print(f"=======================================================")
    
    for it in range(1, total_iterations + 1):
        t0 = time.time()
        rollouts = collect_rollouts(
            actor=actor,
            critic=critic,
            config=cfg,
            num_episodes=episodes_per_iter,
            sampler=sampler,
            seed_offset=it * episodes_per_iter
        )
        
        train_stats = ppo.train_step(rollouts, epochs=4, minibatch_size=64)
        iter_time = time.time() - t0
        
        # Periodic evaluation
        eval_metrics = evaluate_policy_dev(actor, cfg, num_eval_seeds=3)
        mean_eval_cash = eval_metrics["mean_cash"]
        
        # Action distribution in rollouts
        act_counts = {int(a): int(np.sum(rollouts.actions == a)) for a in range(action_dim)}
        follow_a7_pct = (act_counts.get(0, 0) / len(rollouts.actions)) * 100.0
        
        record = {
            "iteration": it,
            "iter_time": iter_time,
            "total_decisions": it * len(rollouts.actions),
            "follow_a7_pct": follow_a7_pct,
            "action_counts": act_counts,
            "mean_reward": float(np.mean(rollouts.rewards)),
            "eval_cash": mean_eval_cash,
            **train_stats
        }
        history.append(record)
        
        print(f"Iter {it:2d}/{total_iterations} | Time: {iter_time:4.1f}s | Dec: {record['total_decisions']:5d} | A7%: {follow_a7_pct:5.1f}% | PG: {train_stats['pg_loss']:7.4f} | VF: {train_stats['v_loss']:7.4f} | Ent: {train_stats['entropy']:5.3f} | Eval: ${mean_eval_cash:,.1f}", flush=True)
        
    out_dir = os.path.join(REPO_ROOT, "candidates", "v32_rlx2", "reports")
    os.makedirs(out_dir, exist_ok=True)
    
    # Save model weights
    ckpt_path = os.path.join(out_dir, f"{experiment_id}_seed{seed}_actor.pt")
    torch.save(actor.state_dict(), ckpt_path)
    
    # Save training curve
    curve_path = os.path.join(out_dir, f"{experiment_id}_seed{seed}_history.json")
    with open(curve_path, "w") as f:
        json.dump(history, f, indent=2)
        
    return {
        "experiment_id": experiment_id,
        "seed": seed,
        "checkpoint": ckpt_path,
        "final_eval": mean_eval_cash,
        "history": history
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="RL-X2 PPO Training")
    parser.add_argument("--exp", type=str, default="RLX2-F2", help="Experiment ID")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--tier", type=str, default="S2", choices=["S0", "S1", "S2", "S3"], help="State tier")
    parser.add_argument("--reward", type=str, default="R1", choices=["R0", "R1", "R2", "R3"], help="Reward mode")
    parser.add_argument("--iters", type=int, default=10, help="Total PPO iterations")
    parser.add_argument("--episodes", type=int, default=4, help="Episodes per iteration")
    parser.add_argument("--targets", type=str, default=None, help="Path to search targets JSONL for pretraining")
    
    args = parser.parse_args()
    print(f"=== Starting RL-X2 Experiment: {args.exp} (Seed {args.seed}) ===", flush=True)
    res = train_ppo(
        seed=args.seed,
        state_tier=args.tier,
        reward_mode=args.reward,
        total_iterations=args.iters,
        episodes_per_iter=args.episodes,
        pretrain_targets_path=args.targets,
        experiment_id=args.exp
    )
    print(f"=== Finished {args.exp} | Final Eval Mean: ${res['final_eval']:,.1f} ===", flush=True)
