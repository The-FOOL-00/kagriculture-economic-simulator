import json
import os
import sys
import copy
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

SCREEN_SEEDS = [249675, 249676, 249677, 249678, 249679]
OPPONENT = "V27-ABL-V3S"

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

def analyze_arm2():
    ckpt_path = os.path.join(REPO_ROOT, "results", "v32_p5_arm2_early_weighting.npz")
    norm = Normalizer.from_json(json.load(open(os.path.join(REPO_ROOT, "results", "v32_p2_norm.json"))))
    d = np.load(ckpt_path, allow_pickle=True)
    m = P3Policy(157, 12)
    m.load_state_dict({k: torch.tensor(v) for k, v in d.items() if k != "meta"})
    m.eval()

    print("=== EVALUATING ARM 2 FIRST DIVERGENCE (SEEDS 249675-249679) ===")
    
    for seed in SCREEN_SEEDS:
        # Run teacher
        env_t = make("kaggriculture", configuration={"seed": seed})
        teacher = V27AblationAdapter("V27-ABL-A7")
        opp_t = V27AblationAdapter(OPPONENT)
        t_obs, t_acts = [], []
        def t_fn(obs, cfg=None):
            a = teacher.act(obs, cfg)
            t_obs.append(copy.deepcopy(obs))
            t_acts.append(copy.deepcopy(a))
            return a
        env_t.run([t_fn, opp_t.act])
        t_cash = float(env_t.steps[-1][0]["reward"])

        # Run Arm 2 policy
        env_p = make("kaggriculture", configuration={"seed": seed})
        opp_p = V27AblationAdapter(OPPONENT)
        fb = EpisodeFeatures()
        fb.reset()
        state_box = {"prev_act": None}
        p_obs, p_acts, p_feats = [], [], []

        def p_fn(obs, cfg=None):
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
            p_obs.append(copy.deepcopy(obs))
            p_acts.append(copy.deepcopy(act))
            p_feats.append(feat)
            state_box["prev_act"] = act
            return act

        env_p.run([p_fn, opp_p.act])
        p_cash = float(env_p.steps[-1][0]["reward"])

        # Detect first divergence
        first_act = None
        first_state = None
        first_econ = None

        for t in range(min(len(t_acts), len(p_acts))):
            match = actions_equal(p_acts[t], t_acts[t])
            if not match and first_act is None:
                first_act = t

            # Physical state difference
            money_diff = abs(float(p_obs[t]["farms"][0]["money"]) - float(t_obs[t]["farms"][0]["money"]))
            pos_diff = abs(p_obs[t]["farms"][0]["farmer"][0] - t_obs[t]["farms"][0]["farmer"][0]) + \
                       abs(p_obs[t]["farms"][0]["farmer"][1] - t_obs[t]["farms"][0]["farmer"][1])
            hands_diff = abs(len(p_obs[t]["farms"][0].get("hands", []) or []) - len(t_obs[t]["farms"][0].get("hands", []) or []))

            if (pos_diff > 0 or hands_diff > 0 or money_diff > 1.0) and first_state is None:
                first_state = t
            if money_diff > 10.0 and first_econ is None:
                first_econ = t

        print(f"Seed {seed}: Teacher Cash=${t_cash:,.2f} | Arm 2 Cash=${p_cash:,.2f} | "
              f"First Act Div=Step {first_act} | First State Div=Step {first_state} | First Econ Div=Step {first_econ}")

        # Detailed view of steps 0..5
        print(f"  Step 0: T_Farmer={t_acts[0].get('farmer')} P_Farmer={p_acts[0].get('farmer')} | T_Mkt={t_acts[0].get('market')[:2]} P_Mkt={p_acts[0].get('market')[:2]}")
        print(f"  Step 1: T_Farmer={t_acts[1].get('farmer')} P_Farmer={p_acts[1].get('farmer')} | P_Hires={sum(1 for o in p_acts[1].get('market', []) if o[0]=='HIRE')} T_Hires=5")
        print(f"  Step 2: T_Farmer={t_acts[2].get('farmer')} P_Farmer={p_acts[2].get('farmer')} | P_Hands={len(p_obs[2]['farms'][0].get('hands', []))} T_Hands=5")
        print(f"  Step 3: T_Farmer={t_acts[3].get('farmer')} P_Farmer={p_acts[3].get('farmer')}")

if __name__ == "__main__":
    analyze_arm2()
