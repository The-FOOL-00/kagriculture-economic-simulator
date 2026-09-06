"""
Phases 5, 6, 7: Open-Loop Replay Opponent Matchup Diagnostic
Tests V2 and Candidate H against OPEN-LOOP REPLAY traces:
- Yuyajk (Phase 5)
- Gayathri (Phase 6)
- qihuaz (Phase 7)

Evaluates:
1. Historical seed
2. Unseen seeds (42, 100, 2026, 777, 999)
3. Both seats (P0 and P1) using standard env.run()
"""

import sys
import os
import json
import copy
from concurrent.futures import ThreadPoolExecutor

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from kaggle_environments import make
import candidates.slot2_aethel_refined_v2 as v2
from scratch.v2_jit_melon_experiment import agent_H_full_jit_pipeline

REPLAY_METADATA = {
    "Gayathri": {
        "file": "scratch/replays/V2_Loss_vs_GAYATHRI SALINI_104796498.json",
        "opp_seat_in_replay": 0,
        "v2_seat_in_replay": 1
    },
    "Yuyajk": {
        "file": "scratch/replays/V2_Loss_vs_Yuyajk_104810879.json",
        "opp_seat_in_replay": 1,
        "v2_seat_in_replay": 0
    },
    "qihuaz": {
        "file": "scratch/replays/V2_Loss_vs_qihuaz_104813423.json",
        "opp_seat_in_replay": 0,
        "v2_seat_in_replay": 1
    }
}

_CACHED_AGENTS = {}

def load_replay_actions(filepath, player_idx):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    steps = data["steps"]
    seed = data["info"]["seed"]
    actions = []
    for s in range(len(steps) - 1):
        act = copy.deepcopy(steps[s + 1][player_idx].get("action", {}))
        actions.append(act)
    while len(actions) < 720:
        actions.append({"farmer": ["PASS"], "hands": [], "market": []})
    return seed, actions

class OpenLoopAgent:
    def __init__(self, actions):
        self.actions = actions
    def __call__(self, obs, config=None):
        step = int(obs.get("step", 0) or 0)
        if step < len(self.actions):
            return copy.deepcopy(self.actions[step])
        return {"farmer": ["PASS"], "hands": [], "market": []}

for opp_name, meta in REPLAY_METADATA.items():
    seed, acts = load_replay_actions(meta["file"], meta["opp_seat_in_replay"])
    _CACHED_AGENTS[opp_name] = {"seed": seed, "agent": OpenLoopAgent(acts)}

def run_single_replay_match(args):
    opp_name, cand_type, seed, cand_seat = args
    cand_fn = agent_H_full_jit_pipeline if cand_type == "H" else v2.agent
    opp_fn = _CACHED_AGENTS[opp_name]["agent"]
    
    agent0 = cand_fn if cand_seat == 0 else opp_fn
    agent1 = opp_fn if cand_seat == 0 else cand_fn
    
    cand_p = cand_seat
    opp_p = 1 - cand_seat
    
    cfg = {"seed": seed, "episodeSteps": 720}
    env = make("kaggriculture", configuration=cfg)
    env.run([agent0, agent1])
    
    cand_reward = float(env.steps[-1][cand_p]["reward"] or 0)
    opp_reward = float(env.steps[-1][opp_p]["reward"] or 0)
    
    cash_264 = float(env.steps[264][cand_p]["observation"]["farms"][cand_p].get("money", 0)) if len(env.steps) > 264 else 0.0
    melon_price_264 = float(env.steps[264][0]["observation"].get("market", {}).get("prices", {}).get("MELON", 250)) if len(env.steps) > 264 else 250.0
    
    return {
        "opp_name": opp_name,
        "cand_type": cand_type,
        "seed": seed,
        "cand_seat": cand_seat,
        "cand_reward": cand_reward,
        "opp_reward": opp_reward,
        "cash_264": cash_264,
        "melon_price_264": melon_price_264
    }

def main():
    unseen_seeds = [42, 100, 2026, 777, 999]
    tasks = []
    
    # 1. Historical Seed matches
    for opp_name, meta in REPLAY_METADATA.items():
        hist_seed = _CACHED_AGENTS[opp_name]["seed"]
        hist_v2_seat = meta["v2_seat_in_replay"]
        tasks.append((opp_name, "V2", hist_seed, hist_v2_seat))
        tasks.append((opp_name, "H", hist_seed, hist_v2_seat))
        
    # 2. Unseen Seed matches
    for opp_name in REPLAY_METADATA.keys():
        for s in unseen_seeds:
            for seat in [0, 1]:
                tasks.append((opp_name, "V2", s, seat))
                tasks.append((opp_name, "H", s, seat))
                
    print(f"Executing {len(tasks)} replay matchup games with ThreadPoolExecutor...")
    with ThreadPoolExecutor(max_workers=6) as executor:
        results = list(executor.map(run_single_replay_match, tasks))
        
    # Organize results
    organized = {}
    for r in results:
        opp = r["opp_name"]
        cand = r["cand_type"]
        pair_key = (r["seed"], r["cand_seat"])
        if opp not in organized:
            organized[opp] = {"V2": {}, "H": {}}
        organized[opp][cand][pair_key] = r
        
    final_report = {}
    for opp_name, cands in organized.items():
        meta = REPLAY_METADATA[opp_name]
        hist_seed = _CACHED_AGENTS[opp_name]["seed"]
        hist_seat = meta["v2_seat_in_replay"]
        
        hist_v2 = cands["V2"][(hist_seed, hist_seat)]
        hist_h = cands["H"][(hist_seed, hist_seat)]
        hist_delta = hist_h["cand_reward"] - hist_v2["cand_reward"]
        
        print(f"\n==========================================")
        print(f"Results vs {opp_name} (OPEN_LOOP REPLAY)")
        print(f"==========================================")
        print(f"Historical Seed ({hist_seed}) [Seat P{hist_seat}]:")
        print(f"  V2: Score={hist_v2['cand_reward']}, Opp={hist_v2['opp_reward']}, Cash@264={hist_v2['cash_264']}, MelonP@264={hist_v2['melon_price_264']}")
        print(f"  H : Score={hist_h['cand_reward']}, Opp={hist_h['opp_reward']}, Cash@264={hist_h['cash_264']}, MelonP@264={hist_h['melon_price_264']}")
        print(f"  H - V2 Delta: {hist_delta:+.1f}")
        
        unseen_deltas = []
        unseen_records = []
        for s in unseen_seeds:
            for seat in [0, 1]:
                v2_m = cands["V2"][(s, seat)]
                h_m = cands["H"][(s, seat)]
                d = h_m["cand_reward"] - v2_m["cand_reward"]
                unseen_deltas.append(d)
                unseen_records.append({
                    "seed": s, "seat": seat,
                    "v2_reward": v2_m["cand_reward"], "h_reward": h_m["cand_reward"],
                    "delta": d, "h_cash264": h_m["cash_264"], "v2_cash264": v2_m["cash_264"],
                    "melon_price_264": h_m["melon_price_264"]
                })
                
        h_wins = sum(1 for d in unseen_deltas if d > 0)
        mean_d = sum(unseen_deltas) / len(unseen_deltas)
        print(f"Unseen Seeds (N={len(unseen_deltas)} games, both seats):")
        print(f"  Mean Delta: {mean_d:+.1f}")
        print(f"  Min Delta:  {min(unseen_deltas):+.1f}, Max Delta: {max(unseen_deltas):+.1f}")
        print(f"  H > V2 Rate: {h_wins}/{len(unseen_deltas)} ({h_wins/len(unseen_deltas)*100:.1f}%)")
        
        final_report[opp_name] = {
            "historical": {
                "seed": hist_seed, "seat": hist_seat,
                "v2": hist_v2, "h": hist_h, "delta": hist_delta
            },
            "unseen_summary": {
                "mean_delta": mean_d,
                "min_delta": min(unseen_deltas),
                "max_delta": max(unseen_deltas),
                "h_beats_v2_rate": h_wins / len(unseen_deltas)
            },
            "unseen_details": unseen_records
        }
        
    with open("scratch/jit_melon_results/phases5_6_7_replay_results.json", "w") as f:
        json.dump(final_report, f, indent=2)

if __name__ == "__main__":
    main()
