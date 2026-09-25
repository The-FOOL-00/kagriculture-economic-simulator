# SPDX-License-Identifier: MIT
"""V32 P6 Step-2 Causal Counterfactual Analysis.

Simulator-grounded comparison:
- Counterfactual A: Step 2 forces SOUTH (expert), then continues under policy.
- Counterfactual B: Step 2 forces PICKUP(COW) (model error), then continues under policy.
Runs through actual Kaggle environment across representative development seeds.
"""

import json
import os
import sys
import numpy as np
import torch

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from kaggle_environments import make
from v32.p2.essentials import essentialize
from v32.p2.features import Normalizer, EpisodeFeatures, unit_ctx
from v32.p3 import codec as C
from v32.p3.models import P3Policy
from v32.p6.mask import compute_unit_op_mask, apply_mask_to_logits
from v32_common import load_agent

norm = Normalizer.from_json(json.load(open(os.path.join(REPO_ROOT, "results", "v32_p2_norm.json"))))


def run_counterfactual(seed, force_step2_op, ckpt_path):
    env = make("kaggriculture", configuration={"seed": seed})
    opp = load_agent("E0_V3")

    model = P3Policy(157, 12)
    d = np.load(ckpt_path, allow_pickle=True)
    model.load_state_dict({k: torch.tensor(v) for k, v in d.items() if k != "meta"})
    model.eval()

    fb = EpisodeFeatures()
    prev_act = None
    step_records = []

    def act(obs, cfg=None):
        nonlocal prev_act
        ess = essentialize(obs, 0)
        st_num = ess["step"]

        feat = norm.transform(np.asarray([fb.update(ess, prev_act)]))[0]
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

        if st_num == 2 and force_step2_op:
            u_ops[0] = C._U_OP_ID[force_step2_op]
            if force_step2_op == "PICKUP":
                u_args[0] = C._U_ARG_ID["COW"]
                u_qtys[0] = C._U_QTY_ID[1]

        u = [(o, a, q) for o, a, q in zip(u_ops, u_args, u_qtys)]
        m = [(o, i, q) for o, i, q in zip(m_ops, m_items, m_qtys)]
        a = C.decode_action(u, m)
        prev_act = a

        step_records.append({
            "step": st_num,
            "farmer_pos": ess["farmer"],
            "money": ess["money"],
            "farmer_act": a.get("farmer", []),
            "shed": ess["shed"],
            "inv": ess["inv"][0] if ess["inv"] else {},
        })
        return a

    env.run([act, opp.act])
    return {
        "final_cash": float(env.steps[-1][0]["reward"]),
        "records": step_records,
    }


def main():
    seeds = [249675, 249676, 249677]
    ckpt = os.path.join(REPO_ROOT, "results", "v32_p5_arm2_early_weighting.npz")

    print("=== V32 P6 STEP-2 COUNTERFACTUAL ANALYSIS ===")
    for s in seeds:
        res_a = run_counterfactual(s, "SOUTH", ckpt)
        res_b = run_counterfactual(s, "PICKUP", ckpt)

        print(f"\nSeed {s}:")
        print(f"  Counterfactual A (Step 2 SOUTH):  Terminal Cash = ${res_a['final_cash']:.2f}")
        print(f"  Counterfactual B (Step 2 PICKUP): Terminal Cash = ${res_b['final_cash']:.2f}")

        # Compare Step 3 farmer position
        r_a3 = res_a["records"][3] if len(res_a["records"]) > 3 else {}
        r_b3 = res_b["records"][3] if len(res_b["records"]) > 3 else {}
        print(f"  Step 3 Pos: CF-A={r_a3.get('farmer_pos')} vs CF-B={r_b3.get('farmer_pos')}")


if __name__ == "__main__":
    main()
