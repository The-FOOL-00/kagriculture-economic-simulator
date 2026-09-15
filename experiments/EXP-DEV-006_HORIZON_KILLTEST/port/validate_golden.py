# SPDX-License-Identifier: MIT
"""Golden validation: replay bundled cppsim traces through the Python port.

Demands EXACT per-step money (both seats) + market inventory match against the
TRUTH block recorded from the REAL environment. Far stricter than the bundled
test (which checks only final banks within 0.5).
"""
import os
import sys

PORT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PORT_DIR)
import kagsim_py as kagsim

ROOT = os.path.abspath(os.path.join(PORT_DIR, "..", "..", "..",
                                    "external_repos", "kaggriculture-cppsim"))
OPS = ["PASS", "NORTH", "SOUTH", "EAST", "WEST", "PICKUP", "DROP", "PLACE",
       "PLANT", "WATER", "HARVEST", "FERTILIZE", "DIG",
       "BUILD_COOP", "BUILD_PASTURE", "FEED", "COLLECT_FERTILIZER", "CARE"]
ITEMS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK",
         "WOOL", "FERTILIZER", "GOOSE", "COW", "SHEEP"]
MOPS = ["NONE", "HIRE", "BUY_LAND", "BUY_SEED", "BUY_PRODUCT", "BUY_ANIMAL", "SELL"]
PRODS = ITEMS[:9]


def unit_of(op, arg, n):
    return [OPS[op], ITEMS[arg], n]


def order_of(op, item, n):
    if op <= 0 or op >= len(MOPS):
        return None
    if op in (1, 2):
        return [MOPS[op]]
    return [MOPS[op], ITEMS[item], n]


def parse_trace(path):
    lines = open(path).read().splitlines()
    seed, n = (int(x) for x in lines[0].split())
    i = 1
    if lines[i].startswith("CONFIG"):
        assert lines[i] == "CONFIG 720 10 3000 10 24 100 0.005 3 4 24 1", lines[i]
        i += 1
    acts = [[], []]
    for _t in range(n):
        for seat in (0, 1):
            toks = lines[i].split()
            i += 1
            nu, no = int(toks[0]), int(toks[1])
            p = 2
            units = []
            for _ in range(nu):
                units.append(unit_of(int(toks[p]), int(toks[p + 1]), int(toks[p + 2])))
                p += 3
            orders = []
            for _ in range(no):
                o = order_of(int(toks[p]), int(toks[p + 1]), int(toks[p + 2]))
                p += 3
                if o:
                    orders.append(o)
            acts[seat].append({"farmer": units[0] if units else ["PASS"],
                               "hands": units[1:], "market": orders})
    assert lines[i] == "TRUTH", path
    i += 1
    truth = []
    while i < len(lines):
        truth.append([float(x) for x in lines[i].split()])
        i += 1
    return seed, acts, truth


def validate_trace(path):
    seed, acts, truth = parse_trace(path)
    n_steps = len(acts[0])
    assert len(truth) == n_steps + 1, (path, len(truth), n_steps)
    g = kagsim.Game(seed)
    mism = 0
    for t in range(n_steps + 1):
        o = g.observe(0)
        m0 = float(o["farms"][0]["money"])
        m1 = float(o["farms"][1]["money"])
        inv = [float(o["market"]["inventory"][p]) for p in PRODS]
        exp = truth[t]
        if m0 != exp[0] or m1 != exp[1] or inv != exp[2:]:
            if mism < 3:
                print(f"  MISMATCH t={t}: got ({m0},{m1},{inv}) exp {exp}")
            mism += 1
        if t < n_steps and not g.done:
            g.step(acts[0][t], acts[1][t])
    assert g.done, "game should be done after 719 steps"
    return mism


def main():
    import glob
    traces = sorted(glob.glob(os.path.join(ROOT, "traces", "replay_*.txt")))
    assert traces, "no traces found"
    total_mism = 0
    total_checks = 0
    for p in traces:
        seed, acts, truth = parse_trace(p)
        checks = (len(acts[0]) + 1) * 11
        total_checks += checks
        mism = validate_trace(p)
        total_mism += mism
        print(f"{'PASS' if mism == 0 else 'FAIL'} {os.path.basename(p)}: "
              f"{checks} exact checkpoints, {mism} mismatches")
    print(f"GOLDEN: {total_checks} checkpoints, {total_mism} mismatches -> "
          f"{'PASS' if total_mism == 0 else 'FAIL'}")
    return 1 if total_mism else 0


if __name__ == "__main__":
    raise SystemExit(main())
