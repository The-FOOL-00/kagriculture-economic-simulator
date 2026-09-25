import sys
sys.path.insert(0, 'scripts')
from kaggle_environments import make
from v32_common import load_agent
from candidates.v32_hmeh.main import make_hmeh_agent

local_a7 = load_agent('E9_AST')
fn_a7 = lambda o, c=None: local_a7.act(o, c)
local_hmeh, hmeh_inst = make_hmeh_agent('HMEH-0')

def _act(obs, cfg=None):
    s = int(obs.get('step', 0) or 0)
    if s <= 24:
        return fn_a7(obs, cfg)
    return local_hmeh(obs, cfg)

opp_fn = load_agent('E0_V3')
env = make('kaggriculture', configuration={'seed': 249675, 'episodeSteps': 60})
env.run([_act, lambda o, c=None: opp_fn.act(o, c)])

for i in range(25, 45):
    act = env.steps[i][0]["action"]
    obs = env.steps[i][0]["observation"]
    money = obs["farms"][0]["money"]
    farmer = act.get("farmer")
    hands = act.get("hands")
    tiles = obs["farms"][0]["tiles"]
    unwatered = 0
    plants = 0
    for r in tiles:
        for t in r:
            if isinstance(t, dict) and t.get("kind") == "PLANT":
                plants += 1
                if not t.get("watered_today"):
                    unwatered += 1
    print(f"step {i:2d}: money={money:7.1f} farmer={farmer} hands={hands[:2]} plants={plants} unwatered={unwatered}")
