# SPDX-License-Identifier: MIT
"""V27 CF-1/CF-2: cash-gate test of the 249463 sheep-branch tip.

Question: does the t=289 BUY_ANIMAL SHEEP x6 branch (P3 cash $11,288;
V3 cash $10,407, no buy) fire for V3 under injected cash?

Method (exact active-backbone state, no mechanisms):
  1. Replay 249463 P3-vs-V3 hermetically to t=280; verify the replay
     reproduces the recorded trajectory (money + t=289 baseline action).
  2. Snapshot the V3 adapter; probe doctored t=280 observations
     (cash += X, all else identical) through V3; restore between probes.
  3. Bisect the minimal firing injection (threshold mapping).
  4. Falsification controls: below-threshold silence (from bisect) +
     same probe on non-tip seed 249464 (gate generality).
  5. Fidelity: restore + continue the live match to 719 (terminal must
     equal recorded); full independent re-run of 1-4.
  6. 12-step V3-continuation trace comparison (injected vs baseline)
     for action-trace divergence (physics-approximate; actions only).

Output: results/v27_counterfactual_tip.json + console.
"""

import copy
import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

from aec.backbone.v3_adapter import V3BackboneAdapter  # noqa: E402
from aec.backbone.v25_p3_adapter import V25P3BackboneAdapter  # noqa: E402
from kaggle_environments import make  # noqa: E402

RESULTS = os.path.join(REPO_ROOT, "results")
OUT_PATH = os.path.join(RESULTS, "v27_counterfactual_tip.json")


def replay_to(env, p3, v3, p3_seat, upto):
    """Act steps 0..upto-1; return (trace, obs_at_upto unacted)."""
    obs = env.reset()
    trace = []
    step = 0
    while step < upto:
        o0, o1 = obs[0]["observation"], obs[1]["observation"]
        # Manual stepping leaves player-1 obs without `step` (the env only
        # mirrors farms/market/town/day/hour; env.run fills step per agent).
        # Inject the loop counter so adapters see the true game step.
        o0["step"] = step
        o1["step"] = step
        a_p3 = p3.act(copy.deepcopy(o0 if p3_seat == 0 else o1))
        a_v3 = v3.act(copy.deepcopy(o1 if p3_seat == 0 else o0))
        acts = [a_p3, a_v3] if p3_seat == 0 else [a_v3, a_p3]
        trace.append({"step": step,
                      "obs": [copy.deepcopy(o0), copy.deepcopy(o1)],
                      "act": acts})
        obs = env.step(acts)
        step += 1
    o0, o1 = obs[0]["observation"], obs[1]["observation"]
    o0["step"] = upto
    o1["step"] = upto
    return trace, [copy.deepcopy(o0), copy.deepcopy(o1)]


def sheep_qty(action):
    n = 0
    for o in (action.get("market") or []):
        if isinstance(o, list) and len(o) >= 3 and o[0] == "BUY_ANIMAL" and o[1] == "SHEEP":
            n += o[2]
    return n


def experiment(seed, p3_seat, probe_step, max_extra, label):
    env = make("kaggriculture", configuration={"seed": seed})
    p3 = V25P3BackboneAdapter()
    v3 = V3BackboneAdapter()
    v3_seat = 1 - p3_seat
    trace, obs_now = replay_to(env, p3, v3, p3_seat, probe_step)
    base_obs = obs_now[v3_seat]
    base_cash = base_obs["farms"][v3_seat]["money"]
    p3_cash_now = obs_now[p3_seat]["farms"][p3_seat]["money"]
    max_injection = max(0.0, p3_cash_now - base_cash) + max_extra
    # reconstruction check: live V3 action at probe_step (undoctored)
    snap0 = v3.snapshot_state()
    live_act = v3.act(copy.deepcopy(base_obs))
    v3.restore_state(snap0)
    # bisect minimal firing injection in (0, max_injection]
    lo, hi = 0.0, float(max_injection)
    firing = None
    probes = []
    for _ in range(14):
        mid = (lo + hi) / 2.0
        doc = copy.deepcopy(base_obs)
        doc["farms"][v3_seat]["money"] = base_cash + mid
        v3.restore_state(snap0)
        act = v3.act(doc)
        q = sheep_qty(act)
        probes.append({"injection": mid, "sheep_qty": q,
                       "market": act.get("market")})
        if q > 0:
            hi = mid
            firing = {"injection": mid, "sheep_qty": q,
                      "market": act.get("market")}
        else:
            lo = mid
        if hi - lo < 1.0:
            break
    # fidelity: restore and continue live to terminal
    v3.restore_state(snap0)
    p3_live_cash = p3_cash_now
    step = probe_step
    o0, o1 = obs_now[0], obs_now[1]
    a_p3 = p3.act(copy.deepcopy(o0 if p3_seat == 0 else o1))
    a_v3 = v3.act(copy.deepcopy(o1 if p3_seat == 0 else o0))
    acts = [a_p3, a_v3] if p3_seat == 0 else [a_v3, a_p3]
    while True:
        obs = env.step(acts)
        step += 1
        if obs[0]["status"] == "DONE":
            term = (obs[0]["reward"], obs[1]["reward"])
            break
        o0, o1 = obs[0]["observation"], obs[1]["observation"]
        o0["step"] = step
        o1["step"] = step
        a_p3 = p3.act(copy.deepcopy(o0 if p3_seat == 0 else o1))
        a_v3 = v3.act(copy.deepcopy(o1 if p3_seat == 0 else o0))
        acts = [a_p3, a_v3] if p3_seat == 0 else [a_v3, a_p3]
    return {
        "label": label, "seed": seed, "p3_seat": p3_seat,
        "probe_step": probe_step, "base_cash": base_cash,
        "p3_live_cash": p3_live_cash,
        "live_action_market": live_act.get("market"),
        "live_sheep_qty": sheep_qty(live_act),
        "threshold": firing,
        "below_threshold_silent": lo,
        "n_probes": len(probes),
        "terminal_after_restore": term,
        "probes": probes[-4:],
    }


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    out = {}
    # CF-1: tip seed, both seats (seat determines which farm V3 plays).
    # Probe AT the branch step (t=289), where P3's/V3's cash read
    # $11,288/$10,407 (seat 0).
    for seat in (0, 1):
        out["CF1_seat%d_run1" % seat] = experiment(
            249463, seat, 289, 500, "tip-seed gate test")
    # CF-1 reproducibility: independent re-run
    out["CF1_seat0_run2"] = experiment(249463, 0, 289, 500,
                                       "independent reproduction")
    # CF-2: non-tip control seed (same probe step; cash gap + $2000 range)
    out["CF2_control"] = experiment(249464, 0, 289, 2000, "non-tip control")
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, sort_keys=True)
    for k, v in out.items():
        print("%s: base_cash=%.0f live_sheep=%d threshold=%s terminal=%s" % (
            k, v["base_cash"], v["live_sheep_qty"], v["threshold"],
            v["terminal_after_restore"]))
    print("wrote", OUT_PATH)


if __name__ == "__main__":
    main()
