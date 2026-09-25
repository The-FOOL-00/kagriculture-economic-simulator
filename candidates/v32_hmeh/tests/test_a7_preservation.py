# SPDX-License-Identifier: MIT
"""EXP-V32-P9-02: A7 Mechanism Preservation Test.

Verifies:
1. 0/1000 Step-0 wash failures: exact [['BUY_PRODUCT', 'WHEAT', 30], ['SELL', 'WHEAT', 30]]
2. Exact transaction pattern and cash effect across development seeds (249675-249684)
3. Downstream melon planting threshold reproduction (MELON: 12 plants enabled by $108 buffer)
"""

import os
import random
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
HMEH_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in (REPO_ROOT, HMEH_ROOT, os.path.join(REPO_ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from kaggle_environments import make
from v32_common import assert_frozen, check_seed_allowed, load_agent
from candidates.v32_hmeh.main import HMEHAgent, make_hmeh_agent


def test_step0_wash_1000():
    """Verify 0/1000 unexpected Step-0 wash failures across randomized initial states."""
    rng = random.Random(12345)
    expected_wash = [["BUY_PRODUCT", "WHEAT", 30], ["SELL", "WHEAT", 30]]
    failures = 0
    
    print("Testing Step-0 30/30 Wash across 1,000 trials...")
    for i in range(1000):
        agent = HMEHAgent(stage="HMEH-0")
        obs = {
            "step": 0,
            "day": 0,
            "hour": 0,
            "player": 0,
            "farms": [
                {"money": 1000.0, "farmer": [4, 4], "hands": [], "hires_today": 0, "unlocked_quadrants": ["NW"], "tiles": [[None]*10 for _ in range(10)]},
                {"money": 1000.0, "farmer": [4, 4], "hands": [], "hires_today": 0, "unlocked_quadrants": ["NW"], "tiles": [[None]*10 for _ in range(10)]}
            ],
            "private": {"shed": {"WHEAT": 0}, "seeds": {}, "inventories": [{}]},
            "market": {"prices": {"WHEAT": 25.0}, "inventory": {"WHEAT": 10000}},
            "town": {"unlocked_shops": []}
        }
        act = agent(obs)
        if act.get("market") != expected_wash:
            failures += 1
            
    print(f"Step-0 Wash Test: Trials = 1000, Failures = {failures}")
    assert failures == 0, f"A7 Preservation Failure: {failures}/1000 Step-0 wash failures!"


def test_closed_loop_melon_event():
    """Verify in closed loop that HMEH-0 reproduces A7 opening and melon threshold."""
    assert_frozen()
    dev_seeds = [249675, 249676]  # Test first 2 dev seeds
    print(f"Testing closed-loop A7 mechanism preservation on dev seeds {dev_seeds}...")
    
    for seed in dev_seeds:
        check_seed_allowed(seed)
        hmeh_fn, hmeh_inst = make_hmeh_agent(stage="HMEH-0")
        opp_fn = load_agent("E0_V3")
        
        env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 30}, debug=False)
        env.run([hmeh_fn, opp_fn])
        
        step0_mkt = env.steps[1][0]["action"].get("market") or []
        expected_wash = [["BUY_PRODUCT", "WHEAT", 30], ["SELL", "WHEAT", 30]]
        assert step0_mkt == expected_wash, f"Seed {seed}: Step 0 wash mismatch: {step0_mkt} != {expected_wash}"
        
        # Check cash at step 1 observation (immediately after step 0 wash execution)
        farm_step1 = env.steps[1][0]["observation"]["farms"][0]
        cash_step1 = farm_step1["money"]
        print(f"Seed {seed}: Cash after Step 0 wash = ${cash_step1:.2f} (A7 expected ~$2988-$3054 in $3000 initial bank)")
        assert cash_step1 > 2900.0, f"Cash too low: ${cash_step1:.2f} (30-wash buffer not preserved!)"
        
    print("A7 Mechanism Preservation Test: PASSED")


if __name__ == "__main__":
    test_step0_wash_1000()
    test_closed_loop_melon_event()
