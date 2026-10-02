import sys, os
sys.path.insert(0, os.path.abspath('.'))
from research.v40.env.fast_sim import FastKagricultureSim

with open('research/final_synthesis/teammates/v24/decoded_inner.py', 'r', encoding='utf-8') as f:
    v24_src = f.read()

v24_clean_src = v24_src.replace("print('HP_TELEMETRY',_HP_STATS)", "pass")
ns_base = {}
exec(compile(v24_clean_src, 'v24_base', 'exec'), ns_base)
base_agent = ns_base['agent']

# Build v24 with V48 overrides
v24_v48_src = v24_clean_src.replace(
    "def _router(observation,step,state):",
    """_V48_OVERRIDES = {
    ('BRUNCH_SPOT', 'FARMERS_MARKET'): 105,
    ('BAKERY', 'BRUNCH_SPOT'): 105,
    ('PET_CAFE', 'FARMERS_MARKET'): 105,
}
def _router(observation,step,state):"""
).replace(
    "if step>=144 and not state.get('day6'):",
    """if step>=144 and not state.get('day6'):
        shops_check = tuple((_get(_get(observation,'town',{}),'unlocked_shops',[]) or [])[:2])
        if shops_check in _V48_OVERRIDES:
            state['expert'] = 'EXP240'
            state['route'] = _V48_OVERRIDES[shops_check]
            state['day6'] = True
            return state.get('route', 0)
    """
)

ns_v48 = {}
exec(compile(v24_v48_src, 'v24_v48', 'exec'), ns_v48)
v48_agent = ns_v48['agent']

seeds = [250607, 250632, 250657, 250671, 250681, 250698]
print('Testing V24 vs V24+V48_OVERRIDES on 6 override seeds (12 legs)...')
base_cash = 0
v48_cash = 0
base_wins = 0
v48_wins = 0
tot = 0

for s in seeds:
    for seat in [0, 1]:
        sim = FastKagricultureSim(seed=s)
        obs = sim.reset(seed=s)
        for step in range(719):
            a0 = base_agent(obs[0]) if seat == 0 else v48_agent(obs[0])
            a1 = v48_agent(obs[1]) if seat == 0 else base_agent(obs[1])
            obs, r, done, info = sim.step([a0, a1])
        c_base = float(obs[seat]['farms'][seat]['money'])
        c_v48 = float(obs[1-seat]['farms'][1-seat]['money'])
        base_cash += c_base
        v48_cash += c_v48
        if c_base > c_v48: base_wins += 1
        elif c_v48 > c_base: v48_wins += 1
        tot += 1
        print(f'Seed {s} Seat {seat}: base={c_base:.1f} v48={c_v48:.1f} diff={c_v48 - c_base:+.1f}')

print(f'Summary: Base Mean={base_cash/tot:.1f}, V48 Mean={v48_cash/tot:.1f}, Diff={(v48_cash-base_cash)/tot:+.1f}, V48 Wins={v48_wins}/{tot}, Base Wins={base_wins}/{tot}')
