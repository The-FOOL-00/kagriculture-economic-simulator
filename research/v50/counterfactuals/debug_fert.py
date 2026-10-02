import sys
import os

REPO_ROOT = r"c:\Users\Sundareswaran\Kagriculture"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from research.v47.elite_benchmark.run_elite_benchmark import load_agent as load_elite_agent
import candidates.v49_meta_fusion.main as v49_mod
from research.v50.counterfactuals.run_exact_counterfactuals import get_remaining_fertilize_demands

seed = 250416
sim = FastKagricultureSim(seed=seed)
obs = sim.reset(seed=seed)
opp = load_elite_agent("V44")
agent_v49 = v49_mod.agent
chassis = v49_mod._IMPL.chassis

for step in range(719):
    act = agent_v49(obs[0])
    aopp = opp.act(obs[1])
    mkt = act.get("market", [])
    fert_buys = [o for o in mkt if len(o) >= 3 and o[0] == "BUY_PRODUCT" and o[1] == "FERTILIZER"]
    if fert_buys:
        native = chassis.players[0]
        rem = get_remaining_fertilize_demands(native, step, chassis)
        inv = obs[0].get("private", {}).get("shed", {}).get("FERTILIZER", 0)
        print(f"Step {step}: BUY FERT {fert_buys}, rem_fert={rem}, inv={inv}")

    obs, _, _, _ = sim.step([act, aopp])
