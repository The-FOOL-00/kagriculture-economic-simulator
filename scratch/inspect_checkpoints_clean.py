import json
from collections import defaultdict

def inspect_clean_all():
    ep_list = [
        ("107560807", "56145326"),
        ("107581148", "56149337"),
        ("107522150", "56141781"),
        ("107563778", "56145078"),
        ("107540087", "56147027"),
        ("107700784", "56157680")
    ]
    for ep_id, opp_name in ep_list:
        path = f"replays/live_tournament/episode_{ep_id}.json"
        d = json.load(open(path))
        info = d.get("info", {})
        seed = info.get("seed") or d.get("configuration", {}).get("seed")
        teams = info.get("TeamNames", ["Player0", "Player1"])
        print(f"\n" + "="*120)
        print(f"EPISODE {ep_id} vs {opp_name} | Seed: {seed} | Teams: {teams}")
        print("="*120)
    
        steps = d["steps"]
        shops = steps[576][0]["observation"]["town"]["unlocked_shops"]
        print(f"Unlocked Shops: {shops}")
        
        # We check at hour 12 of each day (midday) or step 719 for Day 30
        days = [3, 6, 9, 10, 11, 12, 13, 14, 15, 18, 21, 24, 27, 30]
        print(f"{'Day':<4} | {'Step':<4} | {'Us Cash':<8} | {'Opp Cash':<8} | {'Margin':<8} | {'Us H':<4} | {'Opp H':<5} | {'Us Land':<7} | {'Opp Land':<8} | {'Us Crops':<24} | {'Opp Crops':<24} | {'Us Animals':<16} | {'Opp Animals':<16}")
        print("-" * 145)
        
        for day in days:
            s = 719 if day == 30 else day * 24 + 12
            obs0 = steps[s][0]["observation"]
            obs1 = steps[s][1]["observation"]
            f0 = obs0["farms"][0]
            f1 = obs1["farms"][1]
            
            c0 = f0["money"]
            c1 = f1["money"]
            m = c0 - c1
            h0 = len(f0.get("hands", []))
            h1 = len(f1.get("hands", []))
            
            q0 = sum(1 for q in f0.get("unlocked_quadrants", []) if q)
            q1 = sum(1 for q in f1.get("unlocked_quadrants", []) if q)
            
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
            
            print(f"D{day:<3} | {s:<4} | ${c0:6,.0f} | ${c1:6,.0f} | ${m:+7,.0f} | {h0:<4} | {h1:<5} | {q0:<7} | {q1:<8} | {str_c0[:24]:<24} | {str_c1[:24]:<24} | {str_a0[:16]:<16} | {str_a1[:16]:<16}")

if __name__ == "__main__":
    inspect_clean_all()
