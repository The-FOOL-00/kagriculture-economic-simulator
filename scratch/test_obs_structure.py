from kaggle_environments import make

env = make("kaggriculture", configuration={"episodeSteps": 10, "seed": 42}, debug=True)
env.reset()
obs0 = env.state[0].observation
obs1 = env.state[1].observation

print("=== RAW STATE[0] & STATE[1] AFTER RESET ===")
print("type(obs0):", type(obs0), "obs0.step:", getattr(obs0, "step", None))
print("type(obs1):", type(obs1), "obs1.step:", getattr(obs1, "step", None))
print("'step' in obs1 keys:", "step" in obs1 if isinstance(obs1, dict) else hasattr(obs1, "step"))
print("obs1.get('step', 999):", obs1.get("step", 999) if isinstance(obs1, dict) else getattr(obs1, "step", 999))

env.step([{}, {}])
obs0 = env.state[0].observation
obs1 = env.state[1].observation
print("\n=== RAW STATE[0] & STATE[1] AFTER 1 STEP ===")
print("obs0.step:", getattr(obs0, "step", None))
print("obs1.step:", getattr(obs1, "step", None))
print("obs1.get('step', 999):", obs1.get("step", 999) if isinstance(obs1, dict) else getattr(obs1, "step", 999))
print("obs1.get('step') or (day*24+hour):", (obs1.get("step") if isinstance(obs1, dict) else getattr(obs1, "step", None)) or (obs1.day * 24 + obs1.hour))

# Now let's test what an agent receives via env.run() vs runner.act()
received_in_agent_p0 = []
received_in_agent_p1 = []

def a0(obs, cfg):
    received_in_agent_p0.append(obs.get("step"))
    return {}

def a1(obs, cfg):
    received_in_agent_p1.append(obs.get("step"))
    return {}

env2 = make("kaggriculture", configuration={"episodeSteps": 10, "seed": 42}, debug=True)
env2.run([a0, a1])

print("\n=== INSIDE AGENT FUNCTION (via env.run) ===")
print("P0 received steps:", received_in_agent_p0)
print("P1 received steps:", received_in_agent_p1)
