import json

d = json.load(open("replays/live_tournament/episode_107543042.json"))
steps = d["steps"]
for s in [241, 242, 265, 266, 289]:
    c_before = steps[s-1][0]["observation"]["farms"][0]["money"]
    c_after = steps[s][0]["observation"]["farms"][0]["money"]
    act = steps[s][0].get("action", {})
    m = act.get("market", [])
    print(f"Step {s}: Before={c_before}, After={c_after}, Diff={c_after - c_before}")
    print(f"  Orders: {m}")
