import json
from collections import defaultdict

def inspect_worst():
    d = json.load(open("replays/live_tournament/episode_107543042.json"))
    info = d.get("info", {})
    seed = info.get("seed") or d.get("configuration", {}).get("seed")
    print(f"Episode: 107543042 | Seed: {seed} | Teams: {info.get('TeamNames')}")
    
    steps = d["steps"]
    shops = steps[576][0]["observation"]["town"]["unlocked_shops"]
    print(f"Unlocked Shops: {shops}")
    
    checkpoints = [72, 144, 216, 240, 264, 288, 312, 336, 360, 432, 504, 576, 648, 719]
    print("\nCHECKPOINT PROGRESSION:")
    print(f"{'Day':<4} | {'Step':<4} | {'Us Cash':<8} | {'Opp Cash':<8} | {'Margin':<8} | {'Us H':<4} | {'Opp H':<5} | {'Us Crops':<22} | {'Opp Crops':<22} | {'Us Animals':<16} | {'Opp Animals':<16}")
    print("-" * 125)
    
    for s in checkpoints:
        day = s // 24
        obs0 = steps[s][0]["observation"]
        obs1 = steps[s][1]["observation"]
        f0 = obs0["farms"][0]
        f1 = obs1["farms"][1]
        
        c0 = f0["money"]
        c1 = f1["money"]
        m = c0 - c1
        h0 = len(f0.get("hands", []))
        h1 = len(f1.get("hands", []))
        
        crops0 = defaultdict(int)
        crops1 = defaultdict(int)
        ani0 = defaultdict(int)
        ani1 = defaultdict(int)
        
        for r in f0["tiles"]:
            for t in r:
                if isinstance(t, dict):
                    if t.get("kind") == "PLANT": crops0[t.get("crop")] += 1
                    elif t.get("kind") == "PASTURE": ani0[t.get("animal")] += 1
                    
        for r in f1["tiles"]:
            for t in r:
                if isinstance(t, dict):
                    if t.get("kind") == "PLANT": crops1[t.get("crop")] += 1
                    elif t.get("kind") == "PASTURE": ani1[t.get("animal")] += 1
                    
        str_c0 = ", ".join(f"{k}:{v}" for k, v in crops0.items())
        str_c1 = ", ".join(f"{k}:{v}" for k, v in crops1.items())
        str_a0 = ", ".join(f"{k}:{v}" for k, v in ani0.items())
        str_a1 = ", ".join(f"{k}:{v}" for k, v in ani1.items())
        
        print(f"D{day:<3} | {s:<4} | ${c0:6,.0f} | ${c1:6,.0f} | ${m:+7,.0f} | {h0:<4} | {h1:<5} | {str_c0[:22]:<22} | {str_c1[:22]:<22} | {str_a0[:16]:<16} | {str_a1[:16]:<16}")
        
    print("\n--- TURN-BY-TURN TELEMETRY DAYS 8 TO 14 ---")
    for s in range(8 * 24, 14 * 24):
        obs0 = steps[s][0]["observation"]
        obs1 = steps[s][1]["observation"]
        f0 = obs0["farms"][0]
        f1 = obs1["farms"][1]
        c0 = f0["money"]
        c1 = f1["money"]
        
        act0 = steps[s][0].get("action", {}) or {}
        act1 = steps[s][1].get("action", {}) or {}
        m0 = act0.get("market", [])
        m1 = act1.get("market", [])
        
        day = s // 24
        hour = s % 24
        
        # Check if cash dropped sharply or hiring occurred
        if s % 24 in (0, 1, 2) or c0 < 1000 or m0 or m1:
            print(f"D{day:2d} h{hour:2d} (step {s:3d}): Us=${c0:6,.0f}, Opp=${c1:6,.0f} | Us Mkt: {m0} | Opp Mkt: {m1}")

if __name__ == "__main__":
    inspect_worst()
