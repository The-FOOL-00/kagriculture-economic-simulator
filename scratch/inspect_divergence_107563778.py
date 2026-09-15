import json

def inspect_day10_11_divergence(ep_id):
    path = f"replays/live_tournament/episode_{ep_id}.json"
    d = json.load(open(path))
    steps = d["steps"]
    
    print(f"=== DAY 10 to 12 DIVERGENCE AUDIT FOR EPISODE {ep_id} ===")
    
    for s in range(10 * 24, 12 * 24 + 6):
        obs0 = steps[s][0]["observation"]
        obs1 = steps[s][1]["observation"]
        f0 = obs0["farms"][0]
        f1 = obs1["farms"][1]
        c0, c1 = f0["money"], f1["money"]
        
        act0 = steps[s][0].get("action", {}) or {}
        act1 = steps[s][1].get("action", {}) or {}
        m0 = act0.get("market", [])
        m1 = act1.get("market", [])
        
        day = s // 24
        hour = s % 24
        
        if m0 or m1 or hour in (0, 1, 2, 10, 11, 12):
            print(f"D{day:2d} h{hour:02d} (step {s:3d}): Us Cash=${c0:6,.0f} | Opp Cash=${c1:6,.0f} | Margin=${c0-c1:+6,.0f}")
            if m0: print(f"    Us Mkt:  {m0}")
            if m1: print(f"    Opp Mkt: {m1}")

if __name__ == "__main__":
    inspect_day10_11_divergence("107563778")
