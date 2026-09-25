# SPDX-License-Identifier: MIT
"""V37: Cleanroom smoke test executing strictly from submission_final_v35."""

import json
import os
import subprocess
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STAGING_DIR = os.path.join(REPO_ROOT, "submission_final_v35")

TEST_SCRIPT = """
import os, sys, json
import kaggle_environments

# Ensure cwd is staging dir and sys.path[0] is staging dir
assert os.path.abspath(os.getcwd()) == os.path.abspath(r'''__STAGING_DIR__''')

import main
assert hasattr(main, 'agent'), 'Missing agent callable'
assert callable(main.agent), 'agent is not callable'

# 1. Step 0 dummy smoke
obs0 = {
    'step': 0,
    'player': 0,
    'farms': [{'cash': 1000, 'hands': []}, {'cash': 1000, 'hands': []}],
    'market': {'prices': {'WHEAT': {'price': 10}}}
}
act0 = main.agent(obs0)
print('STEP_0_ACTION:', json.dumps(act0))
assert act0['market'] == [['BUY_PRODUCT', 'WHEAT', 25], ['SELL', 'WHEAT', 25]], f'Unexpected step 0 market: {act0[\"market\"]}'

# 2. Step 1 dummy smoke
obs1 = {
    'step': 1,
    'player': 0,
    'farms': [{'cash': 1000, 'hands': []}, {'cash': 1000, 'hands': []}],
    'market': {'prices': {'WHEAT': {'price': 10}}}
}
act1 = main.agent(obs1)
print('STEP_1_ACTION_OK: True')

# 3. Full match execution on safe dev seed 249675
from kaggle_environments import make
env = make('kaggriculture', configuration={'seed': 249675})

# Passive opponent for cleanroom isolated validation
def passive(obs, cfg=None):
    return {'farmer': ['PASS'], 'hands': [], 'market': []}

env.run([main.agent, passive])
r0 = env.steps[-1][0]['reward']
r1 = env.steps[-1][1]['reward']
steps_count = len(env.steps)

print('MATCH_RESULT:', json.dumps({
    'seed': 249675,
    'steps': steps_count,
    'v35_cash': r0,
    'opponent_cash': r1,
    'v35_win': r0 > r1,
    'cleanroom_status': 'PASS'
}))
"""

def main():
    test_code = TEST_SCRIPT.replace("__STAGING_DIR__", STAGING_DIR)
    
    # Clean environment without repo in PYTHONPATH
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    
    proc = subprocess.run(
        [sys.executable, "-c", test_code],
        cwd=STAGING_DIR,
        capture_output=True,
        text=True,
        env=env
    )
    
    print("RETURN CODE:", proc.returncode)
    print("STDOUT:\n", proc.stdout)
    if proc.stderr:
        print("STDERR:\n", proc.stderr)
        
    assert proc.returncode == 0, "Cleanroom smoke test failed!"

if __name__ == "__main__":
    main()
