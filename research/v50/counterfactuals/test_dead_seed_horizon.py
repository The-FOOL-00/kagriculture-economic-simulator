import sys
import os

REPO_ROOT = r"c:\Users\Sundareswaran\Kagriculture"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from research.v47.elite_benchmark.run_elite_benchmark import load_agent as load_elite_agent
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v48_challenger.main as v48_mod

CROP_LATENCIES = {
    "WHEAT": 2,
    "CARROT": 2,
    "TOMATO": 8,
    "STRAWBERRY": 10,
    "MELON": 10,
}

# General Dead-Seed Guard: Suppress any BUY_SEED if (step // 24) + latency > 29
# OR if future remaining actionable plants <= current available seeds!
def make_dead_seed_guard_agent():
    base_agent = v49_mod.agent
    chassis = v49_mod._IMPL.chassis

    def agent(obs, configuration=None):
        act = base_agent(obs, configuration)
        try:
            step = int(obs.get("step", 0) or 0)
            if not isinstance(act, dict):
                return act
            mkt = list(act.get("market") or [])
            if not any(len(o) >= 3 and o[0] == 'BUY_SEED' for o in mkt):
                return act
            
            day = step // 24
            seeds = obs.get('private', {}).get('seeds', {}) or {}
            units = [act.get('farmer') or ['PASS']] + list(act.get('hands') or [])
            
            out = []
            changed = False
            for o in mkt:
                if len(o) >= 3 and o[0] == 'BUY_SEED':
                    crop = o[1]
                    lat = CROP_LATENCIES.get(crop, 2)
                    # 1. Horizon test: cannot mature before day 29
                    if day + lat > 29:
                        changed = True
                        o = []
                if o:
                    out.append(o)
            if changed:
                act = dict(act)
                act['market'] = out[:10]
        except Exception:
            pass
        return act
    return agent

seed = 250428
for seat in (0, 1):
    sim_v49 = FastKagricultureSim(seed=seed)
    obs_v49 = sim_v49.reset(seed=seed)
    opp = load_elite_agent("V44")
    for _ in range(719):
        a = v49_mod.agent(obs_v49[seat])
        ao = opp.act(obs_v49[1-seat])
        obs_v49, _, _, _ = sim_v49.step([a, ao] if seat == 0 else [ao, a])
    cash_v49 = obs_v49[seat]["farms"][seat]["money"]
    opp_v49 = obs_v49[1-seat]["farms"][1-seat]["money"]

    sim_ds = FastKagricultureSim(seed=seed)
    obs_ds = sim_ds.reset(seed=seed)
    opp = load_elite_agent("V44")
    ds_agent = make_dead_seed_guard_agent()
    for _ in range(719):
        a = ds_agent(obs_ds[seat])
        ao = opp.act(obs_ds[1-seat])
        obs_ds, _, _, _ = sim_ds.step([a, ao] if seat == 0 else [ao, a])
    cash_ds = obs_ds[seat]["farms"][seat]["money"]
    opp_ds = obs_ds[1-seat]["farms"][1-seat]["money"]

    print(f"Seed {seed} Seat {seat}:")
    print(f"  V49 Cash: {cash_v49:.0f} vs Opp: {opp_v49:.0f} (Margin: {cash_v49 - opp_v49:+.0f})")
    print(f"  DS  Cash: {cash_ds:.0f} vs Opp: {opp_ds:.0f} (Margin: {cash_ds - opp_ds:+.0f})")
    print(f"  Delta: {cash_ds - cash_v49:+.1f}")
    print(f"  Final seeds V49: {dict(obs_v49[seat]['private']['seeds'])}")
    print(f"  Final seeds DS:  {dict(obs_ds[seat]['private']['seeds'])}")
