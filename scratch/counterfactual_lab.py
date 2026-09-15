import json
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))

import kagsim
import router_parent as mod_r

def test_replay_mirror(ep_id):
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
    
    print(f"\nEpisode {ep_id} (Seed {seed}): Official Us=${official_r_us:,.0f} vs Opp=${official_r_opp:,.0f} (Margin: ${official_r_us - official_r_opp:+,.0f})")
    
    # 1. Verify Bit-Exact Replay in kagsim using replay action stream
    g = kagsim.Game(seed)
    for s in range(len(replay_steps) - 1):
        act0 = replay_steps[s][0].get("action") or {}
        act1 = replay_steps[s][1].get("action") or {}
        g.step(act0, act1)
        
    sim_r0 = g.reward(0)
    sim_r1 = g.reward(1)
    sim_us = sim_r0 if our_seat == 0 else sim_r1
    sim_opp = sim_r1 if our_seat == 0 else sim_r0
    print(f"  kagsim Replay Mirror -> Us: ${sim_us:,.0f} | Opp: ${sim_opp:,.0f} | Diff from Official: ${sim_us - official_r_us:,.0f}")
    
    # 2. Run Dmitrii Router against the Recorded Opponent Stream
    g_dmitrii = kagsim.Game(seed)
    p = mod_r.Policy("extracted_agents/dmitrii_lb2800")
    for s in range(len(replay_steps) - 1):
        opp_act = replay_steps[s][opp_seat].get("action") or {}
        obs_us = g_dmitrii.observe(our_seat)
        our_act = p.act(obs_us)
        if our_seat == 0:
            g_dmitrii.step(our_act, opp_act)
        else:
            g_dmitrii.step(opp_act, our_act)
            
    dm_us = g_dmitrii.reward(our_seat)
    dm_opp = g_dmitrii.reward(opp_seat)
    print(f"  Dmitrii Base vs Recorded Opponent -> Us: ${dm_us:,.0f} | Opp: ${dm_opp:,.0f} | Margin: ${dm_us - dm_opp:+,.0f}")

if __name__ == "__main__":
    for ep in ["107543042", "107560807", "107563778"]:
        test_replay_mirror(ep)
