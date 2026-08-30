from kaggle_environments import make

def probe(obs, cfg):
    print("Market type:", type(obs["market"]))
    print("Market content:", obs["market"])
    print("Town type:", type(obs["town"]))
    print("Town content:", obs["town"])
    print("Farm 0 keys:", obs["farms"][0].keys())
    print("Private keys:", obs["private"].keys())
    return {"farmer": ["PASS"], "hands": []}

env = make("kaggriculture", configuration={"episodeSteps": 2, "seed": 42}, debug=True)
env.run([probe, probe])
