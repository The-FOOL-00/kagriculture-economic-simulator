import json

replay_path = "external_repos/lixingtao123-Kaggriculture/opponents/top1_tetsuya/replays/episode-104060611-replay.json"
with open(replay_path, "r") as f:
    d = json.load(f)

print("Steps sample:")
for s in [0, 1, 2, 5, 10, 24, 50, 72, 100, 144, 200, 216, 288, 300, 400, 500, 600, 700]:
    step_data = d["steps"][s]
    a0 = step_data[0].get("action") or {}
    f_act = a0.get("farmer")
    h_acts = a0.get("hands", [])
    m_acts = a0.get("market", [])
    obs0 = step_data[0].get("observation") or {}
    farm0 = obs0.get("farms", [{}])[0]
    priv0 = obs0.get("private") or {}
    print(f"Step {s:3d} | farmer: {str(f_act):<20} | num_hands_acts: {len(h_acts)} | market_acts: {len(m_acts)} | inv_count: {len(priv0.get('inventories', []))}")
    if m_acts:
        print(f"       Market: {m_acts}")
