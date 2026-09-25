# SPDX-License-Identifier: MIT
import os, sys, json, torch
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from v32.p2.essentials import essentialize
from v32.p2.features import Normalizer, EpisodeFeatures, unit_ctx
from v32.p3 import codec as C
from v32.p3.models import P3Policy
from v32.p6.mask import compute_unit_op_mask, apply_mask_to_logits
from v32_common import load_agent
from kaggle_environments import make

norm = json.load(open(os.path.join(REPO_ROOT, "results", "v32_p2_norm.json")))
normalizer = Normalizer.from_json(norm)
model = P3Policy(157, 12)
d = np.load(os.path.join(REPO_ROOT, "results", "v32_p6_arm2_rebalanced.npz"), allow_pickle=True)
model.load_state_dict({k: torch.tensor(v) for k, v in d.items() if k != "meta"})
model.eval()

seed = 249675
env = make("kaggriculture", configuration={"seed": seed})
opp = load_agent("E0_V3")
fb = EpisodeFeatures()
prev_act = None

actions_emitted = []
farmer_pos_history = []
shed_history = []
inv_history = []
hand_actions_history = []
money_history = []

def act(obs, cfg=None):
    global prev_act
    ess = essentialize(obs, 0)
    feat = normalizer.transform(np.asarray([fb.update(ess, prev_act)]))[0]
    n_u = 1 + len(ess.get("hands", []) or [])
    st = torch.tensor(np.asarray([feat.tolist()]), dtype=torch.float32)
    uc = torch.tensor(np.asarray([[unit_ctx(ess, j) for j in range(n_u)]]), dtype=torch.float32)
    vv = torch.ones(1, n_u, dtype=torch.bool)
    with torch.no_grad():
        out = model(st, uc, vv)
        u_ops = out["u_op"].argmax(-1)[0].tolist()
        u_args = out["u_arg"].argmax(-1)[0].tolist()
        u_qtys = out["u_qty"].argmax(-1)[0].tolist()
        m_ops = out["m_op"].argmax(-1)[0].tolist()
        m_items = out["m_item"].argmax(-1)[0].tolist()
        m_qtys = out["m_qty"].argmax(-1)[0].tolist()
    u = [(o, a, q) for o, a, q in zip(u_ops, u_args, u_qtys)]
    m = [(o, i, q) for o, i, q in zip(m_ops, m_items, m_qtys)]
    a = C.decode_action(u, m)
    prev_act = a
    actions_emitted.append(a)
    farmer_pos_history.append(ess["farmer"])
    shed_history.append(ess["shed"])
    inv_history.append(ess["inv"][0] if ess["inv"] else {})
    hand_actions_history.append(a.get("hands", []))
    money_history.append(ess["money"])
    return a

env.run([act, opp.act])

print("=== P6 ARM 2 (UNMASKED) FREE-RUNNING TRAJECTORY (Steps 0-15) ===")
for st in range(min(16, len(actions_emitted))):
    f_act = actions_emitted[st].get("farmer", [])
    m_act = actions_emitted[st].get("market", [])
    h_act = hand_actions_history[st]
    print(f"Step {st:2d} | Pos={farmer_pos_history[st]} | Money={money_history[st]:.1f} | Farmer={f_act} | Hands={h_act[:2]} | Mkt={m_act[:2]} | Inv={inv_history[st]}")

print(f"\nTerminal Cash: ${env.steps[-1][0]['reward']:.2f}")
print(f"Total Steps: {len(actions_emitted)}")
