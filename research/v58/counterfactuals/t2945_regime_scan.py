#!/usr/bin/env python3
"""V58 conditional follow-up: thomastschinkel_2945 regime scan (committed).

Trigger: run ONLY to characterize the t2945-vs-V49 boundary found in the plan
tournament (mean margin -$79 over 40 legs). Question: does the 6C/6S herd-mix
line EVER beat V49's 12C/5S line on any seed regime?

Design: t2945 vs V49, 60 fresh tournament-split seeds (10120-10179) x 2 seats
= 120 legs, per-leg margins saved for regime analysis (seed, seat, margin,
winner). Seeds avoid holdouts, V56 ladder range, and the plan-tournament
seeds (10100-10119).

Output: research/v58/counterfactuals/T2945_REGIME_SCAN.json
Verdict rule: >=1 t2945 win => isolate the winning regime (shops/prices) and
  evaluate a herd-mix rule; 0 wins => boundary holds, no selector justified.
"""
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, REPO)
os.chdir(REPO)
sys.stdout.reconfigure(line_buffering=True)

from scripts.master_harness import run_single_match  # noqa: E402

SEEDS = list(range(10120, 10180))
T2945 = "research/v47/elite_corpus/agents/thomastschinkel_2945/main.py"
V49 = "candidates/v49_meta_fusion/main.py"
OUT = os.path.join(REPO, "research", "v58", "counterfactuals", "T2945_REGIME_SCAN.json")

for s in SEEDS:
    assert not (214200 <= s <= 214249 or 340090 <= s <= 340199 or 249695 <= s <= 249734), s
    assert not (250600 <= s <= 250632), s
    assert not (10100 <= s <= 10119), s


def main():
    tasks = []
    for s in SEEDS:
        tasks.append((T2945, V49, s, 720, False))
        tasks.append((V49, T2945, s, 720, True))
    legs = []
    with ProcessPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(run_single_match, t) for t in tasks]
        for i, f in enumerate(as_completed(futs), 1):
            r = f.result()
            # normalize: diff from t2945 perspective (agent0 = t2945 by construction)
            legs.append({"seed": r["seed"], "swapped": r["swapped"],
                         "t2945": r["r0"], "v49": r["r1"], "diff": r["diff"],
                         "winner": "t2945" if r["winner"] == 0 else ("v49" if r["winner"] == 1 else "draw"),
                         "status": [r["status0"], r["status1"]], "error": r["error"]})
            if i % 24 == 0 or i == len(tasks):
                w = sum(1 for l in legs if l["winner"] == "t2945")
                print(f"  {i}/{len(tasks)} t2945 wins={w}", flush=True)
    wins = sum(1 for l in legs if l["winner"] == "t2945")
    diffs = [l["diff"] for l in legs]
    import numpy as np
    out = {"seeds": SEEDS, "legs": len(legs), "t2945_wins": wins,
           "mean_diff": float(np.mean(diffs)), "median_diff": float(np.median(diffs)),
           "min_diff": float(min(diffs)), "max_diff": float(max(diffs)),
           "win_legs": [l for l in legs if l["winner"] == "t2945"],
           "closest_losses": sorted([l for l in legs if l["winner"] == "v49"],
                                    key=lambda l: -l["diff"])[:10],
           "all_legs": sorted(legs, key=lambda l: (l["seed"], l["swapped"]))}
    with open(OUT, "w") as f:
        json.dump(out, f, indent=1)
    print(f"t2945 regime scan: {wins}/{len(legs)} wins, mean {out['mean_diff']:+.0f}, "
          f"max {out['max_diff']:+.0f}. wrote {OUT}")


if __name__ == "__main__":
    main()
