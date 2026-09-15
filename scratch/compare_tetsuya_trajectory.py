import json

replay_path = "external_repos/lixingtao123-Kaggriculture/opponents/top1_tetsuya/replays/episode-104060611-replay.json"
with open(replay_path, "r") as f:
    d = json.load(f)

steps = [0, 72, 144, 216, 288, 360, 432, 504, 576, 648, 719]

print(f"{'Step':<6} | {'Tetsuya Money':<14} {'Hands':<6} {'Land':<6} | {'Zhyphirus Money':<16} {'Hands':<6} {'Land':<6}")
print("-" * 75)
for s in steps:
    obs0 = d['steps'][s][0]['observation']['farms'][0]
    obs1 = d['steps'][s][1]['observation']['farms'][1]
    m0, h0, l0 = obs0['money'], len(obs0['hands']), len(obs0['unlocked_quadrants'])
    m1, h1, l1 = obs1['money'], len(obs1['hands']), len(obs1['unlocked_quadrants'])
    print(f"{s:<6} | ${m0:<13,.0f} {h0:<6} {l0:<6} | ${m1:<15,.0f} {h1:<6} {l1:<6}")
