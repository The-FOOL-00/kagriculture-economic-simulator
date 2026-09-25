# SPDX-License-Identifier: MIT
"""V37: Archive roundtrip validation test."""

import hashlib
import json
import os
import subprocess
import sys
import tarfile
import tempfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ARCHIVE_PATH = os.path.join(REPO_ROOT, "final_submission", "V35_FINAL_SUBMISSION.tar.gz")
STAGED_PATH = os.path.join(REPO_ROOT, "submission_final_v35", "main.py")

TEST_RUNNER = """
import os, sys, json
import kaggle_environments

import main
assert callable(main.agent), 'Agent not callable'

# 1. Step 0 Check
obs0 = {
    'step': 0,
    'player': 0,
    'farms': [{'cash': 1000, 'hands': []}, {'cash': 1000, 'hands': []}],
    'market': {'prices': {'WHEAT': {'price': 10}}}
}
act0 = main.agent(obs0)
assert act0['market'] == [['BUY_PRODUCT', 'WHEAT', 25], ['SELL', 'WHEAT', 25]], f'Market mismatch: {act0[\"market\"]}'

# 2. Match execution on safe dev seed 249677
from kaggle_environments import make
env = make('kaggriculture', configuration={'seed': 249677})

def passive(obs, cfg=None):
    return {'farmer': ['PASS'], 'hands': [], 'market': []}

env.run([main.agent, passive])
r0 = env.steps[-1][0]['reward']
r1 = env.steps[-1][1]['reward']

print(json.dumps({
    'seed': 249677,
    'steps': len(env.steps),
    'v35_reward': r0,
    'opponent_reward': r1,
    'step0_market': act0['market'],
    'status': 'PASS'
}))
"""

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def validate_roundtrip():
    staged_sha = sha256_file(STAGED_PATH)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Extract archive
        with tarfile.open(ARCHIVE_PATH, "r:gz") as tar:
            tar.extractall(tmpdir)

        extracted_file = os.path.join(tmpdir, "main.py")
        assert os.path.exists(extracted_file), "Extracted main.py not found"
        extracted_sha = sha256_file(extracted_file)

        assert extracted_sha == staged_sha, f"Hash mismatch: {extracted_sha} vs {staged_sha}"

        # Run isolated execution test
        env = dict(os.environ)
        env.pop("PYTHONPATH", None)

        proc = subprocess.run(
            [sys.executable, "-c", TEST_RUNNER],
            cwd=tmpdir,
            capture_output=True,
            text=True,
            env=env
        )

        print("RETURN CODE:", proc.returncode)
        print("STDOUT:\n", proc.stdout)
        if proc.stderr:
            print("STDERR:\n", proc.stderr)

        assert proc.returncode == 0, "Round-trip execution failed!"

    print("ROUND-TRIP VALIDATION: ALL CHECKS PASSED.")

if __name__ == "__main__":
    validate_roundtrip()
