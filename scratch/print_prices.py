import os, sys
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from candidates.v44_economic_portfolio.main import V44CandidateController
from candidates.v32_rlx2.opponents import load_league_opponent

sim = FastKagricultureSim(seed=249657)
v44 = V44CandidateController()
opp = load_league_opponent("E2_A7")
o0, o1 = sim.reset()

while not sim.done:
    s = o0.get("step", 0)
    p = o0.get("market", {}).get("prices", {})
    inv = o0.get("market", {}).get("inventory", {})
    if 688 <= s <= 706:
        print(f"Step {s:3d} | Straw P: {p.get('STRAWBERRY'):3d} (Inv: {inv.get('STRAWBERRY'):5d}) | Milk P: {p.get('MILK'):3d} | Wool P: {p.get('WOOL'):3d}")
    [o0, o1], _, _, _ = sim.step([v44.act(o0), opp(o1)])
