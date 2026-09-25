# SPDX-License-Identifier: MIT
"""V32 P7 prefix training (Arms 1-4): uniform trajectory-prefix supervision.

Loss (Arm 1 default, H=4):
  L = L_unit + L_mkt + 50*L_crit_s0 + 10*L_early_1_10 + 50*L_s2_farmer
      + lambda_H * L_prefix(H)
where L_prefix(H) is the UNIFORM-mean window loss from v32.p7.loss (no
per-step spikes; dedicated single-step weights for later steps are
deliberately absent).

The P6 base terms are RETAINED (additive design, documented in
V32_P7_PREFIX4.md): the H1 test is the MARGINAL effect of the uniform prefix
term on stability past step 3, without a forgetting confound. --drop_base
ablates this choice as a diagnostic.

Selection: teacher-forced train-prefix probes (farmer prefix-exact, step-3/4
pickup rates, P6 opening gates) + Mode-B truncated rollout consistency on two
fixed TRAIN seeds (249635/249636 seat 0 vs E0_V3; never dev seeds, never
holdouts) as tiebreak. All states simulator-generated; no teacher-state
overwrite, no splicing.
"""

import argparse
import json
import os
import subprocess
import sys
import time

import numpy as np
import torch
import torch.nn as nn

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from v32.p2.dataset import BC_VAL_SEEDS, load_legs  # noqa: E402
from v32.p2.features import Normalizer  # noqa: E402
from v32.p3 import codec as C  # noqa: E402
from v32.p3.dataset import build_samples  # noqa: E402
from v32.p3.metrics import batchify, head_metrics, _op_mask  # noqa: E402
from v32.p3.models import P3Policy, M_ITEM_OPS, U_ARG_OPS, U_QTY_OPS  # noqa: E402
from v32.p7.loss import prefix_loss  # noqa: E402
from v32_p6_train import eval_early_probe  # noqa: E402

MODEB_SEEDS = (249635, 249636)


def git_commit():
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT,
                              capture_output=True, text=True).stdout.strip()
    except Exception:
        return "unknown"


@torch.no_grad()
def eval_prefix_probe(model, pref_groups, F_pref):
    """Teacher-forced prefix probe on train seats.

    pref_groups: list of seats, each a list of (H+1) samples steps 0..H.
    Returns farmer prefix-exact rate + per-step farmer-op accuracy.
    """
    model.eval()
    n_exact = 0
    step_ok = {}
    step_n = {}
    pu_op_id = C._U_OP_ID
    for g, F in zip(pref_groups, F_pref):
        b = batchify(list(range(len(g))), g, F)
        out = model(b["state"], b["uctx"], b["valid"])
        pu = out["u_op"].argmax(-1)
        exact = True
        for r, s in enumerate(g):
            ok = pu[r, 0].item() == s["u_op"][0]
            # arg must also match when the target op carries one
            if ok and s["u_op"][0] in U_ARG_OPS:
                ok = out["u_arg"].argmax(-1)[r, 0].item() == s["u_arg"][0]
            step_ok[s["step"]] = step_ok.get(s["step"], 0) + int(ok)
            step_n[s["step"]] = step_n.get(s["step"], 0) + 1
            exact = exact and ok
        n_exact += int(exact)
    rate = {t: step_ok[t] / step_n[t] for t in sorted(step_n)}
    return {"n_groups": len(pref_groups), "prefix_exact": n_exact,
            "step_farmer_acc": rate}


@torch.no_grad()
def eval_modeb_probe(model, norm):
    """Free-running prefix consistency on fixed TRAIN seeds (Mode B metric).

    Policy (masked) vs live E2_A7 replay, 9-step truncated rollouts. Returns
    median first farmer-action divergence + mean state distance over 0..8.
    """
    from kaggle_environments import make
    from v32_common import load_agent
    from v32.p2.essentials import essentialize
    import v32_p6_eval_screen as P6E
    from v32.p7.metrics import first_divergence
    from v32.p7.rollout import truncated_rollout
    from v32.p7.state import state_distance
    make_fn = lambda s: make("kaggriculture", configuration={"seed": s})  # noqa: E731
    pred = P6E.MaskedPredictor(model, norm, apply_mask=True)

    class PA:
        def __init__(self, seat):
            self.seat = seat

        def act(self, obs, cfg=None):
            return pred.step(essentialize(obs, self.seat),
                             deterministic=True)["action"]

    t_acts, sds = [], []
    for seed in MODEB_SEEDS:
        pred.reset()
        ptr, _ = truncated_rollout(make_fn, seed, [PA(0), load_agent("E0_V3")],
                                   8, trace_seat=0, ess_fn=essentialize)
        ttr, _ = truncated_rollout(make_fn, seed,
                                   [load_agent("E2_A7"), load_agent("E0_V3")],
                                   8, trace_seat=0, ess_fn=essentialize)
        pt = [{"step": r["step"], "ess": r["ess"], "action": r["actions"][0]}
              for r in ptr]
        tt = [{"step": r["step"], "ess": r["ess"], "action": r["actions"][0]}
              for r in ttr]
        div = first_divergence(tt, pt)
        t_acts.append(div["t_act_farmer"]
                      if div["t_act_farmer"] is not None else 999)
        sds.append(float(np.mean(
            [state_distance(tt[t]["ess"], pt[t]["ess"])["total"]
             for t in range(min(9, len(pt), len(tt)))])))
    return {"t_act_median": float(np.median(t_acts)),
            "state_dist_mean": float(np.mean(sds))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--batch_size", type=int, default=128)
    ap.add_argument("--horizon", type=int, default=4)
    ap.add_argument("--prefix_weight", type=float, default=10.0)
    ap.add_argument("--crit_weight", type=float, default=50.0)
    ap.add_argument("--early_weight", type=float, default=10.0)
    ap.add_argument("--s2_weight", type=float, default=50.0)
    ap.add_argument("--drop_base", type=int, default=0)
    ap.add_argument("--early_steps", type=int, default=10)
    ap.add_argument("--init_ckpt", default=os.path.join(
        REPO_ROOT, "results", "v32_p6_arm2_rebalanced.npz"))
    ap.add_argument("--out", default=os.path.join(
        REPO_ROOT, "results", "v32_p7_prefix4.npz"))
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--modeb_every", type=int, default=2)
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    H = args.horizon

    legs_path = os.path.join(REPO_ROOT, "results", "v32_p2_bc_legs.jsonl")
    norm = Normalizer.from_json(json.load(
        open(os.path.join(REPO_ROOT, "results", "v32_p2_norm.json"))))

    tr_samples, va_samples, all_step0, all_early = [], [], [], []
    pref_groups, F_pref = [], []
    for leg in load_legs(legs_path):
        is_val = leg["seed"] in BC_VAL_SEEDS
        for side, expert in (("rows0", leg["left"]), ("rows1", leg["right"])):
            samples = list(build_samples(leg, leg[side], expert))
            (va_samples if is_val else tr_samples).extend(samples)
            if not is_val:
                grp = [s for s in samples if s["step"] <= H]
                assert len(grp) == H + 1, (leg["seed"], side, len(grp))
                pref_groups.append(grp)
                F_pref.append(norm.transform(np.asarray([s["feat"] for s in grp])))
            for s in samples:
                if s["step"] == 0:
                    all_step0.append(s)
                if 1 <= s["step"] <= args.early_steps:
                    all_early.append(s)

    print(f"train={len(tr_samples)} val={len(va_samples)} "
          f"prefix_groups={len(pref_groups)} (H={H})", flush=True)
    F_tr = norm.transform(np.asarray([s["feat"] for s in tr_samples]))
    F_va = norm.transform(np.asarray([s["feat"] for s in va_samples]))
    F_s0 = norm.transform(np.asarray([s["feat"] for s in all_step0]))
    F_early = norm.transform(np.asarray([s["feat"] for s in all_early]))

    model = P3Policy(157, 12)
    print(f"warm-start: {args.init_ckpt}", flush=True)
    d = np.load(args.init_ckpt, allow_pickle=True)
    model.load_state_dict({k: torch.tensor(v) for k, v in d.items()
                           if k != "meta"})
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    ce = nn.CrossEntropyLoss(reduction="none")

    best_score, best_w, curve = -1.0, None, []
    lam = args.prefix_weight
    print(f"P7 prefix-H{H}: epochs={args.epochs} lr={args.lr} lam={lam} "
          f"drop_base={args.drop_base}", flush=True)
    for ep in range(1, args.epochs + 1):
        model.train()
        perm = np.random.permutation(len(tr_samples))
        t0 = time.time()
        acc = {"unit": 0.0, "mkt": 0.0, "crit": 0.0, "early": 0.0,
               "s2": 0.0, "pref": 0.0}
        nb = 0
        steps_of = [s["step"] for s in tr_samples]
        for start in range(0, len(tr_samples), args.batch_size):
            bidx = perm[start:start + args.batch_size].tolist()
            b = batchify(bidx, tr_samples, F_tr)
            out = model(b["state"], b["uctx"], b["valid"])
            loss_m_op = ce(out["m_op"].reshape(-1, len(C.M_OP)),
                           b["m_op"].reshape(-1)).mean()
            mm = _op_mask(b["m_op"], M_ITEM_OPS)
            z = out["m_op"].sum() * 0.0
            loss_m_item = ce(out["m_item"][mm], b["m_item"][mm]).mean() \
                if mm.any() else z
            loss_m_qty = ce(out["m_qty"][mm], b["m_qty"][mm]).mean() \
                if mm.any() else z
            L_mkt = loss_m_op + loss_m_item + loss_m_qty
            vv = b["valid"]
            loss_u_op = ce(out["u_op"][vv], b["u_op"][vv]).mean()
            ma = _op_mask(b["u_op"], U_ARG_OPS) & vv
            loss_u_arg = ce(out["u_arg"][ma], b["u_arg"][ma]).mean() \
                if ma.any() else z
            mq = _op_mask(b["u_op"], U_QTY_OPS) & vv
            loss_u_qty = ce(out["u_qty"][mq], b["u_qty"][mq]).mean() \
                if mq.any() else z
            L_unit = loss_u_op + loss_u_arg + loss_u_qty

            dev = out["m_op"].device
            L_crit = torch.tensor(0.0, device=dev)
            is_s0 = torch.tensor([tr_samples[i]["step"] == 0 for i in bidx],
                                 dtype=torch.bool)
            if is_s0.any() and args.crit_weight > 0 and not args.drop_base:
                s0_u = ce(out["u_op"][is_s0, 0], b["u_op"][is_s0, 0]).mean()
                s0_m = ce(out["m_op"][is_s0].reshape(-1, len(C.M_OP)),
                          b["m_op"][is_s0].reshape(-1)).mean()
                s0_mm = _op_mask(b["m_op"][is_s0], M_ITEM_OPS)
                s0_i = ce(out["m_item"][is_s0][s0_mm],
                          b["m_item"][is_s0][s0_mm]).mean() if s0_mm.any() else 0.0
                s0_q = ce(out["m_qty"][is_s0][s0_mm],
                          b["m_qty"][is_s0][s0_mm]).mean() if s0_mm.any() else 0.0
                L_crit = s0_u + s0_m + s0_i + s0_q
            L_early = torch.tensor(0.0, device=dev)
            is_e = torch.tensor([1 <= tr_samples[i]["step"] <= args.early_steps
                                 for i in bidx], dtype=torch.bool)
            if is_e.any() and args.early_weight > 0 and not args.drop_base:
                e_vv = vv[is_e]
                e_u = ce(out["u_op"][is_e][e_vv],
                         b["u_op"][is_e][e_vv]).mean()
                e_m = ce(out["m_op"][is_e].reshape(-1, len(C.M_OP)),
                         b["m_op"][is_e].reshape(-1)).mean()
                e_mm = _op_mask(b["m_op"][is_e], M_ITEM_OPS)
                e_i = ce(out["m_item"][is_e][e_mm],
                         b["m_item"][is_e][e_mm]).mean() if e_mm.any() else 0.0
                e_q = ce(out["m_qty"][is_e][e_mm],
                         b["m_qty"][is_e][e_mm]).mean() if e_mm.any() else 0.0
                L_early = e_u + e_m + e_i + e_q
            L_s2 = torch.tensor(0.0, device=dev)
            is_s2 = torch.tensor([tr_samples[i]["step"] == 2 for i in bidx],
                                 dtype=torch.bool)
            if is_s2.any() and args.s2_weight > 0 and not args.drop_base:
                L_s2 = ce(out["u_op"][is_s2, 0], b["u_op"][is_s2, 0]).mean()
            L_pref = prefix_loss(out, b, [steps_of[i] for i in bidx], H, ce)
            loss = (L_unit + L_mkt + args.crit_weight * L_crit
                    + args.early_weight * L_early + args.s2_weight * L_s2
                    + lam * L_pref)
            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            for k, v in (("unit", L_unit), ("mkt", L_mkt), ("crit", L_crit),
                         ("early", L_early), ("s2", L_s2), ("pref", L_pref)):
                acc[k] += float(v.item())
            nb += 1

        mv = head_metrics(model, list(range(len(va_samples))), va_samples, F_va)
        probe = eval_early_probe(model, all_step0, F_s0, all_early, F_early)
        pp = eval_prefix_probe(model, pref_groups, F_pref)
        mb = eval_modeb_probe(model, norm) if ep % args.modeb_every == 0 \
            else {"t_act_median": -1.0, "state_dist_mean": -1.0}
        s3 = pp["step_farmer_acc"].get(3, 0.0)
        s4 = pp["step_farmer_acc"].get(4, 0.0)
        print(f"ep={ep:2d} ({time.time()-t0:.0f}s) val_full={mv['full_exact']:.3f} "
              f"S0wash={probe['s0_wash']}/{probe['n_s0']} "
              f"S1N={probe['s1_north']}/{probe['n_s1']} "
              f"S2S={probe['s2_south']}/{probe['n_s2']} "
              f"pem{H}f={pp['prefix_exact']}/{pp['n_groups']} "
              f"S3={s3:.2f} S4={s4:.2f} "
              f"modeB_t={mb['t_act_median']:.0f} "
              f"modeB_d={mb['state_dist_mean']:.3f} "
              f"Lpref={acc['pref']/nb:.3f}", flush=True)
        # Selection: opening gates hard-constrained, then prefix fidelity,
        # then Mode-B consistency (train seeds only).
        gates_ok = (probe["s0_pass"] == probe["n_s0"]
                    and probe["s1_north"] == probe["n_s1"]
                    and probe["s1_hire"] == probe["n_s1"]
                    and probe["s2_south"] == probe["n_s2"])
        score = (10000.0 if gates_ok else 0.0) + pp["prefix_exact"] * 20.0 \
            + (s3 + s4) * 100.0 + mv["full_exact"] \
            + (mb["t_act_median"] * 5.0 if mb["t_act_median"] > 0 else 0.0)
        curve.append({"ep": ep, "score": score, "probe": probe,
                      "prefix": pp["prefix_exact"], "modeb": mb,
                      "val_full": mv["full_exact"]})
        if score > best_score:
            best_score = score
            best_w = {k: v.cpu().numpy()
                      for k, v in model.state_dict().items()}
            best_w["meta"] = {"epoch": ep, "commit": git_commit(),
                              "score": float(best_score), "horizon": H,
                              "prefix_weight": lam,
                              "drop_base": args.drop_base,
                              "val_full_exact": float(mv["full_exact"]),
                              "probe": probe, "prefix_probe": pp,
                              "modeb": mb}
            np.savez_compressed(args.out, **best_w)
    print(f"done best={best_score:.1f} -> {args.out}", flush=True)
    with open(args.out + ".curve.json", "w") as f:
        json.dump(curve, f)


if __name__ == "__main__":
    main()
