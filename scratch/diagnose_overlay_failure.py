import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
import candidates.slot2_aethel_refined_v2 as v2_mod

# Minimal overlay that does NOT touch market queue unless money is actually < 0
def pure_v2_wrapper(obs, config=None):
    return v2_mod.agent(obs, config)

def overlay_market_only_pass(obs, config=None):
    act = v2_mod.agent(obs, config)
    # Don't touch market
    return act

env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42})
env.run([overlay_market_only_pass, "starter"])
print("Overlay (Exact Passthrough) Score:", env.steps[-1][0]["reward"])
