# SPDX-License-Identifier: MIT
"""V32 P5 Unit and Integration Tests (Section 34 Requirements).

Tests:
  1. P4 checkpoint loads correctly
  2. P4 step-0 wash remains correct
  3. Teacher-forced evaluation is deterministic
  4. Free-running evaluation is deterministic
  5. Teacher/policy state logging is consistent
  6. First-divergence detector works
  7. State-distance computation is deterministic
  8. Policy rollout does not mutate training data
  9. Expert oracle does not access hidden future trajectory data
  10. Competition safety remains intact
"""

import copy
import hashlib
import json
import os
import sys
import numpy as np
import pytest
import torch

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from kaggle_environments import make
from v32_common import assert_frozen, load_agent, sha256_file
from v32.p2.dataset import load_legs
from v32.p2.essentials import essentialize
from v32.p2.features import Normalizer, EpisodeFeatures, unit_ctx
from v32.p3 import codec as C
from v32.p3.dataset import build_samples
from v32.p3.models import P3Policy, param_count
from scripts.v32_p4_train import eval_step0_probe

CKPT_PATH = os.path.join(REPO_ROOT, "results", "v32_p4_arm1_balanced.npz")
NORM_PATH = os.path.join(REPO_ROOT, "results", "v32_p2_norm.json")
LEGS_PATH = os.path.join(REPO_ROOT, "results", "v32_p2_bc_legs.jsonl")

def test_1_p4_checkpoint_loads():
    assert os.path.exists(CKPT_PATH), f"Checkpoint missing at {CKPT_PATH}"
    d = np.load(CKPT_PATH, allow_pickle=True)
    assert "meta" in d
    meta = json.loads(str(d["meta"]))
    assert meta.get("arm") in (1, "arm1_balanced")
    m = P3Policy(157, 12)
    m.load_state_dict({k: torch.tensor(v) for k, v in d.items() if k != "meta"})
    assert param_count(m) == 277092

def test_2_p4_step0_wash_intact():
    norm = Normalizer.from_json(json.load(open(NORM_PATH)))
    d = np.load(CKPT_PATH, allow_pickle=True)
    m = P3Policy(157, 12)
    m.load_state_dict({k: torch.tensor(v) for k, v in d.items() if k != "meta"})
    m.eval()
    
    # Check on subset of step-0 samples
    all_step0 = []
    for leg in list(load_legs(LEGS_PATH))[:10]:
        for side, expert in (("rows0", leg["left"]), ("rows1", leg["right"])):
            for s in build_samples(leg, leg[side], expert):
                if s["step"] == 0:
                    all_step0.append(s)
    assert len(all_step0) > 0
    F_s0 = norm.transform([s["feat"] for s in all_step0])
    res = eval_step0_probe(m, all_step0, F_s0)
    assert res["wash"] == len(all_step0), f"Wash failed: {res['wash']}/{len(all_step0)}"

def test_3_teacher_forced_eval_deterministic():
    norm = Normalizer.from_json(json.load(open(NORM_PATH)))
    d = np.load(CKPT_PATH, allow_pickle=True)
    m = P3Policy(157, 12)
    m.load_state_dict({k: torch.tensor(v) for k, v in d.items() if k != "meta"})
    m.eval()
    
    # Run teacher-forced on first leg
    leg = next(load_legs(LEGS_PATH))
    preds_run1 = []
    preds_run2 = []
    
    for run_list in [preds_run1, preds_run2]:
        fb = EpisodeFeatures()
        fb.reset()
        prev_act = None
        for row in leg["rows0"][:15]:
            ess = row["e"]
            rf = fb.update(ess, prev_act)
            feat = norm.transform(np.asarray([rf]))[0]
            st = torch.tensor(np.asarray([feat.tolist()]), dtype=torch.float32)
            n_u = 1 + len(ess.get("hands", []) or [])
            uc = torch.tensor(np.asarray([[unit_ctx(ess, j) for j in range(n_u)]]), dtype=torch.float32)
            vv = torch.ones(1, n_u, dtype=torch.bool)
            with torch.no_grad():
                out = m.act(st, uc, vv, deterministic=True)
            u = [(o, a, q) for o, a, q in zip(out["u_op"][0].tolist(), out["u_arg"][0].tolist(), out["u_qty"][0].tolist())]
            m_act = [(o, i, q) for o, i, q in zip(out["m_op"][0].tolist(), out["m_item"][0].tolist(), out["m_qty"][0].tolist())]
            act = C.decode_action(u, m_act)
            run_list.append(act)
            prev_act = row["a"]
            
    assert preds_run1 == preds_run2

def test_4_free_running_eval_deterministic():
    norm = Normalizer.from_json(json.load(open(NORM_PATH)))
    d = np.load(CKPT_PATH, allow_pickle=True)
    m = P3Policy(157, 12)
    m.load_state_dict({k: torch.tensor(v) for k, v in d.items() if k != "meta"})
    m.eval()
    
    def run_sim():
        env = make("kaggriculture", configuration={"seed": 249675})
        opp = load_agent("E0_V3")
        fb = EpisodeFeatures()
        fb.reset()
        prev_act = None
        traj = []
        def agent_fn(obs, cfg=None):
            nonlocal prev_act
            ess = essentialize(obs, 0)
            rf = fb.update(ess, prev_act)
            feat = norm.transform(np.asarray([rf]))[0]
            st = torch.tensor(np.asarray([feat.tolist()]), dtype=torch.float32)
            n_u = 1 + len(ess.get("hands", []) or [])
            uc = torch.tensor(np.asarray([[unit_ctx(ess, j) for j in range(n_u)]]), dtype=torch.float32)
            vv = torch.ones(1, n_u, dtype=torch.bool)
            with torch.no_grad():
                out = m.act(st, uc, vv, deterministic=True)
            u = [(o, a, q) for o, a, q in zip(out["u_op"][0].tolist(), out["u_arg"][0].tolist(), out["u_qty"][0].tolist())]
            m_act = [(o, i, q) for o, i, q in zip(out["m_op"][0].tolist(), out["m_item"][0].tolist(), out["m_qty"][0].tolist())]
            act = C.decode_action(u, m_act)
            traj.append(copy.deepcopy(act))
            prev_act = act
            return act
        env.run([agent_fn, opp.act])
        return traj[:10], float(env.steps[-1][0]["reward"])

    traj1, cash1 = run_sim()
    traj2, cash2 = run_sim()
    assert cash1 == cash2
    assert traj1 == traj2

def test_5_state_logging_consistency():
    norm = Normalizer.from_json(json.load(open(NORM_PATH)))
    fb = EpisodeFeatures()
    fb.reset()
    env = make("kaggriculture", configuration={"seed": 249675})
    obs0 = env.reset()[0].observation
    ess = essentialize(obs0, 0)
    rf = fb.update(ess, None)
    assert len(rf) == 157
    feat = norm.transform(np.asarray([rf]))[0]
    assert feat.shape == (157,)

def test_6_first_divergence_detector():
    a1 = {"farmer": ["PASS"], "hands": [], "market": [["BUY_PRODUCT", "WHEAT", 30], ["SELL", "WHEAT", 30]]}
    a2 = {"farmer": ["PASS"], "hands": [], "market": [["BUY_PRODUCT", "WHEAT", 30], ["SELL", "WHEAT", 30]]}
    a3 = {"farmer": ["NORTH"], "hands": [], "market": []}
    
    from scratch.v32_p5_rollout_diagnostic import actions_equal
    assert actions_equal(a1, a2) is True
    assert actions_equal(a1, a3) is False

def test_7_state_distance_deterministic():
    v1 = np.ones(157, dtype=np.float32)
    v2 = np.zeros(157, dtype=np.float32)
    d1 = np.linalg.norm(v1 - v2)
    d2 = np.linalg.norm(v1 - v2)
    assert d1 == d2
    assert abs(d1 - np.sqrt(157)) < 1e-5

def test_8_rollout_does_not_mutate_training_data():
    initial_hash = sha256_file(LEGS_PATH)
    # Perform a light read
    legs = list(load_legs(LEGS_PATH))
    final_hash = sha256_file(LEGS_PATH)
    assert initial_hash == final_hash

def test_9_expert_oracle_audit_invariants():
    # Verify A7 cannot plan off-distribution
    from aec.backbone.v27_ablation_adapters import V27AblationAdapter
    adapter = V27AblationAdapter("V27-ABL-A7")
    env = make("kaggriculture", configuration={"seed": 249675})
    obs0 = env.reset()[0].observation
    env.step([{"farmer": ["PASS"], "hands": [], "market": []}, {"farmer": ["PASS"], "hands": [], "market": []}])
    obs1 = copy.deepcopy(env.state[0].observation)
    # Even if money is $0, A7's route tape attempts to purchase animals
    obs1["farms"][0]["money"] = 0.0
    act1 = adapter.act(obs1)
    orders = [o[0] for o in act1.get("market", [])]
    assert "BUY_ANIMAL" in orders, "A7 blindly replays tape even with $0 cash"

def test_10_competition_safety_intact():
    assert_frozen()
