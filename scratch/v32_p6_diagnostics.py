# SPDX-License-Identifier: MIT
import os, sys, json, torch
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from v32.p2.essentials import essentialize
from v32.p2.features import Normalizer
from v32.p3 import codec as C
from v32.p3.models import P3Policy
from v32.p3.rollout import Predictor
from v32_common import load_agent
from kaggle_environments import make

norm = json.load(open(os.path.join(REPO_ROOT, "results", "v32_p2_norm.json")))
normalizer = Normalizer.from_json(norm)

# Load P5 Arm 2 model
model = P3Policy(157, 12)
d = np.load(os.path.join(REPO_ROOT, "results", "v32_p5_arm2_early_weighting.npz"), allow_pickle=True)
model.load_state_dict({k: torch.tensor(v) for k, v in d.items() if k != "meta"})
model.eval()

seed = 249675

# 1. Run Teacher Episode (A7)
env_t = make("kaggriculture", configuration={"seed": seed})
a7 = load_agent("E2_A7")
opp = load_agent("E0_V3")

t_obs_history = []
t_act_history = []
def t_act(obs, cfg=None):
    t_obs_history.append(essentialize(obs, 0))
    act = a7.act(obs, cfg)
    t_act_history.append(act)
    return act

def opp_act(obs, cfg=None):
    return opp.act(obs, cfg)

env_t.run([t_act, opp_act])

print("=== STEP 0, 1, 2 TEACHER INSPECTION ===")
for st in range(3):
    ess = t_obs_history[st]
    act = t_act_history[st]
    print(f"Teacher Step {st}: Pos={ess['farmer']}, Money={ess['money']:.1f}, Shed={ess['shed']}, Hands={len(ess['hands'])}")
    print(f"  Teacher Action: {act}")

# 2. Run Free-Running Policy Episode (P5 Arm 2)
pred = Predictor(model, normalizer)
pred.reset()
env_p = make("kaggriculture", configuration={"seed": seed})
p_obs_history = []
p_act_history = []

def p_act(obs, cfg=None):
    ess = essentialize(obs, 0)
    p_obs_history.append(ess)
    pr = pred.step(ess, deterministic=True)
    p_act_history.append(pr)
    return pr["action"]

env_p.run([p_act, opp_act])

print("\n=== STEP 0, 1, 2 POLICY INSPECTION ===")
for st in range(3):
    ess = p_obs_history[st]
    act = p_act_history[st]["action"]
    print(f"Policy Step {st}: Pos={ess['farmer']}, Money={ess['money']:.1f}, Shed={ess['shed']}, Hands={len(ess['hands'])}")
    print(f"  Policy Action: {act}")

# 3. Check State Differences at Step 2 Before Step-2 Action
t_s2 = t_obs_history[2]
p_s2 = p_obs_history[2]

print("\n=== STEP 2 PRE-ACTION STATE COMPARISON ===")
print("Teacher Step 2 Pos:  ", t_s2["farmer"])
print("Policy Step 2 Pos:   ", p_s2["farmer"])
print("Teacher Step 2 Money:", t_s2["money"])
print("Policy Step 2 Money: ", p_s2["money"])
print("Teacher Step 2 Shed: ", t_s2["shed"])
print("Policy Step 2 Shed:  ", p_s2["shed"])
print("Teacher Step 2 Hands:", len(t_s2["hands"]))
print("Policy Step 2 Hands: ", len(p_s2["hands"]))
print("Positions of Hands (Teacher):", t_s2["hands"])
print("Positions of Hands (Policy): ", p_s2["hands"])

# 4. Model Logits on Teacher Step 2 State
from v32.p2.features import EpisodeFeatures, unit_ctx

fb = EpisodeFeatures()
# Step 0
feat0 = normalizer.transform(np.asarray([fb.update(t_obs_history[0], None)]))[0]
act0 = t_act_history[0]
# Step 1
feat1 = normalizer.transform(np.asarray([fb.update(t_obs_history[1], act0)]))[0]
act1 = t_act_history[1]
# Step 2
s2_ess = t_obs_history[2]
feat2 = normalizer.transform(np.asarray([fb.update(s2_ess, act1)]))[0]

n_u = 1 + len(s2_ess.get("hands", []) or [])
st = torch.tensor(np.asarray([feat2.tolist()]), dtype=torch.float32)
uc = torch.tensor(np.asarray([[unit_ctx(s2_ess, j) for j in range(n_u)]]), dtype=torch.float32)
vv = torch.ones(1, n_u, dtype=torch.bool)

with torch.no_grad():
    out = model(st, uc, vv)
    u_op_logits = out["u_op"][0, 0].numpy()
    probs = torch.softmax(out["u_op"][0, 0], dim=-1).numpy()

print("\n=== P5 ARM 2 FARMER OP LOGITS ON EXACT TEACHER STEP-2 STATE ===")
ranked = np.argsort(-u_op_logits)
for r, idx in enumerate(ranked):
    op_name = C.U_OP[idx]
    logit = u_op_logits[idx]
    prob = probs[idx]
    print(f"Rank {r+1:2d}: {op_name:18s} | Logit: {logit:7.3f} | Prob: {prob*100:6.2f}%")

# Margin and entropy
south_idx = C._U_OP_ID["SOUTH"]
pickup_idx = C._U_OP_ID["PICKUP"]
print("\n=== MARGIN & LOGIT SUMMARY ===")
print(f"SOUTH Logit:  {u_op_logits[south_idx]:.3f} (Prob: {probs[south_idx]*100:.2f}%)")
print(f"PICKUP Logit: {u_op_logits[pickup_idx]:.3f} (Prob: {probs[pickup_idx]*100:.2f}%)")
print(f"Margin (PICKUP - SOUTH): {u_op_logits[pickup_idx] - u_op_logits[south_idx]:.3f}")
entropy = -np.sum(probs * np.log(np.maximum(probs, 1e-12)))
print(f"Farmer Op Entropy: {entropy:.3f}")
