import importlib.util
from kaggle_environments import make

def load_agent(p):
    spec = importlib.util.spec_from_file_location("mod", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, 'agent', getattr(mod, 'my_agent', None))

a0 = load_agent('agents/apex_synthesis_v3.py')
a1 = load_agent('agents/ground_truth_control_current_engine.py')

env = make('kaggriculture', configuration={'episodeSteps': 50, 'seed': 10000}, debug=True)
env.run([a0, a1])

print("P0 status:", env.state[0].status, "Reward:", env.state[0].reward)
print("P1 status:", env.state[1].status, "Reward:", env.state[1].reward)

# Print first 20 turns of actions
for t in range(min(20, len(env.steps))):
    print(f"Turn {t}: P0 action={env.steps[t][0].get('action')} | P1 action={env.steps[t][1].get('action')}")
