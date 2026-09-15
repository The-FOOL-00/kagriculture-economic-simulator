import json
from collections import defaultdict

def print_episode_metrics(ep_id):
    path = f"replays/live_tournament/episode_{ep_id}.json"
    d = json.load(open(path))
    info = d.get("info", {})
    seed = info.get("seed") or d.get("configuration", {}).get("seed")
    teams = info.get("TeamNames", ["Player0", "Player1"])
    
    our_seat = 0 if "Eldritch" in teams[0] else 1
    opp_seat = 1 - our_seat
    
    steps = d["steps"]
    final_step = steps[-1]
    r_us = final_step[our_seat].get("reward", 0)
    r_opp = final_step[opp_seat].get("reward", 0)
    margin = r_us - r_opp
    
    shops = steps[min(576, len(steps)-1)][0]["observation"]["town"]["unlocked_shops"]
    
    print("=" * 110)
    print(f"EPISODE {ep_id}: Us ({teams[our_seat]}, P{our_seat}) vs Opp ({teams[opp_seat]}, P{opp_seat})")
    print(f"Seed: {seed} | Shops: {shops}")
    print(f"Final Outcome: Us: ${r_us:,.0f} | Opp: ${r_opp:,.0f} | Margin: ${margin:+,.0f}")
    print("=" * 110)
    
    days = [3, 6, 9, 10, 11, 12, 13, 14, 15, 18, 21, 24, 27, 30]
    print(f"{'Day':<4} | {'Step':<4} | {'Us Cash':<8} | {'Opp Cash':<8} | {'Margin':<8} | {'Us H':<4} | {'Opp H':<5} | {'Us Crops':<20} | {'Opp Crops':<20} | {'Us Ani':<14} | {'Opp Ani':<14}")
    print("-" * 115)
    
    for day in days:
        s = 719 if day == 30 else day * 24 + 12
        obs = steps[s][our_seat]["observation"]
        farms = obs["farms"]
        f_us = farms[our_seat]
        f_opp = farms[opp_seat]
        
        c0 = f_us["money"]
        c1 = f_opp["money"]
        m = c0 - c1
        h0 = len(f_us.get("hands", []))
        h1 = len(f_opp.get("hands", []))
        
        crops0 = defaultdict(int)
        crops1 = defaultdict(int)
        ani0 = defaultdict(int)
        ani1 = defaultdict(int)
        
        for r in f_us["tiles"]:
            for t in r:
                if isinstance(t, dict):
                    if t.get("kind") == "PLANT": crops0[t.get("crop")] += 1
                    elif t.get("kind") == "PASTURE": ani0[t.get("animal")] += 1
                    
        for r in f_opp["tiles"]:
            for t in r:
                if isinstance(t, dict):
                    if t.get("kind") == "PLANT": crops1[t.get("crop")] += 1
                    elif t.get("kind") == "PASTURE": ani1[t.get("animal")] += 1
                    
        str_c0 = ", ".join(f"{k}:{v}" for k, v in crops0.items())
        str_c1 = ", ".join(f"{k}:{v}" for k, v in crops1.items())
        str_a0 = ", ".join(f"{k}:{v}" for k, v in ani0.items() if k)
        str_a1 = ", ".join(f"{k}:{v}" for k, v in ani1.items() if k)
        
        print(f"D{day:<3} | {s:<4} | ${c0:6,.0f} | ${c1:6,.0f} | ${m:+7,.0f} | {h0:<4} | {h1:<5} | {str_c0[:20]:<20} | {str_c1[:20]:<20} | {str_a0[:14]:<14} | {str_a1[:14]:<14}")

if __name__ == "__main__":
    print_episode_metrics("107560807")
