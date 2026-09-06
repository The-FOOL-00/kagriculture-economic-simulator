"""
Phase 11: Replay Opponent Diagnostic Test for Candidate C
Tests Candidate C against open-loop replays of:
- Gayathri Salini (Seed 1584709029, Seat 1)
- Yuyajk (Seed 1909883827, Seat 0)
- qihuaz (Seed 1256499628, Seat 1)
"""

import sys
import os
sys.path.insert(0, os.path.abspath("."))
import json
import copy
from kaggle_environments import make
import scratch.v2_jit_opening_closed_loop as cand_c

REPLAYS = {
    "Gayathri": {
        "file": "scratch/replays/V2_Loss_vs_GAYATHRI SALINI_104796498.json",
        "seed": 1584709029,
        "opp_seat": 1,
        "cand_seat": 0
    },
    "Yuyajk": {
        "file": "scratch/replays/V2_Loss_vs_Yuyajk_104810879.json",
        "seed": 1909883827,
        "opp_seat": 1,
        "cand_seat": 0
    },
    "qihuaz": {
        "file": "scratch/replays/V2_Loss_vs_qihuaz_104813423.json",
        "seed": 1256499628,
        "opp_seat": 0,
        "cand_seat": 1
    }
}

def make_replay_agent(raw_steps, opp_player):
    replay_actions = []
    for s in range(len(raw_steps) - 1):
        action = raw_steps[s + 1][opp_player].get("action")
        replay_actions.append(copy.deepcopy(action) if action is not None else {})
    while len(replay_actions) < 720:
        replay_actions.append({"farmer": ["PASS"], "hands": [], "market": []})
        
    def replay_agent(obs, config=None):
        step = obs.get("step")
        if step is None:
            step = int(obs.get("day", 0) * 24 + obs.get("hour", 0))
        else:
            step = int(step or 0)
        if step < len(replay_actions):
            return replay_actions[step]
        return {"farmer": ["PASS"], "hands": [], "market": []}
    return replay_agent

def robust(fn):
    def wrapped(obs, cfg=None):
        if obs.get("step") is None:
            obs["step"] = int(obs.get("day", 0) * 24 + obs.get("hour", 0))
        return fn(obs, cfg)
    return wrapped

def run_phase11():
    print("--- PHASE 11: REPLAY OPPONENTS DIAGNOSTIC TEST (Candidate C) ---")
    results = {}
    
    for name, meta in REPLAYS.items():
        with open(meta["file"], "r", encoding="utf-8") as f:
            d = json.load(f)
        opp_agent = make_replay_agent(d["steps"], meta["opp_seat"])
        
        cand_seat = meta["cand_seat"]
        opp_seat = meta["opp_seat"]
        
        agent0 = robust(cand_c.agent if cand_seat == 0 else opp_agent)
        agent1 = robust(opp_agent if cand_seat == 0 else cand_c.agent)
        
        env = make("kaggriculture", configuration={"seed": meta["seed"], "episodeSteps": 720})
        env.run([agent0, agent1])
        
        r_cand = float(env.steps[-1][cand_seat]["reward"] or 0)
        r_opp = float(env.steps[-1][opp_seat]["reward"] or 0)
        margin = r_cand - r_opp
        
        results[name] = {
            "seed": meta["seed"],
            "cand_seat": cand_seat,
            "r_cand": r_cand,
            "r_opp": r_opp,
            "margin": margin,
            "win": 1.0 if r_cand > r_opp else (0.5 if r_cand == r_opp else 0.0)
        }
        print(f"vs {name:10s} (Seed {meta['seed']}): Candidate C = {r_cand:8.1f} | Opponent Replay = {r_opp:8.1f} | Margin = {margin:+8.1f}")
        
    with open("scratch/jit_melon_results/phase11_replay_results.json", "w") as f:
        json.dump(results, f, indent=2)
        
    print("Saved Phase 11 replay results to scratch/jit_melon_results/phase11_replay_results.json")

if __name__ == "__main__":
    run_phase11()
