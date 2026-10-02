import sys, os
sys.path.insert(0, os.path.abspath("."))
import json

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

def get_snapshot_at_step(seed, target_step):
    sim = FastKagricultureSim(seed=seed)
    obs = sim.reset()
    for step in range(target_step):
        a0 = v49_mod.agent(obs[0], sim.configuration)
        a1 = v44_mod.agent(obs[1], sim.configuration)
        obs, rewards, done, info = sim.step([a0, a1])
        if done:
            break
    return obs[0]

for s in [0, 144, 150, 168, 215, 216]:
    obs_416 = get_snapshot_at_step(250416, s)
    obs_436 = get_snapshot_at_step(250436, s)
    
    # Let's compare opponent farm
    opp_416 = obs_416["farms"][1]
    opp_436 = obs_436["farms"][1]
    
    opp_diff = []
    for k in ["money", "farmer", "hands", "unlocked_quadrants", "hires_today"]:
        if opp_416[k] != opp_436[k]:
            opp_diff.append(f"{k}: 416={opp_416[k]} vs 436={opp_436[k]}")
            
    # tiles diff
    tile_diff_count = 0
    for r in range(10):
        for c in range(10):
            if opp_416["tiles"][r][c] != opp_436["tiles"][r][c]:
                tile_diff_count += 1
    if tile_diff_count > 0:
        opp_diff.append(f"tiles mismatch in {tile_diff_count} cells")
        
    mkt_diff = []
    for k in ["prices", "inventory"]:
        if obs_416["market"][k] != obs_436["market"][k]:
            diffs = {prod: (obs_416["market"][k][prod], obs_436["market"][k][prod]) 
                     for prod in obs_416["market"][k] if obs_416["market"][k][prod] != obs_436["market"][k][prod]}
            mkt_diff.append(f"market {k}: {diffs}")
            
    town_diff = []
    if obs_416["town"]["unlocked_shops"] != obs_436["town"]["unlocked_shops"]:
        town_diff.append(f"shops: 416={obs_416['town']['unlocked_shops']} vs 436={obs_436['town']['unlocked_shops']}")
        
    print(f"=== STEP {s} ===")
    print(f"Opponent Farm Diffs: {opp_diff if opp_diff else '100% IDENTICAL'}")
    print(f"Market Diffs: {mkt_diff if mkt_diff else '100% IDENTICAL'}")
    print(f"Town Diffs: {town_diff if town_diff else '100% IDENTICAL'}")
