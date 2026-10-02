import sys
import os

REPO_ROOT = r"c:\Users\Sundareswaran\Kagriculture"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from research.v47.elite_benchmark.run_elite_benchmark import load_agent as load_elite_agent
import candidates.v49_meta_fusion.main as v49_mod

def make_v49_fert_guard(fert_thresh=646):
    base_agent = v49_mod.agent
    def agent(obs, configuration=None):
        act = base_agent(obs, configuration)
        try:
            step = int(obs.get("step", 0) or 0)
            if step < fert_thresh:
                return act
            if not isinstance(act, dict):
                return act
            mkt = list(act.get("market") or [])
            # Filter out BUY_PRODUCT FERTILIZER
            new_mkt = [o for o in mkt if not (len(o) >= 2 and o[0] == "BUY_PRODUCT" and o[1] == "FERTILIZER")]
            if len(new_mkt) != len(mkt):
                act = dict(act)
                act["market"] = new_mkt[:10]
        except Exception:
            pass
        return act
    return agent

if __name__ == "__main__":
    seeds = [250400 + i for i in range(16)]
    fert_agent = make_v49_fert_guard(fert_thresh=646)
    opp = load_elite_agent("V44")
    
    deltas = []
    rescues = 0
    casualties = 0
    
    for s in seeds:
        for seat in (0, 1):
            opp_seat = 1 - seat
            # Run V49
            sim49 = FastKagricultureSim(seed=s)
            obs49 = sim49.reset(seed=s)
            for _ in range(719):
                a49 = v49_mod.agent(obs49[seat])
                aopp = opp.act(obs49[opp_seat]) if hasattr(opp, "act") else opp(obs49[opp_seat])
                obs49, _, _, _ = sim49.step([a49, aopp] if seat == 0 else [aopp, a49])
            c49 = obs49[seat]["farms"][seat]["money"]
            copp49 = obs49[opp_seat]["farms"][opp_seat]["money"]
            w49 = c49 > copp49
            
            # Run V49 + Fert Guard
            sim_fg = FastKagricultureSim(seed=s)
            obs_fg = sim_fg.reset(seed=s)
            for _ in range(719):
                afg = fert_agent(obs_fg[seat])
                aopp = opp.act(obs_fg[opp_seat]) if hasattr(opp, "act") else opp(obs_fg[opp_seat])
                obs_fg, _, _, _ = sim_fg.step([afg, aopp] if seat == 0 else [aopp, afg])
            cfg = obs_fg[seat]["farms"][seat]["money"]
            copp_fg = obs_fg[opp_seat]["farms"][opp_seat]["money"]
            wfg = cfg > copp_fg
            
            delta = cfg - c49
            deltas.append(delta)
            if not w49 and wfg:
                rescues += 1
            if w49 and not wfg:
                casualties += 1
            if delta != 0:
                print(f"Seed {s} Seat {seat}: V49 Cash={c49}, FG Cash={cfg}, Delta={delta:+.1f} (w49={w49}, wfg={wfg})")
                
    import numpy as np
    print(f"\n--- Results on 32 legs ---")
    print(f"Mean Delta vs V49: {np.mean(deltas):+.2f}")
    print(f"Active legs: {sum(d != 0 for d in deltas)} / {len(deltas)}")
    print(f"Active Mean: {np.mean([d for d in deltas if d != 0]):+.2f}")
    print(f"Casualties: {casualties}, Rescues: {rescues}")
    print(f"Min Delta: {np.min(deltas):+.2f}")
