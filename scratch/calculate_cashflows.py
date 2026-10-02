import sys, os
sys.path.insert(0, os.path.abspath("."))
from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v44_economic_portfolio.main as v44_mod

for s in (250621, 250617):
    sim = FastKagricultureSim(seed=s)
    obs = sim.reset(seed=s)
    
    c0_prev = 3000.0
    c1_prev = 3000.0
    inflow0, outflow0 = 0.0, 0.0
    inflow1, outflow1 = 0.0, 0.0
    
    # Also categorize outflows: seeds, animals, hires, land
    outflows_by_type0 = {"seed": 0.0, "animal": 0.0, "hire": 0.0, "land": 0.0, "other": 0.0}
    outflows_by_type1 = {"seed": 0.0, "animal": 0.0, "hire": 0.0, "land": 0.0, "other": 0.0}
    
    for step in range(719):
        a0 = v49_mod.agent(obs[0])
        a1 = v44_mod.agent(obs[1])
        obs, _, done, _ = sim.step([a0, a1])
        c0 = float(obs[0]['farms'][0]['money'])
        c1 = float(obs[1]['farms'][1]['money'])
        d0 = c0 - c0_prev
        d1 = c1 - c1_prev
        if d0 > 0: inflow0 += d0
        else: outflow0 += (-d0)
        if d1 > 0: inflow1 += d1
        else: outflow1 += (-d1)
        c0_prev = c0
        c1_prev = c1
        
    print(f"=== SEED {s} ===")
    print(f"  V49: Inflow = ${inflow0:,.2f}, Outflow = ${outflow0:,.2f}, Final = ${c0_prev:,.2f}")
    print(f"  V44: Inflow = ${inflow1:,.2f}, Outflow = ${outflow1:,.2f}, Final = ${c1_prev:,.2f}")
    print(f"  Delta Inflow  (V49 - V44): ${inflow0 - inflow1:+,.2f}")
    print(f"  Delta Outflow (V49 - V44): ${outflow0 - outflow1:+,.2f}")
    print(f"  Net Margin: ${c0_prev - c1_prev:+,.2f}")
