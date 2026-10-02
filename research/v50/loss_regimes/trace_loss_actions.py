import sys
import os
import json

REPO_ROOT = r"c:\Users\Sundareswaran\Kagriculture"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from research.v47.elite_benchmark.run_elite_benchmark import load_agent as load_elite_agent
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

with open("research/v50/loss_regimes/v49_loss_corpus.json") as f:
    corpus = json.load(f)

for idx, loss in enumerate(corpus):
    seed = loss["seed"]
    seat = loss["seat"]
    opp_seat = 1 - seat
    sim = FastKagricultureSim(seed=seed)
    obs = sim.reset(seed=seed)
    opp = load_elite_agent("V44")
    agent_v49 = v49_mod.agent
    
    route_chosen = None
    late_mkt_actions = []
    
    for step in range(719):
        a_v49 = agent_v49(obs[seat])
        a_opp = opp.act(obs[opp_seat]) if hasattr(opp, "act") else opp(obs[opp_seat])
        
        if step == 0:
            route_chosen = v49_mod._IMPL.chassis.players[seat].get("route")
        
        mkt = a_v49.get("market", [])
        if step >= 600 and mkt:
            late_mkt_actions.append((step, mkt))
            
        actions = [a_v49, a_opp] if seat == 0 else [a_opp, a_v49]
        obs, _, _, _ = sim.step(actions)
        
    cash_v49 = obs[seat]["farms"][seat]["money"]
    cash_opp = obs[opp_seat]["farms"][opp_seat]["money"]
    print(f"Loss {idx+1:02d}: Seed {seed}, Seat {seat}, Route: {route_chosen}, Cash: {cash_v49} vs {cash_opp} (Margin: {cash_v49-cash_opp})")
    print(f"  Late mkt actions count >= 600: {len(late_mkt_actions)}")
    for s, m in late_mkt_actions[:8]:
        print(f"    Step {s}: {m}")
