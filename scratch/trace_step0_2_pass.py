import json
import os
import sys
import numpy as np
import torch

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from kaggle_environments import make
from aec.backbone.v27_ablation_adapters import V27AblationAdapter
from v32.p2.essentials import essentialize
from v32.p2.features import Normalizer, EpisodeFeatures, unit_ctx
from v32.p3 import codec as C
from v32.p3.models import P3Policy

def trace_0_2():
    ckpt_path = os.path.join(REPO_ROOT, "results", "v32_p4_arm1_balanced.npz")
    norm = Normalizer.from_json(json.load(open(os.path.join(REPO_ROOT, "results", "v32_p2_norm.json"))))
    d = np.load(ckpt_path, allow_pickle=True)
    m = P3Policy(157, 12)
    m.load_state_dict({k: torch.tensor(v) for k, v in d.items() if k != "meta"})
    m.eval()

    seed = 249675
    env_t = make("kaggriculture", configuration={"seed": seed})
    teacher = V27AblationAdapter("V27-ABL-A7")
    opp_t = V27AblationAdapter("V27-ABL-V3S")
    t_acts = []
    def t_fn(obs, cfg=None):
        a = teacher.act(obs, cfg)
        t_acts.append(a)
        return a
    env_t.run([t_fn, opp_t.act])

    env_p = make("kaggriculture", configuration={"seed": seed})
    opp_p = V27AblationAdapter("V27-ABL-V3S")
    fb = EpisodeFeatures()
    fb.reset()
    state_box = {"prev_act": None}
    logs = []

    def p_agent_fn(obs, cfg=None):
        step = obs["step"]
        ess = essentialize(obs, 0)
        rf = fb.update(ess, state_box["prev_act"])
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
        
        if step == 0:
            act["farmer"] = ["PASS"]
        elif step == 2:
            act["farmer"] = ["SOUTH"]
            
        t_a = t_acts[step]
        f_match = (act.get("farmer") or ["PASS"]) == (t_a.get("farmer") or ["PASS"])
        t_h = len(t_a.get("hands", []) or [])
        p_h = len(obs["farms"][0].get("hands", []) or [])
        cash = float(obs["farms"][0]["money"])
        logs.append((step, str(t_a.get('farmer')), str(act.get('farmer')), f_match, t_h, p_h, cash, act.get('market', [])[:2]))
        state_box["prev_act"] = act
        return act

    env_p.run([p_agent_fn, opp_p.act])
    print(f"{'Step':<5} | {'Teacher Farmer':<15} | {'Policy Farmer':<15} | {'Match?':<6} | {'T Hands':<8} | {'P Hands':<8} | {'P Cash'} | Market Orders")
    print("-" * 105)
    for l in logs[:15]:
        print(f"{l[0]:<5} | {l[1]:<15} | {l[2]:<15} | {str(l[3]):<6} | {l[4]:<8} | {l[5]:<8} | ${l[6]:.1f} | {l[7]}")
    terminal_cash = float(env_p.steps[-1][0]["reward"])
    print(f"\nTerminal cash with step-0 and step-2 farmer patch: ${terminal_cash:,.2f}")

if __name__ == "__main__":
    trace_0_2()
