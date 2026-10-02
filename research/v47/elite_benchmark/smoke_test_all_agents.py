# SPDX-License-Identifier: MIT
"""Smoke test all extracted elite benchmark agents."""

from __future__ import annotations
import importlib.util
import json
import os
import sys
import time

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from candidates.v44_economic_portfolio.main import V44CandidateController

AGENTS_DIR = os.path.join(REPO_ROOT, "research/v47/elite_corpus/agents")
MANIFEST_PATH = os.path.join(REPO_ROOT, "research/v47/elite_corpus/elite_manifest.json")


def load_agent_function(entrypoint_rel: str):
    abs_path = os.path.join(REPO_ROOT, entrypoint_rel.split(":")[0])
    fn_name = entrypoint_rel.split(":")[1]
    mod_dir = os.path.dirname(abs_path)

    # Insert mod_dir at beginning of sys.path so intra-package imports work
    orig_path = list(sys.path)
    if mod_dir not in sys.path:
        sys.path.insert(0, mod_dir)

    mod_name = os.path.basename(os.path.dirname(abs_path)) + "_mod"
    spec = importlib.util.spec_from_file_location(mod_name, abs_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    fn = getattr(mod, fn_name)

    # Restore sys.path
    sys.path = orig_path
    return fn


def main():
    print("=" * 80)
    print("V47 ELITE BENCHMARK: SMOKE TESTING ALL 9 ELITE AGENTS")
    print("=" * 80)

    manifest = json.load(open(MANIFEST_PATH, "r", encoding="utf-8"))
    sim_seed = 249635

    results = []
    for item in manifest:
        agent_id = item["agent_id"]
        entrypoint = item["entrypoint"]
        if not entrypoint.startswith("research/") and not entrypoint.startswith("extracted_") and not entrypoint.startswith("external_"):
            entrypoint = f"research/v47/elite_corpus/agents/{agent_id}/{entrypoint}"

        print(f"\n--- Smoke Testing [{agent_id}] ({item['title']}) ---")
        t0 = time.time()
        try:
            agent_fn = load_agent_function(entrypoint)
            v44 = V44CandidateController()
            sim = FastKagricultureSim(seed=sim_seed)
            obs0, obs1 = sim.reset(seed=sim_seed)

            # Run 50 steps
            for st in range(50):
                a0 = v44.act(obs0)
                a1 = agent_fn(obs1)
                (obs0, obs1), (r0, r1), done, _ = sim.step([a0, a1])

            elapsed = time.time() - t0
            print(f"  SUCCESS: 50 steps completed in {elapsed:.3f}s")
            print(f"  V44 cash: ${obs0['farms'][0]['money']}, {agent_id} cash: ${obs1['farms'][1]['money']}")
            results.append({"agent_id": agent_id, "status": "PASS", "elapsed": elapsed, "error": None})
        except Exception as e:
            elapsed = time.time() - t0
            print(f"  FAILED with exception: {e}")
            results.append({"agent_id": agent_id, "status": "FAIL", "elapsed": elapsed, "error": str(e)})

    print("\n" + "=" * 80)
    print("SMOKE TEST SUMMARY")
    print("=" * 80)
    for r in results:
        status_str = "PASS" if r["status"] == "PASS" else f"FAIL ({r['error']})"
        print(f"  [{r['agent_id']}]: {status_str}")


if __name__ == "__main__":
    main()
