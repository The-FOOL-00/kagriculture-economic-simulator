import sys, os, copy
sys.path.insert(0, os.path.abspath('.'))
from research.v40.env.fast_sim import FastKagricultureSim
import importlib.util

def load_from_source(src_text, name="temp_agent"):
    ns = {}
    exec(compile(src_text, name, "exec"), ns)
    return ns["agent"], ns

# Load v24 base source
with open('research/final_synthesis/teammates/v24/decoded_inner.py', 'r', encoding='utf-8') as f:
    v24_src = f.read()

# Load v27 base source
with open('research/final_synthesis/teammates/v27/decoded_inner.py', 'r', encoding='utf-8') as f:
    v27_src = f.read()

v24_agent, _ = load_from_source(v24_src, "v24")
v27_agent, _ = load_from_source(v27_src, "v27")

# Variant 1: v24 without PET tilt (remove pet_any_demand_agent wrapper at the end)
# The pet wrapper is lines 10146-10169
v24_no_pet_src = v24_src[:v24_src.rfind('_PET_PARENT=agent')]
v24_no_pet_agent, _ = load_from_source(v24_no_pet_src, "v24_no_pet")

# Variant 2: v24 without room_guard & dead_stock
v24_no_guards_src = v24_src.replace(
    "room_guard': True, 'clamp_sells': False, 'dead_stock': True",
    "room_guard': False, 'clamp_sells': False, 'dead_stock': False"
)
v24_no_guards_agent, _ = load_from_source(v24_no_guards_src, "v24_no_guards")

# Variant 3: v27 WITH pet_any_demand_agent
pet_wrapper = """
_PET_PARENT=agent
_PET_REPORT={'calls':0,'tilted':0,'errors':0}
def pet_any_demand_agent(observation,configuration=None):
    global _CA_MARGIN
    if int(observation.get('step',0))==0:_PET_REPORT.update(calls=0,tilted=0,errors=0)
    _PET_REPORT['calls']+=1;old=_CA_MARGIN
    try:
        day=int(observation.get('day',int(observation.get('step',0))//24))
        shops=list((observation.get('town') or {}).get('unlocked_shops') or [])
        if 10<=day<=23 and 'PET_CAFE' in shops:
            _CA_MARGIN=-30.0
            _PET_REPORT['tilted']+=1
        return _PET_PARENT(observation,configuration)
    except Exception:
        _PET_REPORT['errors']+=1;return _PET_PARENT(observation,configuration)
    finally:_CA_MARGIN=old
pet_any_demand_agent.telemetry=_PET_REPORT
agent=pet_any_demand_agent
kaggle_submission_agent=agent
"""
v27_with_pet_src = v27_src + pet_wrapper
v27_with_pet_agent, _ = load_from_source(v27_with_pet_src, "v27_with_pet")

variants = {
    "v24": v24_agent,
    "v27": v27_agent,
    "v24_no_pet": v24_no_pet_agent,
    "v24_no_guards": v24_no_guards_agent,
    "v27_with_pet": v27_with_pet_agent,
}

seeds = [250600, 250601, 250602, 250603]
results = {}

print("Running differential evaluations...")
for name, cand in variants.items():
    tot_cash = 0
    wins_vs_27 = 0
    tot_legs = 0
    for s in seeds:
        for seat in [0, 1]:
            sim = FastKagricultureSim(seed=s)
            obs = sim.reset(seed=s)
            for step in range(719):
                a0 = cand(obs[0]) if seat == 0 else v27_agent(obs[0])
                a1 = v27_agent(obs[1]) if seat == 0 else cand(obs[1])
                obs, r, done, info = sim.step([a0, a1])
            c_cand = float(obs[seat]['farms'][seat]['money'])
            c_opp = float(obs[1-seat]['farms'][1-seat]['money'])
            tot_cash += c_cand
            if c_cand > c_opp: wins_vs_27 += 1
            tot_legs += 1
    mean_cash = tot_cash / tot_legs
    results[name] = {"mean_cash": mean_cash, "wins_vs_27": wins_vs_27, "legs": tot_legs}
    print(f"Candidate {name:15s}: Mean Cash = {mean_cash:.1f}, Wins vs v27 = {wins_vs_27}/{tot_legs}")

print("\nSummary:")
for k, v in results.items():
    print(k, v)
