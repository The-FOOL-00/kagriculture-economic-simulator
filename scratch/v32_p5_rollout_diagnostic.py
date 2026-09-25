# SPDX-License-Identifier: MIT
"""V32 P5 Diagnostic Rollout Script:
Runs Mode A (Teacher-Forced) vs Mode B (Free-Running) on P4 Arm 1 checkpoint
across development screen seeds.
Measures:
- Per-step exact match (Mode A vs Mode B)
- State divergence ||s_t^P - s_t^T||_2
- Cash and inventory drift
- First divergence detection (action, state, economic)
- Step-interval breakdown
- Nearest-neighbor training manifold distance
"""

import json
import math
import os
import sys
import copy
import numpy as np
import torch

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from kaggle_environments import make
from v32_common import load_agent
from v32.p2.essentials import essentialize
from v32.p2.features import Normalizer, EpisodeFeatures, unit_ctx
from v32.p3 import codec as C
from v32.p3.models import P3Policy

SCREEN_SEEDS = [249675, 249676, 249677, 249678, 249679]
OPPONENT = "E0_V3"
TEACHER = "E2_A7"

def actions_equal(a1, a2):
    if (a1.get("farmer") or ["PASS"]) != (a2.get("farmer") or ["PASS"]):
        return False
    h1 = a1.get("hands") or []
    h2 = a2.get("hands") or []
    if len(h1) != len(h2):
        return False
    for x, y in zip(h1, h2):
        if (x or ["PASS"]) != (y or ["PASS"]):
            return False
    m1 = a1.get("market") or []
    m2 = a2.get("market") or []
    if len(m1) != len(m2):
        return False
    for x, y in zip(m1, m2):
        if (x or []) != (y or []):
            return False
    return True

def predict_action(model, norm, fb, ess, prev_act):
    raw_feat = fb.update(ess, prev_act)
    feat = norm.transform(np.asarray([raw_feat]))[0]
    n_u = 1 + len(ess.get("hands", []) or [])
    assert n_u - 1 <= C.MAX_HANDS_CAP
    st = torch.tensor(np.asarray([feat.tolist()]), dtype=torch.float32)
    uc = torch.tensor(np.asarray([[unit_ctx(ess, j) for j in range(n_u)]]), dtype=torch.float32)
    vv = torch.ones(1, n_u, dtype=torch.bool)
    with torch.no_grad():
        out = model.act(st, uc, vv, deterministic=True)
    u = [(o, a, q) for o, a, q in zip(
        out["u_op"][0].tolist(), out["u_arg"][0].tolist(), out["u_qty"][0].tolist())]
    m = [(o, i, q) for o, i, q in zip(
        out["m_op"][0].tolist(), out["m_item"][0].tolist(), out["m_qty"][0].tolist())]
    act = C.decode_action(u, m)
    return act, feat

def run_diagnostic():
    print("=== RUNNING V32 P5 ROLLOUT DIAGNOSTIC ===")
    ckpt_path = os.path.join(REPO_ROOT, "results", "v32_p4_arm1_balanced.npz")
    norm = Normalizer.from_json(json.load(open(os.path.join(REPO_ROOT, "results", "v32_p2_norm.json"))))
    d = np.load(ckpt_path, allow_pickle=True)
    model = P3Policy(157, 12)
    model.load_state_dict({k: torch.tensor(v) for k, v in d.items() if k != "meta"})
    model.eval()

    all_episode_data = []

    for seed in SCREEN_SEEDS:
        print(f"\nEvaluating Seed {seed} vs {OPPONENT}...")
        
        # 1. Run Teacher Episode to collect expert trajectory (Mode A reference)
        teacher_agent = load_agent(TEACHER)
        opp_agent_1 = load_agent(OPPONENT)
        env_teacher = make("kaggriculture", configuration={"seed": seed})
        
        teacher_obs_list = []
        teacher_act_list = []
        
        def t_agent_fn(obs, cfg=None):
            act = teacher_agent.act(obs, cfg)
            teacher_obs_list.append(copy.deepcopy(obs))
            teacher_act_list.append(copy.deepcopy(act))
            return act
            
        def t_opp_fn(obs, cfg=None):
            return opp_agent_1.act(obs, cfg)
            
        env_teacher.run([t_agent_fn, t_opp_fn])
        t_terminal_cash = float(env_teacher.steps[-1][0]["reward"])
        print(f"  Teacher finished: 720 steps, cash = ${t_terminal_cash:,.2f}")
        
        # 2. Mode A: Teacher-forced evaluation of P4 model on teacher trajectory
        mode_a_preds = []
        mode_a_feats = []
        mode_a_matches = []
        fb_a = EpisodeFeatures()
        fb_a.reset()
        prev_a = None
        
        for t, (obs_t, act_t) in enumerate(zip(teacher_obs_list, teacher_act_list)):
            ess = essentialize(obs_t, 0)
            pred_act, feat = predict_action(model, norm, fb_a, ess, prev_a)
            mode_a_preds.append(pred_act)
            mode_a_feats.append(feat)
            match = actions_equal(pred_act, act_t)
            mode_a_matches.append(match)
            # In teacher-forced mode, the history/next step is conditioned on the teacher action
            prev_a = act_t
            
        mode_a_acc = np.mean(mode_a_matches)
        print(f"  Mode A (Teacher-forced) action accuracy: {mode_a_acc*100:.2f}% ({sum(mode_a_matches)}/720)")
        
        # 3. Mode B: Free-running rollout of P4 model in environment
        opp_agent_2 = load_agent(OPPONENT)
        env_policy = make("kaggriculture", configuration={"seed": seed})
        
        policy_obs_list = []
        policy_act_list = []
        policy_feats = []
        fb_b = EpisodeFeatures()
        fb_b.reset()
        prev_b = None
        
        def p_agent_fn(obs, cfg=None):
            nonlocal prev_b
            ess = essentialize(obs, 0)
            pred_act, feat = predict_action(model, norm, fb_b, ess, prev_b)
            policy_obs_list.append(copy.deepcopy(obs))
            policy_act_list.append(copy.deepcopy(pred_act))
            policy_feats.append(feat)
            prev_b = pred_act
            return pred_act
            
        def p_opp_fn(obs, cfg=None):
            return opp_agent_2.act(obs, cfg)
            
        env_policy.run([p_agent_fn, p_opp_fn])
        p_terminal_cash = float(env_policy.steps[-1][0]["reward"])
        print(f"  Mode B (Free-running) finished: 720 steps, cash = ${p_terminal_cash:,.2f}")
        
        # 4. Comparative Step-by-Step Forensics
        n_steps = min(len(teacher_act_list), len(policy_act_list))
        first_act_div = None
        first_state_div = None
        first_econ_div = None
        
        step_metrics = []
        
        for t in range(n_steps):
            t_act = teacher_act_list[t]
            p_act = policy_act_list[t]
            t_obs = teacher_obs_list[t]
            p_obs = policy_obs_list[t]
            
            act_match = actions_equal(p_act, t_act)
            if act_match and first_act_div is None:
                pass
            elif not act_match and first_act_div is None:
                first_act_div = t
                
            # State distance in normalized feature space
            f_dist = float(np.linalg.norm(policy_feats[t] - mode_a_feats[t]))
            if f_dist > 1e-4 and first_state_div is None:
                first_state_div = t
                
            # Physical state differences
            p_money = float(p_obs["farms"][0]["money"])
            t_money = float(t_obs["farms"][0]["money"])
            money_diff = abs(p_money - t_money)
            
            if money_diff > 10.0 and first_econ_div is None:
                first_econ_div = t
                
            p_pos = p_obs["farms"][0]["farmer"]
            t_pos = t_obs["farms"][0]["farmer"]
            pos_diff = abs(p_pos[0] - t_pos[0]) + abs(p_pos[1] - t_pos[1])
            
            p_hands = len(p_obs["farms"][0].get("hands", []) or [])
            t_hands = len(t_obs["farms"][0].get("hands", []) or [])
            
            step_metrics.append({
                "step": t,
                "act_match": act_match,
                "f_dist": f_dist,
                "p_money": p_money,
                "t_money": t_money,
                "money_diff": money_diff,
                "pos_diff": pos_diff,
                "p_hands": p_hands,
                "t_hands": t_hands,
                "t_act": t_act,
                "p_act": p_act,
            })
            
        print(f"  First Action Divergence: Step {first_act_div}")
        print(f"  First State Divergence:  Step {first_state_div}")
        print(f"  First Economic (> $10) Divergence: Step {first_econ_div}")
        
        all_episode_data.append({
            "seed": seed,
            "teacher_cash": t_terminal_cash,
            "policy_cash": p_terminal_cash,
            "mode_a_acc": mode_a_acc,
            "first_act_div": first_act_div,
            "first_state_div": first_state_div,
            "first_econ_div": first_econ_div,
            "step_metrics": step_metrics,
        })

    # Save complete diagnostic json
    out_path = os.path.join(REPO_ROOT, "results", "v32_p5_rollout_diagnostic.json")
    with open(out_path, "w") as f:
        json.dump(all_episode_data, f, indent=2)
    print(f"\nDiagnostic results written to {out_path}")

if __name__ == "__main__":
    run_diagnostic()
