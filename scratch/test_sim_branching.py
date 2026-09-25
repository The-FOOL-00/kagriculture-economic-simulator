import copy
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from candidates.v35_a7_opening.main import V35OpeningController
from candidates.v32_rlx2.opponents import load_league_opponent

def test_branching():
    sim = FastKagricultureSim(seed=249635)
    v35 = V35OpeningController()
    opp = load_league_opponent("E8_DMITRII")
    obs0, obs1 = sim.reset(seed=249635)

    # step 200 turns
    for _ in range(200):
        act0 = v35.act(obs0)
        act1 = opp(obs1)
        [obs0, obs1], _, _, _ = sim.step([act0, act1])

    print("Step reached:", sim.step_idx)

    # Attempt deepcopy of sim
    try:
        sim_clone = copy.deepcopy(sim)
        print("Deepcopy succeeded!")
        # step both independently
        act0 = v35.act(obs0)
        act1 = opp(obs1)
        [obs0_a, obs1_a], r_a, done_a, _ = sim.step([act0, act1])
        [obs0_b, obs1_b], r_b, done_b, _ = sim_clone.step([act0, act1])
        print("Step after clone match:", obs0_a["step"] == obs0_b["step"])
        print("Farm 0 money match:", obs0_a["farms"][0]["money"] == obs0_b["farms"][0]["money"])
    except Exception as e:
        print("Deepcopy failed:", e)

if __name__ == "__main__":
    test_branching()
