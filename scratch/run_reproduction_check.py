"""
scratch/run_reproduction_check.py
=================================
Independent reproduction check across 50 fresh holdout seeds (940,001–940,050).
Verifies deterministic equality of reward vectors across two identical passes.
"""

import os
import sys
import json
import hashlib
from concurrent.futures import ProcessPoolExecutor
from kaggle_environments import make

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in [
    BASE_DIR,
    os.path.join(BASE_DIR, "external_repos", "lixingtao123-Kaggriculture", "variant_v54_h3q4"),
    os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent"),
    os.path.join(BASE_DIR, "candidates"),
]:
    if p not in sys.path:
        sys.path.insert(0, p)

from candidates.v54_plus_residual import agent as cand_agent
from candidates.v54_plus_shop import agent as v54pp_agent

def worker_init():
    if BASE_DIR not in sys.path:
        sys.path.insert(0, BASE_DIR)
    for p in [
        os.path.join(BASE_DIR, "external_repos", "lixingtao123-Kaggriculture", "variant_v54_h3q4"),
        os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent"),
        os.path.join(BASE_DIR, "candidates"),
    ]:
        if p not in sys.path:
            sys.path.insert(0, p)

def run_seed(seed):
    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env.reset()
    for s in range(719):
        o0, o1 = env.state[0].observation, env.state[1].observation
        o0["step"], o1["step"] = s, s
        env.step([cand_agent(o0), v54pp_agent(o1)])
    return float(env.state[0].reward or 0), float(env.state[1].reward or 0)

def main():
    seeds = list(range(940001, 940051))
    print(f"Running Pass 1 across {len(seeds)} seeds...")
    with ProcessPoolExecutor(max_workers=12, initializer=worker_init) as ex:
        r1 = list(ex.map(run_seed, seeds))
    print(f"Running Pass 2 across {len(seeds)} seeds...")
    with ProcessPoolExecutor(max_workers=12, initializer=worker_init) as ex:
        r2 = list(ex.map(run_seed, seeds))

    diffs = sum(1 for a, b in zip(r1, r2) if a != b)
    h1 = hashlib.sha256(json.dumps(r1).encode()).hexdigest()
    h2 = hashlib.sha256(json.dumps(r2).encode()).hexdigest()

    print(f"Reproduction Check: {len(seeds)} seeds run twice.")
    print(f"Differences observed : {diffs}")
    print(f"Pass 1 Checksum      : {h1}")
    print(f"Pass 2 Checksum      : {h2}")
    print(f"Deterministic Match  : {h1 == h2}")

    out_file = os.path.join(BASE_DIR, "research", "residual_reproduction_check.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "seeds": [seeds[0], seeds[-1]],
            "num_seeds": len(seeds),
            "differences": diffs,
            "pass1_checksum": h1,
            "pass2_checksum": h2,
            "deterministic_match": (h1 == h2),
        }, f, indent=2)

if __name__ == "__main__":
    main()
