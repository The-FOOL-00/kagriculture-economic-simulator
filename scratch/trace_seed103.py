import os, sys, importlib.util
from kaggle_environments import make

def load(path):
    d = os.path.dirname(os.path.abspath(path))
    if d not in sys.path: sys.path.insert(0, d)
    spec = importlib.util.spec_from_file_location('mod_' + os.path.basename(path), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.agent

a54 = load('external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py')
a66 = load('external_repos/kaggriculture-v66-agent/main.py')

# Test Seed 103 with V66 in Seat 0 and V54 in Seat 1
env = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': 103})
env.reset()
for s in range(4):
    obs0 = env.state[0].observation
    obs1 = env.state[1].observation
    mkt = obs0.market
    w_sup = mkt['inventory'].get('WHEAT') if isinstance(mkt, dict) else mkt.inventory.get('WHEAT')
    w_prc = mkt['prices'].get('WHEAT') if isinstance(mkt, dict) else mkt.prices.get('WHEAT')
    print(f"Step {s} START:")
    f0 = obs0.farms[0] if isinstance(obs0.farms, list) else obs0.farms[0]
    f1 = obs1.farms[1] if isinstance(obs1.farms, list) else obs1.farms[1]
    m0 = f0.get('money') if isinstance(f0, dict) else f0.money
    m1 = f1.get('money') if isinstance(f1, dict) else f1.money
    h0 = len(f0.get('hands', [])) if isinstance(f0, dict) else len(f0.hands)
    h1 = len(f1.get('hands', [])) if isinstance(f1, dict) else len(f1.hands)
    print(f"  P0 (V66) Money: {m0}, Hands: {h0}")
    print(f"  P1 (V54) Money: {m1}, Hands: {h1}")
    print(f"  Market Wheat Supply: {w_sup}, Price: {w_prc}")
    act0 = a66(obs0, env.configuration)
    act1 = a54(obs1, env.configuration)
    print(f"  P0 (V66) Market: {act0.get('market')}")
    print(f"  P1 (V54) Market: {act1.get('market')}")
    env.step([act0, act1])
