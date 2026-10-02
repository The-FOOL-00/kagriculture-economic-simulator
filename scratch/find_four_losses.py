import sys, os
sys.path.insert(0, os.path.abspath("."))
import json

from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

FRESH_SEEDS = [250600 + i for i in range(32)]
losses = []

print("Scanning 64 legs of V49 vs V44 on fresh seeds [250600..250631]...")
for s in FRESH_SEEDS:
    for seat in (0, 1):
        opp_seat = 1 - seat
        sim = FastKagricultureSim(seed=s)
        obs = sim.reset(seed=s)
        
        for step in range(719):
            a49 = v49_mod.agent(obs[seat])
            a44 = v44_mod.agent(obs[opp_seat])
            obs, _, done, _ = sim.step([a49, a44] if seat == 0 else [a44, a49])
            if done:
                break
                
        cash49 = float(obs[seat]["farms"][seat]["money"])
        cash44 = float(obs[opp_seat]["farms"][opp_seat]["money"])
        margin = cash49 - cash44
        win = cash49 > cash44
        
        if not win:
            losses.append({
                "seed": s,
                "seat": seat,
                "opp_seat": opp_seat,
                "cash49": cash49,
                "cash44": cash44,
                "margin": margin,
                "result": "LOSS" if cash49 < cash44 else "TIE"
            })
            print(f"LOSS FOUND: Seed {s} | Seat {seat} | V49: ${cash49:.2f} | V44: ${cash44:.2f} | Margin: ${margin:+.2f}")

print(f"\nTotal losses found: {len(losses)} / 64 legs")
with open("scratch/four_losses_raw.json", "w") as f:
    json.dump(losses, f, indent=2)
