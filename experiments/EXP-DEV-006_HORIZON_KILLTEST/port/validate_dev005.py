# SPDX-License-Identifier: MIT
"""DEV-005 frozen-replay validation of the kagsim Python port.

Replays the exact EXP-DEV-005 Discovery procedure (50 seeds x 2 CRN matches)
through the port and demands EXACT agreement with frozen artifacts:
  - RAW_RESULTS.json: match deltas, paired means, outcomes, plans
  - DECISION_EVENTS.csv: every checkpoint field incl. liquidity, shops,
    expected_incremental_value (price-path validation), decisions
Any mismatch fails loudly. Allowed seeds: 247000-247049 ONLY.
"""
import os
import sys
import csv
import json
import time
import importlib.util

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
PORT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PORT_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

import kagsim_py as kagsim
from dev_005_confirmed_shop_scheduler import Dev005ConfirmedShopScheduler

BASELINE_PATH = os.path.join(BASE_DIR, "candidates", "compiled_v54_plus_residual.py")
EXP005 = os.path.join(BASE_DIR, "experiments", "EXP-DEV-005")


def assert_cohort(seed):
    if not (247000 <= seed <= 247049):
        raise RuntimeError(f"seed {seed} outside validation cohort!")
    for lo, hi in ((214200, 214249), (50050, 50099), (245000, 245049), (246000, 246049)):
        if lo <= seed <= hi:
            raise RuntimeError(f"QUARANTINED seed {seed}!")


def load_baseline(name):
    spec = importlib.util.spec_from_file_location(name, BASELINE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_seed(seed):
    assert_cohort(seed)
    deci = []
    g0 = kagsim.Game(seed)
    c0 = Dev005ConfirmedShopScheduler(seat=0, seed=seed)
    b1 = load_baseline(f"vbase_{seed}_m0")
    while not g0.done:
        g0.step(c0.act(g0.observe(0)), b1.agent(g0.observe(1)))
    r0c, r0b = float(g0.reward(0)), float(g0.reward(1))
    for ev in c0.decision_events:
        d = dict(ev)
        d["match"] = 0
        deci.append(d)
    g1 = kagsim.Game(seed)
    b0 = load_baseline(f"vbase_{seed}_m1")
    c1 = Dev005ConfirmedShopScheduler(seat=1, seed=seed)
    while not g1.done:
        g1.step(b0.agent(g1.observe(0)), c1.act(g1.observe(1)))
    r1b, r1c = float(g1.reward(0)), float(g1.reward(1))
    for ev in c1.decision_events:
        d = dict(ev)
        d["match"] = 1
        deci.append(d)
    d0, d1 = r0c - r0b, r1c - r1b
    return {"seed": seed, "m0": (r0c, r0b, d0), "m1": (r1b, r1c, d1),
            "paired": 0.5 * (d0 + d1), "plans": (c0.active_plan, c1.active_plan),
            "activated": any(e["decision"] == "SPECIALIZE_CONFIRMED" for e in deci),
            "deci": deci}


def main():
    t_start = time.time()
    frozen = {r["seed"]: r for r in json.load(open(os.path.join(EXP005, "RAW_RESULTS.json")))}
    fdeci = {}
    with open(os.path.join(EXP005, "DECISION_EVENTS.csv")) as f:
        for row in csv.DictReader(f):
            fdeci.setdefault((int(row["seed"]), int(row["match"])), {})[int(row["step"])] = row
    n_delta_checks = n_event_checks = 0
    fails = []
    for idx, seed in enumerate(range(247000, 247050), 1):
        r = run_seed(seed)
        fz = frozen[seed]
        checks = [("m0d", r["m0"][2], fz["match0_delta"]),
                  ("m1d", r["m1"][2], fz["match1_delta"]),
                  ("paired", r["paired"], fz["paired_mean_delta"]),
                  ("m0c", r["m0"][0], fz["match0_cand_p0"]),
                  ("m0b", r["m0"][1], fz["match0_base_p1"]),
                  ("m1b", r["m1"][0], fz["match1_base_p0"]),
                  ("m1c", r["m1"][1], fz["match1_cand_p1"])]
        n_delta_checks += len(checks)
        for name, got, exp in checks:
            if got != exp:
                fails.append(f"seed {seed} {name}: got {got} exp {exp}")
        if r["plans"] != (fz["cand0_plan"], fz["cand1_plan"]):
            fails.append(f"seed {seed} plans: got {r['plans']} exp {(fz['cand0_plan'], fz['cand1_plan'])}")
        if r["activated"] != fz["activated"]:
            fails.append(f"seed {seed} activated: got {r['activated']} exp {fz['activated']}")
        for ev in r["deci"]:
            fe = fdeci[(seed, ev["match"])][ev["step"]]
            n_event_checks += 1
            pairs = [("current_shops", str(ev["current_shops"])),
                     ("confirmation_status", str(ev["confirmation_status"])),
                     ("selected_route", ev["selected_route"]),
                     ("best_candidate_plan", ev["best_candidate_plan"]),
                     ("expected_incremental_value", str(ev["expected_incremental_value"])),
                     ("liquidity", str(float(ev["liquidity"]))),
                     ("decision", ev["decision"]),
                     ("rejection_reason", ev["rejection_reason"]),
                     ("active_plan_after", ev["active_plan_after"])]
            for k, got in pairs:
                if got != fe[k]:
                    fails.append(f"seed {seed} m{ev['match']} step {ev['step']} {k}: got {got!r} exp {fe[k]!r}")
        print(f"[{idx:02d}/50] seed {seed}: paired {r['paired']:+.1f} "
              f"(frozen {fz['paired_mean_delta']:+.1f}) "
              f"{'OK' if r['paired'] == fz['paired_mean_delta'] else 'MISMATCH'}", flush=True)
        if len(fails) > 15:
            print("... too many failures, aborting")
            break
    print(f"\nchecks: {n_delta_checks} deltas + {n_event_checks} events (+plans/activation)")
    print(f"elapsed: {time.time() - t_start:.1f}s")
    if fails:
        print("FAILURES:")
        for x in fails[:20]:
            print("  " + x)
        return 1
    print("DEV-005 REPLAY: 100/100 games bit-identical, 400/400 events identical -> PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
