import json
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates"))

import kagsim
import router_parent as mod_r
import compiled_v54_plus_residual as v54

def compare_agents_against_opponent(ep_id):
    path = f"replays/live_tournament/episode_{ep_id}.json"
    d = json.load(open(path))
    info = d.get("info", {})
    seed = int(info.get("seed") or d.get("configuration", {}).get("seed"))
    teams = info.get("TeamNames", ["Player0", "Player1"])
    
    our_seat = 0 if "Eldritch" in teams[0] else 1
    opp_seat = 1 - our_seat
    
    replay_steps = d["steps"]
    official_r_us = replay_steps[-1][our_seat].get("reward", 0)
    official_r_opp = replay_steps[-1][opp_seat].get("reward", 0)
    
    print("\n" + "="*90)
    print(f"EPISODE {ep_id} (Seed {seed}) vs {teams[opp_seat]} (Official Us=${official_r_us:,.0f} vs Opp=${official_r_opp:,.0f})")
    print("="*90)
    
    # 1. V54++ Residual vs Recorded Opponent
    g_v54 = kagsim.Game(seed)
    for s in range(len(replay_steps) - 1):
        opp_act = replay_steps[s][opp_seat].get("action") or {}
        obs_us = g_v54.observe(our_seat)
        our_act = v54.agent(obs_us)
        if our_seat == 0:
            g_v54.step(our_act, opp_act)
        else:
            g_v54.step(opp_act, our_act)
            
    v54_us = g_v54.reward(our_seat)
    v54_opp = g_v54.reward(opp_seat)
    print(f"  V54++ Residual vs Recorded Opponent -> Us: ${v54_us:,.0f} | Opp: ${v54_opp:,.0f} | Margin: ${v54_us - v54_opp:+,.0f}")
    
    # 2. Dmitrii Base vs Recorded Opponent
    g_dm = kagsim.Game(seed)
    p = mod_r.Policy("extracted_agents/dmitrii_lb2800")
    for s in range(len(replay_steps) - 1):
        opp_act = replay_steps[s][opp_seat].get("action") or {}
        obs_us = g_dm.observe(our_seat)
        our_act = p.act(obs_us)
        if our_seat == 0:
            g_dm.step(our_act, opp_act)
        else:
            g_dm.step(opp_act, our_act)
            
    dm_us = g_dm.reward(our_seat)
    dm_opp = g_dm.reward(opp_seat)
    print(f"  Dmitrii Base   vs Recorded Opponent -> Us: ${dm_us:,.0f} | Opp: ${dm_opp:,.0f} | Margin: ${dm_us - dm_opp:+,.0f}")

if __name__ == "__main__":
    for ep in ["107543042", "107560807", "107563778", "107581148"]:
        compare_agents_against_opponent(ep)
