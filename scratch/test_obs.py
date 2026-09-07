import kaggle_environments
env = kaggle_environments.make("kaggriculture")
env.reset()
obs = env.state[0]["observation"]
print("Keys in obs:", list(obs.keys()))
for k in obs:
    if k not in ("farms", "market"):
        print(f"  {k}: {obs[k]}")
