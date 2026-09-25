# SPDX-License-Identifier: MIT
import os
import sys
import json
import time

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from kaggle_environments import make
from scripts.v32_common import load_agent, assert_frozen, telemetry

def test_match(seed=249677, seat=0):
    assert_frozen()
    a7 = load_agent("E9_AST")
    dmitrii = load_agent("E8_DMITRII")
    
    fn_a7 = lambda o, c=None: a7.act(o, c)
    fn_dmitrii = lambda o, c=None: dmitrii.act(o, c)
    
    agents = [fn_a7, fn_dmitrii] if seat == 0 else [fn_dmitrii, fn_a7]
    env = make("kaggriculture", configuration={"seed": seed})
    t0 = time.time()
    env.run(agents)
    dur = time.time() - t0
    
    p0_reward = env.steps[-1][0]["reward"]
    p1_reward = env.steps[-1][1]["reward"]
    
    a7_rew = p0_reward if seat == 0 else p1_reward
    dmit_rew = p1_reward if seat == 0 else p0_reward
    delta = a7_rew - dmit_rew
    
    print(f"Seed {seed} | A7 Seat {seat} ({dur:.1f}s): A7 Cash=${a7_rew:,.2f} | Dmitrii Cash=${dmit_rew:,.2f} | Margin (A7 - Dmitrii)={delta:+,.2f}")
    return env, a7_rew, dmit_rew, delta

if __name__ == "__main__":
    print("Testing Seat 0 (A7=P0, Dmitrii=P1)...")
    env0, a7_0, dmit_0, delta_0 = test_match(249677, seat=0)
    print("Testing Seat 1 (Dmitrii=P0, A7=P1)...")
    env1, a7_1, dmit_1, delta_1 = test_match(249677, seat=1)
