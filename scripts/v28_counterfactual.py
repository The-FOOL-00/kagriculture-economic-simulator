# SPDX-License-Identifier: MIT
"""V28 counterfactual audit (V26 backbone-aware probes as diagnostic only).

CF-V28-1: 249534/seat1 step-290 expansion bundle (A7 fires BUY_LAND +
  SHEEPx6 + HIREx2; V3 silent). Replay to t=290, bisect V3's firing
  cash threshold, brain-swap probes (V3-brain on A7-state; A7-brain on
  V3-state), restore-and-continue fidelity, independent re-run.
CF-V28-2: 249530 step-18 melon-seed budget (A7 buys MELONx2, V3 x1).
  Bisect the cash injection at which V3's live policy buys x2.
  Quantifies the wash-savings -> melon causality on a typical seed.

Predicted (probe firing) vs realized (frozen trajectory consequence)
reported separately, never equated. Output:
results/v28_counterfactual.json + console.
"""

import copy
import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from v28_confirmation_tournament import assert_frozen  # noqa: E402
from aec.backbone.v3_adapter import V3BackboneAdapter  # noqa: E402
from aec.backbone.v27_ablation_adapters import V27AblationAdapter  # noqa: E402
from kaggle_environments import make  # noqa: E402

OUT = os.path.join(REPO_ROOT, "results", "v28_counterfactual.json")


def replay_to(env, a7, v3, a7_seat, upto):
    cfg = env.configuration
    obs = env.reset()
    step = 0
    while step < upto:
        o0, o1 = obs[0]["observation"], obs[1]["observation"]
        o0["step"] = step
        o1["step"] = step
        a_a7 = a7.act(copy.deepcopy(o0 if a7_seat == 0 else o1), cfg)
        a_v3 = v3.act(copy.deepcopy(o1 if a7_seat == 0 else o0), cfg)
        acts = [a_a7, a_v3] if a7_seat == 0 else [a_v3, a_a7]
        obs = env.step(acts)
        step += 1
    o0, o1 = obs[0]["observation"], obs[1]["observation"]
    o0["step"] = upto
    o1["step"] = upto
    return [copy.deepcopy(o0), copy.deepcopy(o1)]


def sheep_qty(action):
    n = 0
    for o in (action.get("market") or []):
        if isinstance(o, list) and len(o) >= 3 and o[0] == "BUY_ANIMAL" \
                and o[1] == "SHEEP":
            n += o[2]
    return n


def melon_qty(action):
    for o in (action.get("market") or []):
        if isinstance(o, list) and len(o) >= 3 and o[0] == "BUY_SEED" \
                and o[1] == "MELON":
            return o[2]
    return 0


def continue_to_terminal(env, a7, v3, a7_seat, obs_now, step):
    cfg = env.configuration
    o0, o1 = obs_now[0], obs_now[1]
    a_a7 = a7.act(copy.deepcopy(o0 if a7_seat == 0 else o1), cfg)
    a_v3 = v3.act(copy.deepcopy(o1 if a7_seat == 0 else o0), cfg)
    acts = [a_a7, a_v3] if a7_seat == 0 else [a_v3, a_a7]
    while True:
        obs = env.step(acts)
        step += 1
        if obs[0]["status"] == "DONE":
            return (obs[0]["reward"], obs[1]["reward"])
        o0, o1 = obs[0]["observation"], obs[1]["observation"]
        o0["step"] = step
        o1["step"] = step
        a_a7 = a7.act(copy.deepcopy(o0 if a7_seat == 0 else o1), cfg)
        a_v3 = v3.act(copy.deepcopy(o1 if a7_seat == 0 else o0), cfg)
        acts = [a_a7, a_v3] if a7_seat == 0 else [a_v3, a_a7]


def cf1_tip(run_tag):
    seed, a7_seat, probe = 249534, 1, 289
    v3_seat = 1 - a7_seat
    env = make("kaggriculture", configuration={"seed": seed})
    a7 = V27AblationAdapter(variant="V27-ABL-A7")
    v3 = V3BackboneAdapter()
    obs_now = replay_to(env, a7, v3, a7_seat, probe)
    base_obs = obs_now[v3_seat]
    a7_obs = obs_now[a7_seat]
    base_cash = base_obs["farms"][v3_seat]["money"]
    a7_cash = a7_obs["farms"][a7_seat]["money"]
    snap_v3 = v3.snapshot_state()
    snap_a7 = a7.snapshot_state()
    live_v3 = v3.act(copy.deepcopy(base_obs), env.configuration)
    v3.restore_state(snap_v3)
    live_a7 = a7.act(copy.deepcopy(a7_obs), env.configuration)
    a7.restore_state(snap_a7)
    # brain swaps (exact foreign state, own internal history)
    v3.restore_state(snap_v3)
    swap_v3_on_a7state = v3.act(copy.deepcopy(a7_obs), env.configuration)
    v3.restore_state(snap_v3)
    a7.restore_state(snap_a7)
    try:
        swap_a7_on_v3state = a7.act(copy.deepcopy(base_obs), env.configuration)
    except Exception as e:
        swap_a7_on_v3state = {"error": repr(e)}
    a7.restore_state(snap_a7)
    # bisect V3 firing threshold
    lo, hi = 0.0, float(max(0.0, a7_cash - base_cash) + 500.0)
    firing = None
    for _ in range(14):
        mid = (lo + hi) / 2.0
        doc = copy.deepcopy(base_obs)
        doc["farms"][v3_seat]["money"] = base_cash + mid
        v3.restore_state(snap_v3)
        q = sheep_qty(v3.act(doc, env.configuration))
        if q > 0:
            hi = mid
            firing = {"injection": mid, "sheep_qty": q}
        else:
            lo = mid
        if hi - lo < 1.0:
            break
    v3.restore_state(snap_v3)
    a7.restore_state(snap_a7)
    term = continue_to_terminal(env, a7, v3, a7_seat, obs_now, probe)
    return {"label": "CF-V28-1 tip gate " + run_tag, "seed": seed,
            "probe_step": probe, "v3_cash": base_cash, "a7_cash": a7_cash,
            "live_v3_market": live_v3.get("market"),
            "live_v3_sheep": sheep_qty(live_v3),
            "live_a7_market": live_a7.get("market"),
            "live_a7_sheep": sheep_qty(live_a7),
            "swap_v3_on_a7state_market": swap_v3_on_a7state.get("market"),
            "swap_v3_on_a7state_sheep": sheep_qty(swap_v3_on_a7state),
            "swap_a7_on_v3state_market": swap_a7_on_v3state.get("market"),
            "swap_a7_on_v3state_sheep": sheep_qty(swap_a7_on_v3state)
            if isinstance(swap_a7_on_v3state, dict) else None,
            "threshold": firing, "below_silent": lo,
            "terminal_after_restore": term}


def cf2_melon():
    seed, a7_seat, probe = 249530, 0, 17
    v3_seat = 1 - a7_seat
    env = make("kaggriculture", configuration={"seed": seed})
    a7 = V27AblationAdapter(variant="V27-ABL-A7")
    v3 = V3BackboneAdapter()
    obs_now = replay_to(env, a7, v3, a7_seat, probe)
    base_obs = obs_now[v3_seat]
    a7_obs = obs_now[a7_seat]
    base_cash = base_obs["farms"][v3_seat]["money"]
    a7_cash = a7_obs["farms"][a7_seat]["money"]
    snap_v3 = v3.snapshot_state()
    snap_a7 = a7.snapshot_state()
    live_v3 = v3.act(copy.deepcopy(base_obs), env.configuration)
    v3.restore_state(snap_v3)
    live_a7 = a7.act(copy.deepcopy(a7_obs), env.configuration)
    a7.restore_state(snap_a7)
    lo, hi = 0.0, float(max(0.0, a7_cash - base_cash) + 500.0)
    firing = None
    for _ in range(14):
        mid = (lo + hi) / 2.0
        doc = copy.deepcopy(base_obs)
        doc["farms"][v3_seat]["money"] = base_cash + mid
        v3.restore_state(snap_v3)
        q = melon_qty(v3.act(doc, env.configuration))
        if q >= 2:
            hi = mid
            firing = {"injection": mid, "melon_qty": q}
        else:
            lo = mid
        if hi - lo < 1.0:
            break
    v3.restore_state(snap_v3)
    a7.restore_state(snap_a7)
    term = continue_to_terminal(env, a7, v3, a7_seat, obs_now, probe)
    return {"label": "CF-V28-2 melon budget", "seed": seed,
            "probe_step": probe, "v3_cash": base_cash, "a7_cash": a7_cash,
            "live_v3_market": live_v3.get("market"),
            "live_a7_market": live_a7.get("market"),
            "threshold_x2": firing, "below_silent": lo,
            "terminal_after_restore": term}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    assert_frozen()
    out = {"CF1_run1": cf1_tip("run1"),
           "CF1_run2_independent": cf1_tip("run2"),
           "CF2": cf2_melon()}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    for k, v in out.items():
        print("%s: %s" % (k, json.dumps(
            {kk: v[kk] for kk in v if kk not in ("live_v3_market", "live_a7_market",
                                                "swap_v3_on_a7state_market",
                                                "swap_a7_on_v3state_market")})))
    print("CF1 live_a7_market:", out["CF1_run1"]["live_a7_market"])
    print("CF1 live_v3_market:", out["CF1_run1"]["live_v3_market"])
    print("CF1 swap markets:", out["CF1_run1"]["swap_v3_on_a7state_market"],
          "|", out["CF1_run1"]["swap_a7_on_v3state_market"])
    print("wrote", OUT)


if __name__ == "__main__":
    main()
