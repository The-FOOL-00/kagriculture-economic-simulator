import sys
import os

REPO_ROOT = r"c:\Users\Sundareswaran\Kagriculture"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from research.v47.elite_benchmark.run_elite_benchmark import load_agent as load_elite_agent
import candidates.v49_meta_fusion.main as v49_mod
import candidates.v48_challenger.main as v48_mod

# Implement Per-Crop Exact Demand Cap on top of V48
def make_exact_crop_agent(seed_thresh=624):
    base_agent = v48_mod.agent
    chassis = v48_mod._IMPL.chassis
    cache = {}

    def get_need(route, step, crop):
        key = (route, step, crop)
        if key in cache:
            return cache[key]
        need = 0
        for t in range(step + 1, 719):
            tape = chassis.routes[2 if t >= 648 else route]
            act = tape[t]
            units = [act.get('farmer') or ['PASS']] + list(act.get('hands') or [])
            need += sum(1 for c in units if len(c) > 1 and c[0] == 'PLANT' and c[1] == crop)
        cache[key] = need
        return need

    def agent(obs, configuration=None):
        act = base_agent(obs, configuration)
        try:
            step = int(obs.get("step", 0) or 0)
            if step < seed_thresh:
                return act
            if not isinstance(act, dict):
                return act
            mkt = list(act.get("market") or [])
            if not any(len(o) >= 3 and o[0] == 'BUY_SEED' for o in mkt):
                return act
            seat = int(obs['player'])
            native = chassis.players[seat]
            route = native.get('route', 0)
            units = [act.get('farmer') or ['PASS']] + list(act.get('hands') or [])
            seeds = obs.get('private', {}).get('seeds', {}) or {}
            
            # Count available seeds right now
            avail = {}
            for crop in ('WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'MELON'):
                planted_now = sum(c[:2] == ['PLANT', crop] for c in units)
                avail[crop] = max(0, int(seeds.get(crop, 0)) - planted_now)
                
            out = []
            changed = False
            for o in mkt:
                if len(o) >= 3 and o[0] == 'BUY_SEED' and o[1] in avail:
                    crop = o[1]
                    qty = max(0, int(o[2]))
                    rem = get_need(route, step, crop)
                    # Pending queue plants
                    rem += sum(1 for queue in native.get('pending', {}).values() for pos, c in queue
                               if len(c) > 1 and c[0] == 'PLANT' and c[1] == crop)
                    keep = min(qty, max(0, rem - avail[crop]))
                    avail[crop] += keep
                    if keep < qty:
                        changed = True
                        o = [o[0], crop, keep] if keep else []
                if o:
                    out.append(o)
            if changed:
                act = dict(act)
                act['market'] = out[:10]
        except Exception:
            pass
        return act
    return agent

seed = 250416
sim_v49 = FastKagricultureSim(seed=seed)
obs_v49 = sim_v49.reset(seed=seed)
opp = load_elite_agent("V44")
for step in range(719):
    a = v49_mod.agent(obs_v49[0])
    ao = opp.act(obs_v49[1])
    obs_v49, _, _, _ = sim_v49.step([a, ao])
cash_v49 = obs_v49[0]["farms"][0]["money"]

sim_exact = FastKagricultureSim(seed=seed)
obs_exact = sim_exact.reset(seed=seed)
opp = load_elite_agent("V44")
exact_agent = make_exact_crop_agent(seed_thresh=624)
for step in range(719):
    a = exact_agent(obs_exact[0])
    ao = opp.act(obs_exact[1])
    obs_exact, _, _, _ = sim_exact.step([a, ao])
cash_exact = obs_exact[0]["farms"][0]["money"]

print(f"Seed {seed}:")
print(f"V49 Cash: {cash_v49}")
print(f"Exact Crop Cap Cash: {cash_exact}")
print(f"Delta: {cash_exact - cash_v49:+.1f}")
print("Final seeds V49:", {k: v for k, v in obs_v49[0]["private"]["seeds"].items() if v > 0})
print("Final seeds Exact:", {k: v for k, v in obs_exact[0]["private"]["seeds"].items() if v > 0})
