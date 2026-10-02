import sys, os, copy
sys.path.insert(0, os.path.abspath('.'))
from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49_mod

# 1. Load V24
with open('research/final_synthesis/teammates/v24/decoded_inner.py', 'r', encoding='utf-8') as f:
    v24_src = f.read()

# Remove the debug print in line 7156: print('HP_TELEMETRY',_HP_STATS)
v24_src_clean = v24_src.replace("print('HP_TELEMETRY',_HP_STATS)", "pass")

ns24 = {}
exec(compile(v24_src_clean, "v24_clean", "exec"), ns24)
v24_agent = ns24["agent"]

# 2. V24 + V49 E402 Late Seed Cap
# Let's inspect how E402 works on v24
v24_chassis = ns24['_IMPL'].chassis

v49_e402_cache = {}
def v49_e402_remaining(native, step, chassis):
    route = native.get('route', 0)
    key = (route, step)
    if key in v49_e402_cache:
        return v49_e402_cache[key]
    need = 0
    for t in range(step + 1, 719):
        tape = chassis.routes[2 if t >= 648 else route]
        act = tape[t]
        need += sum(1 for c in [act.get('farmer') or ['PASS']] + list(act.get('hands') or [])
                    if len(c) > 1 and c[0] == 'PLANT' and c[1] in ('WHEAT', 'CARROT'))
    v49_e402_cache[key] = need
    return need

def make_e402_overlay(base_agent, chassis):
    def e402_agent(observation, configuration=None):
        act = base_agent(observation, configuration)
        try:
            step = int(observation.get("step", 0) or 0)
            if step == 0:
                v49_e402_cache.clear()
            if step < 624:
                return act
            if not isinstance(act, dict):
                return act
            mkt = list(act.get("market") or [])
            if not any(len(o) >= 3 and o[0] == 'BUY_SEED' and o[1] in ('WHEAT', 'CARROT') for o in mkt):
                return act
            seat = int(observation['player'])
            native = chassis.players[seat]
            remaining = v49_e402_remaining(native, step, chassis)
            remaining += sum(1 for queue in native.get('pending', {}).values() for pos, c in queue
                             if len(c) > 1 and c[0] == 'PLANT' and c[1] in ('WHEAT', 'CARROT'))
            units = [act.get('farmer') or ['PASS']] + list(act.get('hands') or [])
            seeds = observation.get('private', {}).get('seeds', {}) or {}
            available = {p: max(0, int(seeds.get(p, 0)) - sum(c[:2] == ['PLANT', p] for c in units)) for p in ('WHEAT', 'CARROT')}
            out = []
            changed = False
            for o in mkt:
                if len(o) >= 3 and o[0] == 'BUY_SEED' and o[1] in available:
                    p = o[1]
                    qty = max(0, int(o[2]))
                    keep = min(qty, max(0, remaining - available[p]))
                    available[p] += keep
                    if keep < qty:
                        changed = True
                        o = [o[0], p, keep] if keep else []
                out.append(o)
            if changed:
                act["market"] = [o for o in out if o][:10]
        except Exception:
            pass
        return act
    return e402_agent

v24_e402_agent = make_e402_overlay(v24_agent, v24_chassis)

# 3. V24 + V44 CapEx cutoff (step >= 520)
def make_capex_overlay(base_agent):
    def capex_agent(observation, configuration=None):
        act = base_agent(observation, configuration)
        try:
            step = int(observation.get("step", 0) or 0)
            if not isinstance(act, dict):
                return act
            mkt = list(act.get("market") or [])
            if step >= 520:
                mkt = [o for o in mkt if not (len(o) > 0 and o[0] in ("BUY_ANIMAL", "BUY_LAND"))]
            act["market"] = mkt[:10]
        except Exception:
            pass
        return act
    return capex_agent

v24_capex_agent = make_capex_overlay(v24_agent)
v24_e402_capex_agent = make_capex_overlay(v24_e402_agent)

# Test candidates against V49 control on seeds 250600..250603 (8 legs)
candidates = {
    "V49_baseline": v49_mod.agent,
    "V24_clean": v24_agent,
    "V24_plus_E402": v24_e402_agent,
    "V24_plus_CapEx520": v24_capex_agent,
    "V24_plus_E402_CapEx520": v24_e402_capex_agent,
}

seeds = [250600, 250601, 250602, 250603]
control_agent = v49_mod.agent

print(f"{'Candidate':25s} | {'Mean Cash':10s} | {'Mean Opp Cash':14s} | {'Diff':9s} | {'Wins':8s}")
print("-" * 75)

for c_name, c_agent in candidates.items():
    tot_cash = 0
    tot_opp_cash = 0
    wins = 0
    legs = 0
    for s in seeds:
        for seat in [0, 1]:
            sim = FastKagricultureSim(seed=s)
            obs = sim.reset(seed=s)
            for step in range(719):
                a0 = c_agent(obs[0]) if seat == 0 else control_agent(obs[0])
                a1 = control_agent(obs[1]) if seat == 0 else c_agent(obs[1])
                obs, r, done, info = sim.step([a0, a1])
            cc = float(obs[seat]['farms'][seat]['money'])
            co = float(obs[1-seat]['farms'][1-seat]['money'])
            tot_cash += cc
            tot_opp_cash += co
            if cc > co: wins += 1
            legs += 1
    mean_c = tot_cash / legs
    mean_o = tot_opp_cash / legs
    diff = mean_c - mean_o
    print(f"{c_name:25s} | {mean_c:10.1f} | {mean_o:14.1f} | {diff:+9.1f} | {wins}/{legs}")
