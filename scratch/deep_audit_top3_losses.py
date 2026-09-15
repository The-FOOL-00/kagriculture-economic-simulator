import json
import os
from collections import defaultdict

CHECKPOINT_DAYS = [3, 6, 9, 10, 11, 12, 13, 14, 15, 18, 21, 24, 27, 30]

def analyze_top3():
    episodes = [
        ("107543042", "56146971", "ORiginators (56120608)"),
        ("107564294", "56146971", "Les 2 oies (56149479)"),
        ("107582150", "56146947", "xxxxyt (56148830)"),
        ("107560807", "56146947", "56145326"),
        ("107581148", "56146971", "56149337"),
        ("107522150", "56146971", "56141781")
    ]
    
    for ep_id, our_sub, opp_desc in episodes:
        path = f"replays/live_tournament/episode_{ep_id}.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        info = data.get("info", {})
        seed = info.get("seed") or data.get("configuration", {}).get("seed")
        teams = info.get("TeamNames", ["Player0", "Player1"])
        
        our_seat = 0 if "Eldritch" in teams[0] else 1
        opp_seat = 1 - our_seat
        
        steps = data.get("steps", [])
        final_step = steps[-1]
        r_us = final_step[our_seat].get("reward", 0)
        r_opp = final_step[opp_seat].get("reward", 0)
        margin = r_us - r_opp
        
        # Shops
        shops = []
        for s_idx in [72, 144, 216, 288, 360, 432, 504, 576]:
            if s_idx < len(steps):
                obs = steps[s_idx][0].get("observation", {})
                town_shops = obs.get("town", {}).get("unlocked_shops", [])
                if town_shops:
                    shops = town_shops
                    
        print("\n" + "="*110)
        print(f"EPISODE {ep_id}: Our Sub {our_sub} ({teams[our_seat]}, P{our_seat}) vs {opp_desc} ({teams[opp_seat]}, P{opp_seat})")
        print(f"Seed: {seed} | Shops: {shops}")
        print(f"Final Rewards -> Us: ${r_us:,.0f} | Opponent: ${r_opp:,.0f} | Margin: ${margin:+,.0f}")
        print("="*110)
        
        print(f"{'Day':<4} | {'Step':<4} | {'Our Cash':<9} | {'Opp Cash':<9} | {'Margin':<9} | {'Our H':<5} | {'Opp H':<5} | {'Our Land':<8} | {'Opp Land':<8} | {'Our Animals':<15} | {'Opp Animals':<15}")
        print("-" * 110)
        
        for day in CHECKPOINT_DAYS:
            step_idx = min(day * 24 if day < 30 else 719, len(steps) - 1)
            obs = steps[step_idx][0].get("observation", {})
            farms = obs.get("farms", [{}, {}])
            
            f_us = farms[our_seat]
            f_opp = farms[opp_seat]
            
            c_us = f_us.get("money", 0)
            c_opp = f_opp.get("money", 0)
            m = c_us - c_opp
            
            h_us = len(f_us.get("units", []))
            h_opp = len(f_opp.get("units", []))
            
            q_us = sum(1 for q in f_us.get("unlocked_quadrants", []) if q)
            q_opp = sum(1 for q in f_opp.get("unlocked_quadrants", []) if q)
            
            ani_us = defaultdict(int)
            for row in f_us.get("tiles", []):
                for t in row:
                    if isinstance(t, dict) and t.get("kind") == "PASTURE":
                        ani_us[t.get("animal")] += 1
                        
            ani_opp = defaultdict(int)
            for row in f_opp.get("tiles", []):
                for t in row:
                    if isinstance(t, dict) and t.get("kind") == "PASTURE":
                        ani_opp[t.get("animal")] += 1
                        
            str_ani_us = ", ".join(f"{k}:{v}" for k, v in ani_us.items() if k) or "None"
            str_ani_opp = ", ".join(f"{k}:{v}" for k, v in ani_opp.items() if k) or "None"
            
            print(f"D{day:<3} | {step_idx:<4} | ${c_us:7,.0f} | ${c_opp:7,.0f} | ${m:+7,.0f} | {h_us:<5} | {h_opp:<5} | {q_us:<8} | {q_opp:<8} | {str_ani_us:<15} | {str_ani_opp:<15}")

        # Cash runway analysis around Day 8-15
        print("\n--- DETAILED HOURLY CASH RUNWAY (Days 9 to 13) ---")
        for s in range(9 * 24, 14 * 24):
            obs = steps[s][0].get("observation", {})
            farms = obs.get("farms", [{}, {}])
            c_us = farms[our_seat].get("money", 0)
            c_opp = farms[opp_seat].get("money", 0)
            d = s // 24
            h = s % 24
            
            act_us = steps[s][our_seat].get("action", {}) or {}
            m_us = act_us.get("market", [])
            
            act_opp = steps[s][opp_seat].get("action", {}) or {}
            m_opp = act_opp.get("market", [])
            
            # Print if cash is low or market orders occurred
            if c_us < 2000 or m_us or m_opp or h == 0:
                print(f"  Day {d:2d} h{h:2d} (step {s:3d}): Us Cash=${c_us:6,.0f} | Opp Cash=${c_opp:6,.0f} | Us Mkt: {m_us} | Opp Mkt: {m_opp}")

if __name__ == "__main__":
    analyze_top3()
