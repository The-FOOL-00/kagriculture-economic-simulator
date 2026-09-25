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
from v32.p2.dataset import load_legs
from v32.p3.dataset import build_samples
from v32.p3 import codec as C
from v32.p3.models import P3Policy

def main():
    norm = Normalizer.from_json(json.load(open(os.path.join(REPO_ROOT, "results", "v32_p2_norm.json"))))
    train_feats = []
    for leg in list(load_legs(os.path.join(REPO_ROOT, "results", "v32_p2_bc_legs.jsonl")))[:20]:
        for s in build_samples(leg, leg["rows0"], leg["left"]):
            train_feats.append(s["feat"])
            if len(train_feats) >= 3000:
                break
        if len(train_feats) >= 3000:
            break
    F_train = norm.transform(train_feats)

    d = np.load(os.path.join(REPO_ROOT, "results", "v32_p4_arm1_balanced.npz"), allow_pickle=True)
    m = P3Policy(157, 12)
    m.load_state_dict({k: torch.tensor(v) for k, v in d.items() if k != "meta"})
    m.eval()

    seed = 249675
    # Run teacher
    env_t = make("kaggriculture", configuration={"seed": seed})
    teacher = V27AblationAdapter("V27-ABL-A7")
    opp_t = V27AblationAdapter("V27-ABL-V3S")
    t_obs_list, t_act_list = [], []
    def t_fn(obs, cfg=None):
        a = teacher.act(obs, cfg)
        t_obs_list.append(obs)
        t_act_list.append(a)
        return a
    env_t.run([t_fn, opp_t.act])

    # Run policy
    env_p = make("kaggriculture", configuration={"seed": seed})
    opp_p = V27AblationAdapter("V27-ABL-V3S")
    p_obs_list, p_act_list = [], []
    fb_p = EpisodeFeatures()
    fb_p.reset()
    prev_act = None
    def p_fn(obs, cfg=None):
        nonlocal prev_act
        ess = essentialize(obs, 0)
        rf = fb_p.update(ess, prev_act)
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
        p_obs_list.append(obs)
        p_act_list.append(act)
        prev_act = act
        return act
    env_p.run([p_fn, opp_p.act])

    # Now compute features for both
    fb_t = EpisodeFeatures()
    fb_t.reset()
    prev_t = None
    t_feats, p_feats = [], []
    for o, a in zip(t_obs_list, t_act_list):
        rf = fb_t.update(essentialize(o, 0), prev_t)
        t_feats.append(norm.transform(np.asarray([rf]))[0])
        prev_t = a

    fb_p2 = EpisodeFeatures()
    fb_p2.reset()
    prev_p2 = None
    for o, a in zip(p_obs_list, p_act_list):
        rf = fb_p2.update(essentialize(o, 0), prev_p2)
        p_feats.append(norm.transform(np.asarray([rf]))[0])
        prev_p2 = a

    print(f"{'Step':<5} | {'||s_P - s_T||':<15} | {'Min Dist(T, Train)':<20} | {'Min Dist(P, Train)':<20}")
    print("-" * 70)
    for step in [0, 1, 2, 5, 10, 24, 72, 144, 288, 480, 718]:
        st_dist = np.linalg.norm(p_feats[step] - t_feats[step])
        t_dists = np.min(np.linalg.norm(F_train - t_feats[step], axis=1))
        p_dists = np.min(np.linalg.norm(F_train - p_feats[step], axis=1))
        print(f"{step:<5} | {st_dist:<15.3f} | {t_dists:<20.3f} | {p_dists:<20.3f}")

if __name__ == "__main__":
    main()
