# SPDX-License-Identifier: MIT
"""V32 P6 Trace Steps 0 to 24: Side-by-side Teacher vs P6 Arm 2 (with mask)."""

import os, sys, json, torch
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from v32.p2.essentials import essentialize
from v32.p2.features import Normalizer
from v32.p3.models import P3Policy
from scripts.v32_p6_eval_screen import MaskedPredictor
from v32_common import load_agent
from kaggle_environments import make

norm = json.load(open(os.path.join(REPO_ROOT, "results", "v32_p2_norm.json")))
normalizer = Normalizer.from_json(norm)
model = P3Policy(157, 12)
d = np.load(os.path.join(REPO_ROOT, "results", "v32_p6_arm2_rebalanced.npz"), allow_pickle=True)
model.load_state_dict({k: torch.tensor(v) for k, v in d.items() if k != "meta"})
model.eval()

seed = 249675

def get_trace(use_teacher=False, mask=True):
    env = make("kaggriculture", configuration={"seed": seed})
    opp = load_agent("E0_V3")
    teacher = load_agent("E0_V3") if use_teacher else None
    pred = MaskedPredictor(model, normalizer, apply_mask=mask)

    records = []

    def act(obs, cfg=None):
        ess = essentialize(obs, 0)
        st_num = ess["step"]

        if use_teacher:
            a = teacher.act(obs, cfg)
        else:
            res = pred.step(ess)
            a = res["action"]

        records.append({
            "step": st_num,
            "farmer_pos": ess["farmer"],
            "money": ess["money"],
            "farmer_act": a.get("farmer", []),
            "hands_count": len(ess.get("hands", []) or []),
            "shed": ess["shed"],
            "inv": ess["inv"][0] if ess["inv"] else {},
            "market_act": a.get("market", []),
        })
        return a

    env.run([act, opp.act])
    return {
        "final_cash": float(env.steps[-1][0]["reward"]),
        "records": records[:25],
    }

teacher_trace = get_trace(use_teacher=True)
policy_trace = get_trace(use_teacher=False, mask=True)

out_data = {
    "seed": seed,
    "teacher_final_cash": teacher_trace["final_cash"],
    "policy_final_cash": policy_trace["final_cash"],
    "teacher_records": teacher_trace["records"],
    "policy_records": policy_trace["records"],
}

with open(os.path.join(REPO_ROOT, "results", "v32_p6_steps_0_24_trace.json"), "w") as f:
    json.dump(out_data, f, indent=2)

print(f"Teacher Final Cash: ${teacher_trace['final_cash']:.2f}")
print(f"Policy Final Cash: ${policy_trace['final_cash']:.2f}")
print(f"Teacher records count: {len(teacher_trace['records'])}, Policy records count: {len(policy_trace['records'])}")
print("\n--- STEP BY STEP COMPARISON (Steps 0-24) ---")
print(f"{'Step':<4} | {'Teacher Farmer':<22} | {'Policy Farmer':<22} | {'T Pos':<8} | {'P Pos':<8} | {'T Cash':<8} | {'P Cash':<8} | {'Match'}")
max_st = max(len(teacher_trace["records"]), len(policy_trace["records"]))
for st in range(max_st):
    t_r = teacher_trace["records"][st] if st < len(teacher_trace["records"]) else {}
    p_r = policy_trace["records"][st] if st < len(policy_trace["records"]) else {}
    t_act = str(t_r.get("farmer_act", "N/A"))
    p_act = str(p_r.get("farmer_act", "N/A"))
    t_pos = str(t_r.get("farmer_pos", "N/A"))
    p_pos = str(p_r.get("farmer_pos", "N/A"))
    t_cash = f"{t_r.get('money', 0.0):.1f}" if "money" in t_r else "N/A"
    p_cash = f"{p_r.get('money', 0.0):.1f}" if "money" in p_r else "N/A"
    match = "==" if t_act == p_act and t_pos == p_pos else "!="
    print(f"{st:<4} | {t_act:<22} | {p_act:<22} | {t_pos:<8} | {p_pos:<8} | {t_cash:<8} | {p_cash:<8} | {match}")
