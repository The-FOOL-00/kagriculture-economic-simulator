import sys
sys.path.insert(0, 'scripts')
from kaggle_environments import make
from v32_common import load_agent

a7 = load_agent('E9_AST')
fn = lambda o, c=None: a7.act(o, c)
env = make('kaggriculture', configuration={'seed': 249675, 'episodeSteps': 720})
env.run([fn, load_agent('E0_V3')])

print("--- A7 EXACT 25 STEPS ---")
for i in range(1, 26):
    act = env.steps[i][0]["action"]
    obs = env.steps[i][0]["observation"]
    mkt = act.get("market")
    farmer = act.get("farmer")
    money = obs["farms"][0]["money"]
    shed = obs.get("private", {}).get("shed", {})
    seeds = obs.get("private", {}).get("seeds", {})
    print(f"step {i:2d}: money={money:7.1f} farmer={farmer} mkt={mkt} shed={shed} seeds={seeds}")
