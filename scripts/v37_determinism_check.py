# SPDX-License-Identifier: MIT
"""V37: Determinism check on staged V35 agent."""

import hashlib
import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STAGING_DIR = os.path.join(REPO_ROOT, "submission_final_v35")
sys.path.insert(0, STAGING_DIR)

import main
from kaggle_environments import make

SEED = 249676  # Safe dev seed

def run_episode():
    env = make("kaggriculture", configuration={"seed": SEED})
    # Run agent vs passive
    def passive(obs, cfg=None):
        return {"farmer": ["PASS"], "hands": [], "market": []}
    
    env.run([main.agent, passive])
    actions = [step[0]["action"] for step in env.steps]
    rewards = (env.steps[-1][0]["reward"], env.steps[-1][1]["reward"])
    action_dump = json.dumps(actions, sort_keys=True)
    digest = hashlib.sha256(action_dump.encode("utf-8")).hexdigest()
    return actions, rewards, digest

def main_test():
    act1, rew1, dig1 = run_episode()
    act2, rew2, dig2 = run_episode()
    
    print(f"Run 1: Reward = {rew1}, Digest = {dig1}")
    print(f"Run 2: Reward = {rew2}, Digest = {dig2}")
    
    mismatches = []
    for step_idx, (a1, a2) in enumerate(zip(act1, act2)):
        if a1 != a2:
            mismatches.append((step_idx, a1, a2))
            
    res = {
        "seed": SEED,
        "run1_reward": rew1[0],
        "run2_reward": rew2[0],
        "run1_digest": dig1,
        "run2_digest": dig2,
        "digests_match": dig1 == dig2,
        "rewards_match": rew1 == rew2,
        "mismatches_count": len(mismatches),
        "status": "PASS" if (dig1 == dig2 and rew1 == rew2 and len(mismatches) == 0) else "FAIL"
    }
    print("DETERMINISM_RESULT:", json.dumps(res, indent=2))
    assert res["status"] == "PASS", "Determinism check failed!"

if __name__ == "__main__":
    main_test()
