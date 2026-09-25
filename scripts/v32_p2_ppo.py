# SPDX-License-Identifier: MIT
"""V32 P2 PPO driver: BC-init -> ~1M slope run (preregistered config only).

Multiprocess rollout (env + torch in .venv), round-robin opponent/seat
schedule (deterministic), GAE + clipped updates, checkpoint registry.
Usage: v32_p2_ppo.py --out DIR [--total-steps N] [--smoke]
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

import numpy as np  # noqa: E402
import torch  # noqa: E402

from v32.p2.ppo import compute_gae, ppo_update  # noqa: E402

TRAIN_OPPS = ["E0_V3", "E2_A7", "E3_V25P3", "E6_W72", "E7_W2015", "E8_DMITRII"]

_W = {}


def _worker_init(vocab, norm_json):
    import sys as _s
    _s.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    _s.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import torch as _t
    _t.set_num_threads(1)
    _t.set_num_interop_threads(1)
    from v32.p2.features import Normalizer as _N
    from v32.p2.models import P2Policy as _P
    from v32.p2.rollout import Predictor as _Pr
    _W["vocab"] = vocab
    _W["norm"] = _N.from_json(norm_json)
    _W["uvoc"] = [tuple(c) for c in vocab["unit_vocab"]]
    _W["mvoc"] = [tuple(c) for c in vocab["market_vocab"]]
    _W["model"] = _P(157, 12, _W["uvoc"], _W["mvoc"], vocab["ops"], vocab["items"])
    _W["pred"] = _Pr(_W["model"], _W["norm"], _W["uvoc"], _W["mvoc"])


def _run_eps(args):
    state, eps, base_seed = args
    import torch as _t
    from v32.p2.rollout import run_episode
    from v32_common import check_seed_allowed, load_agent
    from kaggle_environments import make
    _W["model"].load_state_dict(
        {k: _t.tensor(np.asarray(v)) for k, v in state.items()})
    _W["model"].eval()
    out = []
    cache = _W.setdefault("opp_cache", {})
    for (k, opp, seed, seat) in eps:
        check_seed_allowed(seed)
        _t.manual_seed((base_seed + k) % (2 ** 31))
        if opp == "E8_DMITRII":
            ag = load_agent(opp)  # reactive, unproven reset: fresh each ep
        else:
            # V3-chassis: reset-safe (_state resets on step<=last_step).
            ag = cache.get(opp)
            if ag is None:
                ag = cache[opp] = load_agent(opp)
        steps, mine, theirs = run_episode(
            lambda s: make("kaggriculture", configuration={"seed": s}),
            seed, seat, _W["pred"], ag)
        out.append({"k": k, "opp": opp, "seed": seed, "seat": seat,
                    "mine": mine, "theirs": theirs, "steps": steps})
    return out


def git_commit():
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT,
                              capture_output=True, text=True).stdout.strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--total-steps", type=int, default=1000000)
    ap.add_argument("--episodes-per-iter", type=int, default=24)
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--train-seeds", default="249635:249649")
    ap.add_argument("--bc-init", default="results/v32_p2_bc.npz")
    ap.add_argument("--ckpt-at", default="0,100000,250000,500000,750000,1000000")
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--clip", type=float, default=0.2)
    ap.add_argument("--gamma", type=float, default=1.0)
    ap.add_argument("--lam", type=float, default=0.95)
    ap.add_argument("--vf-coef", type=float, default=0.5)
    ap.add_argument("--ent-coef", type=float, default=0.01)
    ap.add_argument("--epochs", type=int, default=4)
    ap.add_argument("--minibatch", type=int, default=2048)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    from v32_common import assert_frozen
    from v32.p2.features import Normalizer
    from v32.p2.models import P2Policy, param_count
    assert_frozen()
    os.makedirs(args.out, exist_ok=True)
    lo, hi = [int(x) for x in args.train_seeds.split(":")]
    seeds = list(range(lo, hi + 1))
    for s in seeds:
        from v32_common import check_seed_allowed
        check_seed_allowed(s)

    vocab = json.load(open(os.path.join(REPO_ROOT, "results", "v32_p2_vocab.json")))
    norm = Normalizer.from_json(json.load(open(
        os.path.join(REPO_ROOT, "results", "v32_p2_norm.json"))))
    uvoc = [tuple(c) for c in vocab["unit_vocab"]]
    mvoc = [tuple(c) for c in vocab["market_vocab"]]
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    model = P2Policy(157, 12, uvoc, mvoc, vocab["ops"], vocab["items"])
    bc = np.load(os.path.join(REPO_ROOT, args.bc_init), allow_pickle=True)
    bmeta = json.loads(str(bc["meta"]))
    state = {k: torch.tensor(v) for k, v in bc.items() if k != "meta"}
    missing = set(model.state_dict()) - set(state)
    # critic head trains from scratch (BC has no value head... it does share
    # the trunk; critic layers are randomly initialized in P2Policy; BC ckpt
    # includes critic weights fitted to nothing — EXCLUDE critic from init).
    state = {k: v for k, v in state.items() if not k.startswith("critic.")}
    model.load_state_dict(state, strict=False)
    print("BC init: loaded %d tensors (critic fresh); params=%d" % (
        len(state), param_count(model)), flush=True)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)

    ckpt_at = sorted(int(x) for x in args.ckpt_at.split(","))
    EPI = 2 if args.smoke else args.episodes_per_iter
    total = 2000 if args.smoke else args.total_steps
    log = open(os.path.join(args.out, "run.jsonl"), "a", buffering=1)
    ckpts = []
    steps_done = 0
    it = 0

    def save_ckpt(tag):
        import numpy as _np
        sd = {k: v.detach().numpy() for k, v in model.state_dict().items()}
        meta = {"tag": tag, "steps": steps_done, "iter": it,
                "git": git_commit(), "seed": args.seed}
        p = os.path.join(args.out, "ckpt_%s.npz" % tag)
        _np.savez(p, **sd, meta=json.dumps(meta, sort_keys=True))
        ckpts.append({"tag": tag, "steps": steps_done,
                      "sha256": hashlib.sha256(open(p, "rb").read()).hexdigest()})
        print("saved %s steps=%d" % (p, steps_done), flush=True)

    if 0 in ckpt_at:
        save_ckpt("0")
        ckpt_at = [c for c in ckpt_at if c != 0]
    t0 = time.time()
    # NOTE: no max_tasks cap (respawn wedged pools in eval; workers hold
    # no cross-episode env state: fresh env per episode, predictor.reset(),
    # per-episode torch seeding; V3-family opponent cache is reset-safe,
    # DMITRII is fresh-loaded per episode).
    with ProcessPoolExecutor(max_workers=args.workers,
                             initializer=_worker_init,
                             initargs=(vocab, {"mu": norm.mu.tolist(),
                                               "sd": norm.sd.tolist()})) as ex:
        ep_counter = 0
        while steps_done < total:
            sched = []
            for j in range(EPI):
                k = ep_counter + j
                sched.append((k, TRAIN_OPPS[k % len(TRAIN_OPPS)],
                              seeds[(k // len(TRAIN_OPPS)) % len(seeds)],
                              k % 2))
            ep_counter += EPI
            np_state = {k: v.detach().numpy()
                        for k, v in model.state_dict().items()}
            chunks = [[] for _ in range(args.workers)]
            for i, e in enumerate(sched):
                chunks[i % args.workers].append(e)
            futs = [ex.submit(_run_eps, (np_state, ch, args.seed + it * 100003))
                    for ch in chunks if ch]
            eps = [e for f in futs for e in f.result()]
            eps.sort(key=lambda e: e["k"])
            # assemble batch + GAE
            batch = {"feat": [], "uctx": [], "mask": [], "seeds": [],
                     "u_idx": [], "m_idx": [], "logprob": [], "adv": [],
                     "ret": [], "hashes": []}
            ep_cash = []
            for e in eps:
                st = e["steps"]
                r = torch.tensor([s["reward"] for s in st])
                v = torch.tensor([s["value"] for s in st])
                d = torch.tensor([s["done"] for s in st])
                adv, ret = compute_gae(r, v, d, args.gamma, args.lam)
                for s, a, rr in zip(st, adv.tolist(), ret.tolist()):
                    batch["feat"].append(s["feat"])
                    batch["uctx"].append(s["uctx"])
                    batch["mask"].append(s["mask"])
                    batch["seeds"].append(s["seeds"])
                    batch["u_idx"].append(s["u_idx"])
                    batch["m_idx"].append(s["m_idx"])
                    batch["logprob"].append(s["logprob"])
                    batch["adv"].append(a)
                    batch["ret"].append(rr)
                    batch["hashes"].append(s["hashes"])
                ep_cash.append(e["mine"])
            stats = ppo_update(model, opt, batch, len(uvoc), len(mvoc),
                               uvoc, mvoc, clip=args.clip,
                               vf_coef=args.vf_coef, ent_coef=args.ent_coef,
                               epochs=args.epochs if not args.smoke else 1,
                               minibatch=args.minibatch)
            steps_done += len(batch["feat"])
            it += 1
            rec = {"iter": it, "steps": steps_done, "rollout_episodes": len(eps),
                   "rollout_mean_cash": float(np.mean(ep_cash)),
                   "wall_min": round((time.time() - t0) / 60, 1), **stats}
            log.write(json.dumps(rec, sort_keys=True) + "\n")
            print("iter=%d steps=%d cash=%.0f ent=%.3f clip=%.3f" % (
                it, steps_done, rec["rollout_mean_cash"], stats["ent"],
                stats["clip_frac"]), flush=True)
            while ckpt_at and steps_done >= ckpt_at[0]:
                save_ckpt(str(ckpt_at.pop(0)))
            if args.smoke:
                break
    with open(os.path.join(args.out, "checkpoints.json"), "w") as f:
        json.dump({"git": git_commit(), "seed": args.seed,
                   "total_steps": steps_done, "checkpoints": ckpts}, f, indent=1)
    print("PPO done: steps=%d iters=%d wall=%.1fmin" % (
        steps_done, it, (time.time() - t0) / 60))


if __name__ == "__main__":
    main()
