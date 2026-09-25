# SPDX-License-Identifier: MIT
"""Kagriculture V38 Bounded Residual PPO Trainer.

Fine-tunes the BC-initialized macro actor-critic with bounded residual options,
action masking, fail-closed safety fallback, and GAE advantage estimation.
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
import torch.optim as optim
from kaggle_environments import make

try:
    from config import (
        SCRATCH_DIR, NUM_MACRO_ACTIONS, SAFE_TRAIN_SEEDS, SAFE_DEV_SEEDS,
        assert_seed_safe, DEFAULT_MACRO_HORIZON
    )
    from heuristic import V38DeterministicExpert
    from macro_options import execute_macro_option, get_macro_action_mask
    from policy import MacroActorCritic
    from safety import SafetyEnforcer
    from state_features import StateAbstraction, extract_state_abstraction, vectorize_economic_features
except ImportError:
    from candidates.v38_heuristic_ppo.config import (
        SCRATCH_DIR, NUM_MACRO_ACTIONS, SAFE_TRAIN_SEEDS, SAFE_DEV_SEEDS,
        assert_seed_safe, DEFAULT_MACRO_HORIZON
    )
    from candidates.v38_heuristic_ppo.heuristic import V38DeterministicExpert
    from candidates.v38_heuristic_ppo.macro_options import execute_macro_option, get_macro_action_mask
    from candidates.v38_heuristic_ppo.policy import MacroActorCritic
    from candidates.v38_heuristic_ppo.safety import SafetyEnforcer
    from candidates.v38_heuristic_ppo.state_features import (
        StateAbstraction, extract_state_abstraction, vectorize_economic_features
    )

from candidates.v32_rlx2.opponents import load_league_opponent, LEAGUE_OPPONENTS


PPO_CHECKPOINT_PATH = os.path.join(SCRATCH_DIR, "ppo_policy.pt")
PPO_METRICS_PATH = os.path.join(SCRATCH_DIR, "ppo_metrics.json")


def _get_shared_obs(env: Any, pos: int) -> Dict[str, Any]:
    obs = copy.deepcopy(env.steps[-1][pos]["observation"])
    for k in ("step", "market", "town", "day", "hour"):
        if k in env.steps[-1][0]["observation"] and k not in obs:
            obs[k] = env.steps[-1][0]["observation"][k]
    return obs


def collect_macro_episode(
    env: Any,
    policy: MacroActorCritic,
    seed: int,
    opponent_id: str,
    seat: int = 0,
    macro_interval: int = 4,
    use_safety_fallback: bool = True
) -> Dict[str, Any]:
    """Runs a single episode under the policy and records transitions."""
    assert_seed_safe(seed)
    
    expert = V38DeterministicExpert()
    opp_fn = load_league_opponent(opponent_id)
    safety = SafetyEnforcer() if use_safety_fallback else None
    
    env.reset()
    
    states = []
    actions = []
    masks = []
    log_probs = []
    values = []
    rewards = []
    
    step_idx = 0
    prev_econ = None
    active_macro_option = 0
    active_macro_remaining = 0
    interventions = 0
    
    while not env.done:
        p_obs = _get_shared_obs(env, seat)
        opp_obs = _get_shared_obs(env, 1 - seat)
        step_idx = int(p_obs.get("step", step_idx) or step_idx)
        
        state_abs = extract_state_abstraction(p_obs, player=seat, prev_econ=prev_econ)
        prev_econ = state_abs.economic
        base_act = expert.get_base_action(p_obs)
        opp_act = opp_fn(opp_obs)
        
        # Decision point: every macro_interval steps
        if active_macro_remaining <= 0 and (step_idx % macro_interval == 0) and (step_idx < 710):
            mask = get_macro_action_mask(state_abs)
            s_vec = vectorize_economic_features(state_abs.economic, state_abs.physical)
            
            s_tensor = torch.tensor(s_vec, dtype=torch.float32).unsqueeze(0)
            m_tensor = torch.tensor(mask, dtype=torch.bool).unsqueeze(0)
            
            with torch.no_grad():
                act_tensor, lp_tensor, _, val_tensor, conf_tensor = policy.get_action_and_value(
                    s_tensor, m_tensor, deterministic=False
                )
            
            raw_action = act_tensor.item()
            conf = conf_tensor.item()
            
            if safety:
                approved_act, dur, is_int, _ = safety.evaluate_safety(raw_action, conf, state_abs)
                if is_int:
                    interventions += 1
            else:
                approved_act = raw_action
                dur = macro_interval
                if approved_act != 0:
                    interventions += 1
                    
            active_macro_option = approved_act
            active_macro_remaining = dur
            
            states.append(s_vec)
            actions.append(raw_action)
            masks.append(mask)
            log_probs.append(lp_tensor.item())
            values.append(val_tensor.item())
            # Reward placeholder, computed retroactively
            rewards.append(0.0)
            
        # Execute turn action
        if active_macro_remaining > 0 and active_macro_option != 0:
            cand_act, ok = execute_macro_option(active_macro_option, base_act, state_abs, p_obs)
            p_act = cand_act if ok else base_act
            active_macro_remaining -= 1
        else:
            p_act = base_act
            active_macro_remaining = 0
            
        if seat == 0:
            env.step([p_act, opp_act])
        else:
            env.step([opp_act, p_act])
            
    c_cash = float(env.steps[-1][seat]["reward"] or 0.0)
    o_cash = float(env.steps[-1][1 - seat]["reward"] or 0.0)
    win = 1.0 if c_cash > o_cash else (0.5 if c_cash == o_cash else 0.0)
    
    # Differential terminal reward
    # Normalize cash reward relative to standard baseline (~$100k)
    term_reward = (c_cash - o_cash) / 10000.0
    if len(rewards) > 0:
        rewards[-1] = term_reward
        
    return {
        "states": states,
        "actions": actions,
        "masks": masks,
        "log_probs": log_probs,
        "values": values,
        "rewards": rewards,
        "cand_cash": c_cash,
        "opp_cash": o_cash,
        "win": win,
        "interventions": interventions
    }


def train_ppo(
    bc_init_path: Optional[str] = None,
    output_checkpoint: str = PPO_CHECKPOINT_PATH,
    output_metrics: str = PPO_METRICS_PATH,
    total_iterations: int = 15,
    episodes_per_iter: int = 6,
    lr: float = 3e-4,
    clip_eps: float = 0.2,
    entropy_coef: float = 0.01,
    value_coef: float = 0.5,
    seeds: Optional[List[int]] = None,
    opponents: Optional[List[str]] = None,
    use_safety_fallback: bool = True
) -> Dict[str, Any]:
    """PPO fine-tuning loop."""
    os.makedirs(os.path.dirname(output_checkpoint), exist_ok=True)
    seeds = seeds or SAFE_TRAIN_SEEDS[:6]
    opponents = opponents or ["E2_A7", "E8_DMITRII", "SYN_AGG"]
    
    model = MacroActorCritic()
    if bc_init_path and os.path.exists(bc_init_path):
        print(f"Loading BC initialization from {bc_init_path}...")
        model.load_state_dict(torch.load(bc_init_path, weights_only=True))
    else:
        print("Initializing PPO from random initialization (Control).")
        
    optimizer = optim.Adam(model.parameters(), lr=lr)
    
    history = []
    print(f"Starting PPO fine-tuning: {total_iterations} iterations, {episodes_per_iter} episodes/iter...")
    
    for it in range(1, total_iterations + 1):
        t0 = time.time()
        batch_states = []
        batch_actions = []
        batch_masks = []
        batch_log_probs = []
        batch_values = []
        batch_rewards = []
        
        iter_cash = []
        iter_wins = []
        iter_interventions = []
        
        for ep in range(episodes_per_iter):
            seed = seeds[(it * episodes_per_iter + ep) % len(seeds)]
            opp = opponents[ep % len(opponents)]
            seat = ep % 2
            
            env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
            ep_data = collect_macro_episode(
                env=env, policy=model, seed=seed, opponent_id=opp,
                seat=seat, use_safety_fallback=use_safety_fallback
            )
            
            if ep_data["states"]:
                batch_states.extend(ep_data["states"])
                batch_actions.extend(ep_data["actions"])
                batch_masks.extend(ep_data["masks"])
                batch_log_probs.extend(ep_data["log_probs"])
                batch_values.extend(ep_data["values"])
                batch_rewards.extend(ep_data["rewards"])
                
            iter_cash.append(ep_data["cand_cash"])
            iter_wins.append(ep_data["win"])
            iter_interventions.append(ep_data["interventions"])
            
        if not batch_states:
            continue
            
        # Compute simple returns & advantages
        returns = []
        discounted = 0.0
        for r in reversed(batch_rewards):
            discounted = r + 0.99 * discounted
            returns.insert(0, discounted)
            
        b_obs = torch.tensor(np.array(batch_states), dtype=torch.float32)
        b_act = torch.tensor(np.array(batch_actions), dtype=torch.long)
        b_mask = torch.tensor(np.array(batch_masks), dtype=torch.bool)
        b_old_lp = torch.tensor(np.array(batch_log_probs), dtype=torch.float32)
        b_returns = torch.tensor(np.array(returns), dtype=torch.float32)
        b_old_val = torch.tensor(np.array(batch_values), dtype=torch.float32)
        
        advantages = b_returns - b_old_val
        if len(advantages) > 1 and advantages.std() > 1e-6:
            advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
            
        # PPO Update (4 epochs per iteration)
        model.train()
        for _ in range(4):
            _, new_lp, entropy, new_val, _ = model.get_action_and_value(
                b_obs, b_mask, action=b_act
            )
            ratio = torch.exp(new_lp - b_old_lp)
            surr1 = ratio * advantages
            surr2 = torch.clamp(ratio, 1.0 - clip_eps, 1.0 + clip_eps) * advantages
            policy_loss = -torch.min(surr1, surr2).mean()
            value_loss = F.mse_loss(new_val, b_returns)
            entropy_loss = -entropy.mean()
            
            loss = policy_loss + value_coef * value_loss + entropy_coef * entropy_loss
            
            optimizer.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=0.5)
            optimizer.step()
            
        elapsed = time.time() - t0
        mean_cash = float(np.mean(iter_cash))
        win_rate = float(np.mean(iter_wins)) * 100.0
        mean_interv = float(np.mean(iter_interventions))
        
        iter_log = {
            "iteration": it,
            "mean_cash": mean_cash,
            "win_rate": win_rate,
            "mean_interventions": mean_interv,
            "policy_loss": policy_loss.item(),
            "value_loss": value_loss.item(),
            "entropy": entropy.mean().item(),
            "elapsed_s": elapsed
        }
        history.append(iter_log)
        print(f"Iter {it:02d} | Cash: ${mean_cash:.1f} | WR: {win_rate:.1f}% | Interv: {mean_interv:.1f} | Loss: {policy_loss.item():.4f} ({elapsed:.1f}s)")
        
    torch.save(model.state_dict(), output_checkpoint)
    
    final_res = {
        "iterations": total_iterations,
        "final_cash": history[-1]["mean_cash"],
        "final_win_rate": history[-1]["win_rate"],
        "final_interventions": history[-1]["mean_interventions"],
        "checkpoint": output_checkpoint,
        "history": history
    }
    with open(output_metrics, "w", encoding="utf-8") as f:
        json.dump(final_res, f, indent=2)
        
    return final_res
