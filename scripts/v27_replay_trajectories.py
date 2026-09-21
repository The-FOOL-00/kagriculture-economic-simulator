# SPDX-License-Identifier: MIT
"""V27 Phase 3: deterministic trajectory replay + fidelity audit.

Replays historical matches with their ORIGINAL loaders and captures
compact per-step trajectories for the behavioral ledger, first-divergence
detection, and regime decomposition.

Series replayed (200 matches):
  DISC-P1/DISC-P2/DISC-P3 : V25 discovery file loader (run_v25_parallel semantics)
  CONF-P3                 : V25 confirmation file loader
  V26A1                   : V26 ARM1 adapter loader (run_v26_transfer_tournament semantics)

Alignment (verified empirically): env.steps[i]['observation'] is the
pre-action state at game step i; env.steps[i]['action'] (i>=1) is the
action taken at game step i-1; env.steps[0]['action'] is a placeholder.
All captured action[t] below use TRUE game-step indexing (action[t] acted
on obs[t]); the fidelity digest hashes the RAW recorded array exactly
like V25/V26 did.

Output: results/v27_trajectories.jsonl (checkpointed, resumable).
Fidelity vs the vendored checkpoints is reported, never asserted:
mismatches are findings (see V27_QUARANTINE note for DISC-P3).
"""

import hashlib
import importlib.util
import json
import os
import shutil
import sys
import tarfile
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

RESULTS = os.path.join(REPO_ROOT, "results")
OUT_PATH = os.path.join(RESULTS, "v27_trajectories.jsonl")

GOODS9 = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG",
          "MILK", "WOOL", "FERTILIZER"]
SHED12 = GOODS9 + ["GOOSE", "COW", "SHEEP"]
SEEDS5 = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"]


def _verb(act):
    if isinstance(act, list) and act:
        return act[0]
    return "NONE"


def summarize_tiles(tiles):
    agg = {"empty": 0, "locked": 0, "plant": 0, "dry": 0, "weed": 0,
           "pasture": 0, "coop": 0, "yield": 0,
           "cow": 0, "sheep": 0, "goose": 0, "unfed": 0,
           "wheat": 0, "melon": 0, "strawberry": 0, "carrot": 0,
           "tomato": 0}
    for row in tiles:
        for t in row:
            if t is None:
                agg["empty"] += 1
            elif isinstance(t, str):
                agg["locked"] += 1
            elif isinstance(t, dict):
                k = t.get("kind")
                if k == "PLANT":
                    agg["plant"] += 1
                    if not t.get("watered_today", False):
                        agg["dry"] += 1
                    c = (t.get("crop") or "").lower()
                    if c in agg:
                        agg[c] += 1
                    try:
                        agg["yield"] += int(t.get("yield_units", 0) or 0)
                    except (TypeError, ValueError):
                        pass
                elif k == "WEED":
                    agg["weed"] += 1
                elif k == "PASTURE":
                    agg["pasture"] += 1
                    a = (t.get("animal") or "").lower()
                    if a in ("cow", "sheep", "goose"):
                        agg[a] += 1
                    try:
                        agg["yield"] += int(t.get("yield_units", 0) or 0)
                    except (TypeError, ValueError):
                        pass
                    if not t.get("fed_today", True):
                        agg["unfed"] += 1
                elif k == "COOP":
                    agg["coop"] += 1
    return agg


def capture(env, cand_seat):
    steps = env.steps
    n = len(steps)
    obs_step = [None] * n
    seats = [{}, {}]
    for s in (0, 1):
        seats[s] = {
            "money": [0.0] * n, "hands_n": [0] * n,
            "farmer": [None] * n, "hands": [None] * n,
            "quads_n": [0] * n, "hires": [0] * n,
            "shed": [], "seeds": [], "tiles": [],
            "f_op": [None] * n, "h_ops": [None] * n,
            "market": [None] * n,
        }
    market_snaps = []
    last_market_sig = None
    for i in range(n):
        row = steps[i]
        o0 = row[0]["observation"]
        obs_step[i] = o0.get("step")
        # true game-step actions: action[t] Taken at t == recorded row t+1
        for s in (0, 1):
            ob = row[s]["observation"]
            farm = ob["farms"][s]
            st = seats[s]
            st["money"][i] = farm.get("money", 0.0)
            hands = farm.get("hands", []) or []
            st["hands_n"][i] = len(hands)
            st["farmer"][i] = list(farm.get("farmer") or [-1, -1])
            st["hands"][i] = [list(h) for h in hands]
            st["quads_n"][i] = len(farm.get("unlocked_quadrants", []) or [])
            st["hires"][i] = farm.get("hires_today", 0) or 0
            priv = ob.get("private", {}) or {}
            shed = priv.get("shed", {}) or {}
            seeds = priv.get("seeds", {}) or {}
            st["shed"].append([int(shed.get(g, 0) or 0) for g in SHED12])
            st["seeds"].append([int(seeds.get(g, 0) or 0) for g in SEEDS5])
            st["tiles"].append(summarize_tiles(farm.get("tiles", []) or []))
            if i + 1 < n:
                a = steps[i + 1][s].get("action") or {}
                st["f_op"][i] = a.get("farmer") or ["PASS"]
                st["h_ops"][i] = [h or ["PASS"] for h in (a.get("hands") or [])]
                st["market"][i] = a.get("market") or []
            else:
                st["f_op"][i] = ["END"]
                st["h_ops"][i] = []
                st["market"][i] = []
        mkt = o0.get("market", {}) or {}
        pr = mkt.get("prices", {}) or {}
        inv = mkt.get("inventory", {}) or {}
        sig = (tuple(pr.get(g) for g in GOODS9),
               tuple(inv.get(g) for g in GOODS9))
        active = bool(seats[0]["market"][i]) or bool(seats[1]["market"][i])
        if sig != last_market_sig or i % 12 == 0 or active:
            market_snaps.append({"step": i,
                                 "prices": [pr.get(g) for g in GOODS9],
                                 "inventory": [inv.get(g) for g in GOODS9]})
            last_market_sig = sig
    # shop / quad unlock events (seat-0 view; seat views asserted equal in test)
    shops = []
    seen_shops = set()
    for i in range(n):
        for sh in steps[i][0]["observation"]["town"].get("unlocked_shops", []) or []:
            if sh not in seen_shops:
                seen_shops.add(sh)
                shops.append([i, sh])
    return {"n_steps": n, "obs_step": obs_step, "seats": seats,
            "market": market_snaps, "shop_unlocks": shops}


def v25_idle_rate(env, seat):
    early_idle = 0
    early_total = 0
    for s_idx in range(min(100, len(env.steps))):
        a = env.steps[s_idx][seat].get("action") or {}
        f = a.get("farmer") or ["PASS"]
        h = a.get("hands") or []
        if f and f[0] == "PASS":
            early_idle += 1
        early_idle += sum(1 for x in h if x and x[0] == "PASS")
        early_total += (1 + len(h))
    return early_idle / max(1, early_total)


def fidelity_digest(env, seat):
    acts = [s[seat].get("action") for s in env.steps]
    return hashlib.sha256(json.dumps(acts, sort_keys=True).encode("utf-8")).hexdigest()


def run_file_match(seed, seat, cand_file):
    """Exact V25 loader semantics (fresh process state per call)."""
    import sys as _sys
    _sys.path.insert(0, REPO_ROOT)
    v3_tar = os.path.join(REPO_ROOT, "submission_Vj_kc_v3.tar.gz")
    work = tempfile.mkdtemp(prefix="v27_file_")
    try:
        with tarfile.open(v3_tar, "r:gz") as tar:
            tar.extractall(work)
        spec_v3 = importlib.util.spec_from_file_location(
            "v27v3_%d_%d_%d" % (seed, seat, time.time_ns()),
            os.path.join(work, "main.py"))
        mod_v3 = importlib.util.module_from_spec(spec_v3)
        spec_v3.loader.exec_module(mod_v3)
        spec_c = importlib.util.spec_from_file_location(
            "v27cand_%d_%d_%d" % (seed, seat, time.time_ns()), cand_file)
        mod_c = importlib.util.module_from_spec(spec_c)
        spec_c.loader.exec_module(mod_c)
        from kaggle_environments import make
        env = make("kaggriculture", configuration={"seed": seed})
        agents = [mod_c.agent, mod_v3.agent] if seat == 0 else [mod_v3.agent, mod_c.agent]
        t0 = time.time()
        env.run(agents)
        return env, time.time() - t0
    finally:
        shutil.rmtree(work, ignore_errors=True)


def run_adapter_match(seed, seat):
    """Exact V26 ARM1 loader semantics."""
    import sys as _sys
    _sys.path.insert(0, REPO_ROOT)
    from aec.backbone.v3_adapter import V3BackboneAdapter
    from aec.backbone.v25_p3_adapter import V25P3BackboneAdapter
    from kaggle_environments import make
    p3 = V25P3BackboneAdapter()
    v3 = V3BackboneAdapter()
    agents = ([lambda o, c=None: p3.act(o, c), lambda o, c=None: v3.act(o, c)]
              if seat == 0 else
              [lambda o, c=None: v3.act(o, c), lambda o, c=None: p3.act(o, c)])
    env = make("kaggriculture", configuration={"seed": seed})
    t0 = time.time()
    env.run(agents)
    return env, time.time() - t0


def run_one(spec):
    series = spec["series"]
    seed = spec["seed"]
    seat = spec["seat"]
    if series == "V26A1":
        env, dur = run_adapter_match(seed, seat)
    else:
        cand_path = spec["cand_path"]
        env, dur = run_file_match(seed, seat, cand_path)
    r0 = env.steps[-1][0]["reward"]
    r1 = env.steps[-1][1]["reward"]
    cand_r = r0 if seat == 0 else r1
    base_r = r1 if seat == 0 else r0
    rec = {
        "series": series, "seed": seed, "seat": seat,
        "key": "%s:%d:%d" % (series, seed, seat),
        "cand_reward": cand_r, "base_reward": base_r,
        "delta": cand_r - base_r,
        "action_digest": fidelity_digest(env, seat),
        "early_idle_rate": v25_idle_rate(env, seat),
        "duration_sec": dur,
        "traj": capture(env, seat),
    }
    exp = spec.get("expect")
    if exp:
        rec["expect"] = exp
        rec["fidelity"] = {
            "cand_match": cand_r == exp["cand"],
            "base_match": base_r == exp["base"],
            "digest_match": rec["action_digest"] == exp["digest"],
        }
    return rec


def load_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


VENDOR_HASHES = {
    "v25_p1_macro.py": "7f605723ba1c48dd14628c1b3932d07478461f59fe0890a69ac971e3feb17512",
    "v25_p2_production.py": "3c6847758227d66fc2d11750fe44ddc543e617fcef13b7673f86160df0caae7d",
}


def vendor_branch_file(name):
    """Materialize a V25-branch-only candidate file into runtime temp.

    DISC-P1/P2 sources live only on research/v25-coherent-planner; they are
    replay INPUTS, not V27 deliverables, so they are extracted from the
    pinned git blob (hash-asserted) instead of added to the worktree.
    """
    import hashlib as _hl
    import subprocess as _sp
    dest_dir = "/tmp/v27_vendor"
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, name)
    if not os.path.exists(dest):
        blob = _sp.run(["git", "show",
                        "research/v25-coherent-planner:candidates/%s" % name],
                       cwd=REPO_ROOT, capture_output=True, check=True).stdout
        with open(dest, "wb") as f:
            f.write(blob)
    with open(dest, "rb") as f:
        digest = _hl.sha256(f.read()).hexdigest()
    assert digest == VENDOR_HASHES[name], (name, digest)
    return dest


def build_queue():
    cand_paths = {
        "DISC-P1": vendor_branch_file("v25_p1_macro.py"),
        "DISC-P2": vendor_branch_file("v25_p2_production.py"),
        "DISC-P3": os.path.join(REPO_ROOT, "candidates", "v25_p3_unified.py"),
        "CONF-P3": os.path.join(REPO_ROOT, "candidates", "v25_p3_unified.py"),
    }
    queue = []
    for r in load_jsonl(os.path.join(RESULTS, "v25_backbone_matches.jsonl")):
        series = {"V25_P1_MACRO": "DISC-P1", "V25_P2_PRODUCTION": "DISC-P2",
                  "V25_P3_UNIFIED": "DISC-P3"}[r["candidate"]]
        queue.append({"series": series, "seed": r["seed"], "seat": r["seat"],
                      "cand_path": cand_paths[series],
                      "expect": {"cand": r["candidate_reward"],
                                 "base": r["baseline_reward"],
                                 "digest": r["action_digest"]}})
    for r in load_jsonl(os.path.join(RESULTS, "v25_confirmation_matches.jsonl")):
        queue.append({"series": "CONF-P3", "seed": r["seed"], "seat": r["seat"],
                      "cand_path": cand_paths["CONF-P3"],
                      "expect": {"cand": r["candidate_reward"],
                                 "base": r["baseline_reward"],
                                 "digest": r["action_digest"]}})
    for r in load_jsonl(os.path.join(RESULTS, "v26_aec_transfer_matches.jsonl")):
        if r["arm"] != "ARM1_V25_STANDALONE":
            continue
        queue.append({"series": "V26A1", "seed": r["seed"], "seat": r["seat"],
                      "expect": {"cand": r["terminal_reward"],
                                 "base": r["opponent_reward"],
                                 "digest": r["action_digest"]}})
    return queue


def main():
    import sys as _sys
    _sys.stdout.reconfigure(encoding="utf-8")
    completed = set()
    if os.path.exists(OUT_PATH):
        for line in open(OUT_PATH, "r", encoding="utf-8"):
            if line.strip():
                try:
                    completed.add(json.loads(line)["key"])
                except Exception:
                    pass
    queue = [q for q in build_queue()
             if "%s:%d:%d" % (q["series"], q["seed"], q["seat"]) not in completed]
    print("queued=%d completed=%d" % (len(queue), len(completed)), flush=True)
    if not queue:
        print("nothing to do")
        return
    n_ok = {"DISC-P1": 0, "DISC-P2": 0, "DISC-P3": 0, "CONF-P3": 0, "V26A1": 0}
    n_tot = dict(n_ok)
    t_start = time.time()
    with open(OUT_PATH, "a", encoding="utf-8") as f_out:
        with ProcessPoolExecutor(max_workers=9) as ex:
            futs = {ex.submit(run_one, spec): spec for spec in queue}
            done = 0
            for fut in as_completed(futs):
                spec = futs[fut]
                try:
                    rec = fut.result()
                except Exception as e:
                    print("ERROR %s:%d:%d %r" % (spec["series"], spec["seed"],
                                                spec["seat"], e), flush=True)
                    continue
                f_out.write(json.dumps(rec) + "\n")
                f_out.flush()
                done += 1
                fid = rec.get("fidelity", {})
                ok = fid.get("digest_match", None)
                n_tot[rec["series"]] += 1
                if ok:
                    n_ok[rec["series"]] += 1
                else:
                    print("FIDELITY-DIFF %s seed=%d seat=%d got=%s/%s/%s want=%s/%s/%s"
                          % (rec["series"], rec["seed"], rec["seat"],
                             rec["cand_reward"], rec["base_reward"],
                             rec["action_digest"][:12],
                             rec["expect"]["cand"], rec["expect"]["base"],
                             rec["expect"]["digest"][:12]), flush=True)
                if done % 20 == 0:
                    print("... %d/%d (%.0fs)" % (done, len(queue), time.time() - t_start),
                          flush=True)
    print("fidelity digest-match by series:",
          {k: "%d/%d" % (n_ok[k], n_tot[k]) for k in n_tot}, flush=True)
    print("elapsed %.1fs" % (time.time() - t_start), flush=True)


if __name__ == "__main__":
    main()
