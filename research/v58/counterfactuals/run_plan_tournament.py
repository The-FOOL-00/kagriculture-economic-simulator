#!/usr/bin/env python3
"""V58 fixed elite plan tournament (committed, Stage B / spec section 14).

Each executable elite plan vs V49, paired legs, both seats, tournament seeds
10100-10119 (20 seeds x 2 seats = 40 legs per matchup, 400 legs total).
Authoritative engine via scripts/master_harness.py (kaggle-environments 1.32.7).

Horse-race question (decision hierarchy step 1): does ANY fixed elite plan
beat V49 anywhere? Per-leg records support regime analysis (seed/winner/margin
for both seats).

Output: research/v58/counterfactuals/PLAN_TOURNAMENT.json
"""
import json
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, REPO)
os.chdir(REPO)
sys.stdout.reconfigure(line_buffering=True)

from scripts.master_harness import run_paired_tournament  # noqa: E402

SEEDS = list(range(10100, 10120))
V49 = "candidates/v49_meta_fusion/main.py"
PLANS = {
    "v44": "candidates/v44_economic_portfolio/main.py",
    "kaitofukami_v48_3009": "research/v47/elite_corpus/agents/kaitofukami_v48_3009/main.py",
    "saiteja_mega_3000": "research/v47/elite_corpus/agents/saiteja_mega_3000/main.py",
    "thomastschinkel_2945": "research/v47/elite_corpus/agents/thomastschinkel_2945/main.py",
    "tetsutani_pasture": "research/v47/elite_corpus/agents/tetsutani_pasture/main.py",
    "indarkarhana_top10": "research/v47/elite_corpus/agents/indarkarhana_top10/main.py",
    "dmitrii_lb2800": "extracted_agents/dmitrii_lb2800/main.py",
    "P3090_claimed": "external_repos/lixingtao123-Kaggriculture/public_3090/output/main.py",
    "P3000_claimed": "external_repos/lixingtao123-Kaggriculture/opponents/public_3000/main.py",
    "night_harvest": "external_repos/lixingtao123-Kaggriculture/opponents/night_harvest/main.py",
}
OUT = os.path.join(REPO, "research", "v58", "counterfactuals", "PLAN_TOURNAMENT.json")

# Protected holdouts + V56 ladder range guard
for s in SEEDS:
    assert not (214200 <= s <= 214249 or 340090 <= s <= 340199 or 249695 <= s <= 249734), s
    assert not (250600 <= s <= 250632), s


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    table = {"seeds": SEEDS, "engine": "kaggle-environments 1.32.7",
             "matchups": {}, "legs_total": 0}
    for name, path in PLANS.items():
        print(f"=== {name} vs V49 ({len(SEEDS)} seeds x 2 seats) ===", flush=True)
        # run_paired_tournament(agent0, agent1): agent0 = elite, agent1 = V49
        res = run_paired_tournament(path, V49, SEEDS, max_workers=8, show_progress=True)
        table["matchups"][name] = res
        table["legs_total"] += res["n_matches"]
        print(f"  elite WR={res['pooled_wr']:.3f} wins={res['total_wins']}/{res['n_matches']} "
              f"mean_margin={res['mean_margin']:+.0f} catast={res['catastrophic']}", flush=True)
        with open(OUT, "w") as f:
            json.dump(table, f, indent=1)
    print(f"wrote {OUT} legs={table['legs_total']}")


if __name__ == "__main__":
    main()
