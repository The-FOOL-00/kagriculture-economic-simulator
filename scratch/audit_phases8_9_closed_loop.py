"""
Phases 8 & 9: Closed-Loop Adversarial & Top-Meta Benchmark
Evaluates V2 and Candidate H against genuinely closed-loop opponents:
- Live Flooder (opponents/live_flooder_v1.py) [200 matched games]
- Adversarial Champion Killer (opponents/adversarial_champion_killer.py) [100 matched games]
- Top-Meta O12 (opponents/o12_top_meta.py) [50 matched games]
- Aethel V1 (agents/candidate_a_aethel_v1.py) [50 matched games]
- V2 (candidates/slot2_aethel_refined_v2.py) [matched direct H2H]
"""

import sys
import os
import json
import numpy as np
from concurrent.futures import ProcessPoolExecutor

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from kaggle_environments import make
import candidates.slot2_aethel_refined_v2 as v2
import agents.candidate_a_aethel_v1 as v1
import opponents.live_flooder_v1 as lf
import opponents.adversarial_champion_killer as ack
import opponents.o12_top_meta as o12
from scratch.v2_jit_melon_experiment import agent_H_full_jit_pipeline

OPPONENT_FNS = {
    "live_flooder": lf.agent,
    "adversarial_champion_killer": ack.agent if hasattr(ack, "agent") else ack.OpponentBot().agent if hasattr(ack, "OpponentBot") else None,
    "o12_top_meta": o12.agent if hasattr(o12, "agent") else o12.OpponentBot().agent if hasattr(o12, "OpponentBot") else None,
    "v1": v1.agent,
    "v2": v2.agent
}

# Wrap class-based bots if needed
if OPPONENT_FNS["adversarial_champion_killer"] is None:
    def _ack_agent(obs, config=None):
        if not hasattr(_ack_agent, "bot"):
            _ack_agent.bot = ack.OpponentBot()
        if int(obs.get("step", 0) or 0) == 0:
            _ack_agent.bot = ack.OpponentBot()
        return _ack_agent.bot.step(obs)
    OPPONENT_FNS["adversarial_champion_killer"] = _ack_agent

if OPPONENT_FNS["o12_top_meta"] is None:
    def _o12_agent(obs, config=None):
        if not hasattr(_o12_agent, "bot"):
            _o12_agent.bot = o12.OpponentBot()
        if int(obs.get("step", 0) or 0) == 0:
            _o12_agent.bot = o12.OpponentBot()
        return _o12_agent.bot.step(obs)
    OPPONENT_FNS["o12_top_meta"] = _o12_agent

def robust(fn):
    def wrapped(obs, cfg=None):
        if obs.get("step") is None:
            obs["step"] = int(obs.get("day", 0) * 24 + obs.get("hour", 0))
        return fn(obs, cfg)
    return wrapped

def run_single_game(args):
    cand_key, opp_key, seed, cand_seat = args
    cand_fn = agent_H_full_jit_pipeline if cand_key == "H" else v2.agent
    opp_fn = OPPONENT_FNS[opp_key]
    
    agent0 = robust(cand_fn if cand_seat == 0 else opp_fn)
    agent1 = robust(opp_fn if cand_seat == 0 else cand_fn)
    
    cfg = {"seed": seed, "episodeSteps": 720}
    env = make("kaggriculture", configuration=cfg)
    env.run([agent0, agent1])
    
    cand_p = cand_seat
    opp_p = 1 - cand_seat
    
    r_cand = float(env.steps[-1][cand_p]["reward"] or 0)
    r_opp = float(env.steps[-1][opp_p]["reward"] or 0)
    margin = r_cand - r_opp
    win = 1.0 if r_cand > r_opp else (0.5 if r_cand == r_opp else 0.0)
    
    return {
        "cand_key": cand_key,
        "opp_key": opp_key,
        "seed": seed,
        "cand_seat": cand_seat,
        "r_cand": r_cand,
        "r_opp": r_opp,
        "margin": margin,
        "win": win
    }

def benchmark_suite():
    tasks = []
    
    # 1. Phase 8: 200 matched games vs Live Flooder (seeds 5000..5099, both seats = 200 games for V2, 200 games for H)
    lf_seeds = list(range(5000, 5100))
    for s in lf_seeds:
        for seat in [0, 1]:
            tasks.append(("V2", "live_flooder", s, seat))
            tasks.append(("H", "live_flooder", s, seat))
            
    # 2. Phase 9: Adversarial Champion Killer (seeds 5200..5249, both seats = 100 games each)
    ack_seeds = list(range(5200, 5250))
    for s in ack_seeds:
        for seat in [0, 1]:
            tasks.append(("V2", "adversarial_champion_killer", s, seat))
            tasks.append(("H", "adversarial_champion_killer", s, seat))
            
    # 3. Phase 9: O12 Top Meta (seeds 5300..5324, both seats = 50 games each)
    o12_seeds = list(range(5300, 5325))
    for s in o12_seeds:
        for seat in [0, 1]:
            tasks.append(("V2", "o12_top_meta", s, seat))
            tasks.append(("H", "o12_top_meta", s, seat))
            
    # 4. Phase 9: Aethel V1 (seeds 5400..5424, both seats = 50 games each)
    v1_seeds = list(range(5400, 5425))
    for s in v1_seeds:
        for seat in [0, 1]:
            tasks.append(("V2", "v1", s, seat))
            tasks.append(("H", "v1", s, seat))

    print(f"Total game executions scheduled: {len(tasks)}")
    
    with ProcessPoolExecutor(max_workers=6) as executor:
        results = list(executor.map(run_single_game, tasks))
        
    # Group results by opponent
    grouped = {}
    for r in results:
        opp = r["opp_key"]
        cand = r["cand_key"]
        pair_key = (r["seed"], r["cand_seat"])
        if opp not in grouped:
            grouped[opp] = {"V2": {}, "H": {}}
        grouped[opp][cand][pair_key] = r
        
    summary = {}
    for opp, cands in grouped.items():
        v2_games = cands["V2"]
        h_games = cands["H"]
        
        shared_keys = sorted(list(set(v2_games.keys()) & set(h_games.keys())))
        n = len(shared_keys)
        
        v2_margins = [v2_games[k]["margin"] for k in shared_keys]
        h_margins = [h_games[k]["margin"] for k in shared_keys]
        v2_rewards = [v2_games[k]["r_cand"] for k in shared_keys]
        h_rewards = [h_games[k]["r_cand"] for k in shared_keys]
        v2_wins = [v2_games[k]["win"] for k in shared_keys]
        h_wins = [h_games[k]["win"] for k in shared_keys]
        h_v2_deltas = [h_rewards[i] - v2_rewards[i] for i in range(n)]
        
        # P0 vs P1 seat breakdown
        p0_keys = [k for k in shared_keys if k[1] == 0]
        p1_keys = [k for k in shared_keys if k[1] == 1]
        
        p0_deltas = [h_games[k]["r_cand"] - v2_games[k]["r_cand"] for k in p0_keys]
        p1_deltas = [h_games[k]["r_cand"] - v2_games[k]["r_cand"] for k in p1_keys]
        
        summary[opp] = {
            "n_matched_games": n,
            "v2_win_rate": float(np.mean(v2_wins)),
            "h_win_rate": float(np.mean(h_wins)),
            "v2_mean_margin": float(np.mean(v2_margins)),
            "h_mean_margin": float(np.mean(h_margins)),
            "v2_mean_reward": float(np.mean(v2_rewards)),
            "h_mean_reward": float(np.mean(h_rewards)),
            "h_minus_v2_reward_delta": float(np.mean(h_v2_deltas)),
            "h_beats_v2_rate": float(np.mean([1 if d > 0 else 0 for d in h_v2_deltas])),
            "p0_reward_delta": float(np.mean(p0_deltas)) if p0_deltas else 0.0,
            "p1_reward_delta": float(np.mean(p1_deltas)) if p1_deltas else 0.0
        }
        
    print("\n--- PHASES 8 & 9 BENCHMARK SUMMARY ---")
    print(json.dumps(summary, indent=2))
    
    with open("scratch/jit_melon_results/phases8_9_closed_loop_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    benchmark_suite()
