# SPDX-License-Identifier: MIT
"""V26 Transfer Tournament Runner (Serial and Parallel MAX_WORKERS=9 Execution)."""

import copy
import hashlib
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any, Dict

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from aec.backbone.v3_adapter import V3BackboneAdapter
from aec.backbone.v25_p3_adapter import V25P3BackboneAdapter
from aec.config import AECConfig
from aec.integration.executor import AECExecutor
from kaggle_environments import make


def run_single_v26_match(match_spec: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a single V26 match in complete process isolation."""
    arm = match_spec["arm"]
    seed = match_spec["seed"]
    seat = match_spec["seat"]

    # 1. Build Candidate Agent
    commit_count = 0
    safety_events = 0

    if arm == "ARM1_V25_STANDALONE":
        adapter = V25P3BackboneAdapter()
        backbone_id = adapter.identity()
        backbone_hash = adapter.code_hash()
        aec_config_hash = "NONE"

        def cand_agent(obs, conf=None):
            return adapter.act(obs, conf)

    elif arm == "ARM2_V25_AEC_INFRA_ONLY":
        cfg = AECConfig(
            enabled_mechanisms=(),
            operational_mode="ROBUST_MODE",
            enable_quarantine_scan=False,
        )
        adapter = V25P3BackboneAdapter(config=cfg)
        executor = AECExecutor(backbone_adapter=adapter, config=cfg)
        backbone_id = adapter.identity()
        backbone_hash = adapter.code_hash()
        aec_config_hash = hashlib.sha256(str(cfg.enabled_mechanisms).encode()).hexdigest()

        def cand_agent(obs, conf=None):
            return executor.act(obs, conf)

    elif arm == "ARM3_V25_MARKET_TIMING":
        cfg = AECConfig(
            enabled_mechanisms=("DEPENDENCY_AWARE_MARKET_TIMING",),
            operational_mode="ROBUST_MODE",
            enable_quarantine_scan=False,
        )
        adapter = V25P3BackboneAdapter(config=cfg)
        executor = AECExecutor(backbone_adapter=adapter, config=cfg)
        backbone_id = adapter.identity()
        backbone_hash = adapter.code_hash()
        aec_config_hash = hashlib.sha256(str(cfg.enabled_mechanisms).encode()).hexdigest()

        def cand_agent(obs, conf=None):
            act = executor.act(obs, conf)
            nonlocal commit_count
            if executor._latest_committed_patch is not None:
                commit_count += 1
            return act

    elif arm == "ARM4_V3_MARKET_TIMING_REFERENCE":
        cfg = AECConfig(
            enabled_mechanisms=("DEPENDENCY_AWARE_MARKET_TIMING",),
            operational_mode="ROBUST_MODE",
            enable_quarantine_scan=False,
        )
        adapter = V3BackboneAdapter(config=cfg)
        executor = AECExecutor(backbone_adapter=adapter, config=cfg)
        backbone_id = adapter.identity()
        backbone_hash = adapter.code_hash()
        aec_config_hash = hashlib.sha256(str(cfg.enabled_mechanisms).encode()).hexdigest()

        def cand_agent(obs, conf=None):
            act = executor.act(obs, conf)
            nonlocal commit_count
            if executor._latest_committed_patch is not None:
                commit_count += 1
            return act

    else:
        raise ValueError(f"Unknown arm: {arm}")

    # 2. Build Opponent Agent (Pure Frozen V3 Standalone)
    opp_adapter = V3BackboneAdapter()
    def opp_agent(obs, conf=None):
        return opp_adapter.act(obs, conf)

    # 3. Execute Match in Kaggle Environments
    env = make("kaggriculture", configuration={"seed": seed})
    agents = [cand_agent, opp_agent] if seat == 0 else [opp_agent, cand_agent]

    t0 = time.time()
    env.run(agents)
    dur = time.time() - t0

    r0 = env.steps[-1][0]["reward"]
    r1 = env.steps[-1][1]["reward"]
    cand_reward = r0 if seat == 0 else r1
    opp_reward = r1 if seat == 0 else r0
    delta = cand_reward - opp_reward

    # Action digest of candidate actions
    cand_actions = [s[seat].get("action") for s in env.steps]
    action_digest = hashlib.sha256(
        json.dumps(cand_actions, sort_keys=True).encode("utf-8")
    ).hexdigest()

    return {
        "seed": seed,
        "seat": seat,
        "arm": arm,
        "backbone_id": backbone_id,
        "backbone_hash": backbone_hash,
        "aec_config_hash": aec_config_hash,
        "engine_version": "1.32.7",
        "terminal_reward": cand_reward,
        "opponent_reward": opp_reward,
        "paired_delta": delta,
        "action_digest": action_digest,
        "commit_count": commit_count,
        "safety_events": safety_events,
        "duration_sec": round(dur, 2),
        "completion_status": "COMPLETED",
    }


def main():
    results_dir = os.path.join(os.path.dirname(__file__), "..", "results")
    os.makedirs(results_dir, exist_ok=True)
    checkpoint_file = os.path.join(results_dir, "v26_aec_transfer_matches.jsonl")

    manifest_path = os.path.join(os.path.dirname(__file__), "..", "V26_COHORT_MANIFEST.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    seeds = manifest["seeds"]
    arms = [arm["arm_id"] for arm in manifest["arm_definitions"]]
    seats = manifest["seats"]

    completed = set()
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        rec = json.loads(line)
                        completed.add((rec["arm"], rec["seed"], rec["seat"]))
                    except Exception:
                        pass

    queue = []
    for arm in arms:
        for seed in seeds:
            for seat in seats:
                if (arm, seed, seat) not in completed:
                    queue.append({"arm": arm, "seed": seed, "seat": seat})

    print(f"Total matches to execute: {len(queue)} (Already completed: {len(completed)})")
    if not queue:
        print("All matches already completed.")
        return

    MAX_WORKERS = 9
    print(f"Launching parallel execution with MAX_WORKERS = {MAX_WORKERS}...")
    t_start = time.time()
    completed_count = 0

    with open(checkpoint_file, "a", encoding="utf-8") as f_out:
        with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_spec = {executor.submit(run_single_v26_match, spec): spec for spec in queue}
            for future in as_completed(future_to_spec):
                try:
                    res = future.result()
                    f_out.write(json.dumps(res) + "\n")
                    f_out.flush()
                    completed_count += 1
                    print(
                        f"[{completed_count}/{len(queue)}] {res['arm']} | Seed {res['seed']} | "
                        f"Seat {res['seat']} | Reward: {res['terminal_reward']:,.0f} | "
                        f"Delta: {res['paired_delta']:+,.0f} | Commits: {res['commit_count']}"
                    )
                except Exception as e:
                    print(f"ERROR executing match: {e}")

    print(f"Tournament execution completed in {time.time() - t_start:.1f}s.")


if __name__ == "__main__":
    main()
