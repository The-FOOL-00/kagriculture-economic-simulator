import sys
import os
import json

REPO_ROOT = r"c:\Users\Sundareswaran\Kagriculture"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from research.v47.elite_benchmark.run_elite_benchmark import load_agent as load_elite_agent
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v48_challenger.main as v48_mod
from research.v50.counterfactuals.test_exact_crop import make_exact_crop_agent

with open("research/v50/loss_regimes/v49_loss_corpus.json") as f:
    corpus = json.load(f)

print(f"Testing Exact Crop Cap across the 11 V49 Losses against V44:")
print("=" * 80)

opp = load_elite_agent("V44")
exact_agent = make_exact_crop_agent(seed_thresh=624)

for idx, loss in enumerate(corpus):
    seed = loss["seed"]
    seat = loss["seat"]
    opp_seat = 1 - seat
    
    # 1. Run V49
    sim49 = FastKagricultureSim(seed=seed)
    obs49 = sim49.reset(seed=seed)
    for _ in range(719):
        a49 = v49_mod.agent(obs49[seat])
        aopp = opp.act(obs49[opp_seat]) if hasattr(opp, "act") else opp(obs49[opp_seat])
        obs49, _, _, _ = sim49.step([a49, aopp] if seat == 0 else [aopp, a49])
    c49 = obs49[seat]["farms"][seat]["money"]
    copp49 = obs49[opp_seat]["farms"][opp_seat]["money"]
    w49 = c49 > copp49
    
    # 2. Run Exact Agent
    sim_ex = FastKagricultureSim(seed=seed)
    obs_ex = sim_ex.reset(seed=seed)
    for _ in range(719):
        a_ex = exact_agent(obs_ex[seat])
        aopp = opp.act(obs_ex[opp_seat]) if hasattr(opp, "act") else opp(obs_ex[opp_seat])
        obs_ex, _, _, _ = sim_ex.step([a_ex, aopp] if seat == 0 else [aopp, a_ex])
    c_ex = obs_ex[seat]["farms"][seat]["money"]
    copp_ex = obs_ex[opp_seat]["farms"][opp_seat]["money"]
    w_ex = c_ex > copp_ex
    
    delta = c_ex - c49
    rescue = not w49 and w_ex
    print(f"Loss {idx+1:02d} (Seed {seed} Seat {seat}): V49={c49:.0f} vs Opp={copp49:.0f} (Margin={c49-copp49:+.0f})")
    print(f"   Exact Agent: Cash={c_ex:.0f}, Delta vs V49={delta:+.1f}, Rescued={rescue}")
    print(f"   Final Seeds V49: {dict(obs49[seat]['private']['seeds'])}")
    print(f"   Final Seeds Exact: {dict(obs_ex[seat]['private']['seeds'])}")
