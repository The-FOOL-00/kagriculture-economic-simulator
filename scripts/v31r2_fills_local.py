"""V31R2 diagnosis: exact SELL fills + revenue via engine instrumentation.

Runs ONE A7-vs-A7 match on an already-consumed dev seed (249591, E1 range)
with _commit_unit wrapped. No virgin seeds touched. Diagnostic only.
"""
import os
import sys
from collections import Counter

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

from aec.backbone.v27_ablation_adapters import V27AblationAdapter  # noqa: E402
from kaggle_environments import make  # noqa: E402
import kaggle_environments.envs.kaggriculture.kaggriculture as K  # noqa: E402

fills = [Counter(), Counter()]
rev = [0.0, 0.0]
units_at_px1 = [0, 0]
orig = K._commit_unit


def wrapped(op, item, price, farm, private, market, shed_capacity=100):
    ok = orig(op, item, price, farm, private, market, shed_capacity)
    if ok and op == "SELL":
        # attribute by matching farm object identity is unavailable; use money delta side-channel instead
        pass
    return ok


# Attribute via per-player money tracking: wrap at _process_market level instead.
orig_pm = K._process_market


def pm_wrap(state, env):
    for j in (0, 1):
        farm_id[id(state[0].observation.farms[j])] = j
    return orig_pm(state, env)


K._process_market = pm_wrap


K._commit_unit = wrapped

# Per-player fill counting: patch _commit_unit with player id via farms identity map
fills = [Counter(), Counter()]
rev = [0.0, 0.0]
px1 = [0, 0]
farm_id = {}


def counting_commit(op, item, price, farm, private, market, shed_capacity=100):
    ok = orig(op, item, price, farm, private, market, shed_capacity)
    if ok and op == "SELL":
        pid = farm_id.get(id(farm), -1)
        if pid >= 0:
            fills[pid][item] += 1
            rev[pid] += price
            if price <= 1:
                px1[pid] += 1
    return ok


K._commit_unit = counting_commit

a = V27AblationAdapter(variant="V27-ABL-A7")
b = V27AblationAdapter(variant="V27-ABL-A7")
env = make("kaggriculture", configuration={"seed": 249591})
# map farm ids after init: poke via a dry reset
env.reset()
for i, s in enumerate(env.state):
    farm_id[id(s.observation.farms[i])] = i
env.run([lambda o, c=None: a.act(o, c), lambda o, c=None: b.act(o, c)])
for i in (0, 1):
    tot = sum(fills[i].values())
    print(f"seat{i}: fills={tot} rev={rev[i]:.0f} px1_units={px1[i]} ({px1[i]/max(tot,1)*100:.0f}%)")
    print(f"  by prod: {dict(fills[i])}")
    print(f"  final money: {env.steps[-1][i]['reward']:.0f}")
