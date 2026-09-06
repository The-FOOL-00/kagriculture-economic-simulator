"""
Phases 10, 11, 12: Benchmark Candidate C (Closed-Loop JIT + V2 handoff)
Evaluates:
- Phase 10: Matched development games vs Frozen V2 (50 seeds, both seats = 100 games)
- Phase 11: Open-loop replay opponents (Gayathri, Yuyajk, qihuaz)
- Phase 12: Closed-loop meta opponents (Live Flooder, ACK, O12, Aethel V1)
"""

import sys
import os
sys.path.insert(0, os.path.abspath("."))
import json
import numpy as np
from concurrent.futures import ProcessPoolExecutor
from kaggle_environments import make

import candidates.slot2_aethel_refined_v2 as v2
import agents.candidate_a_aethel_v1 as v1
import opponents.live_flooder_v1 as lf
import opponents.adversarial_champion_killer as ack
import opponents.o12_top_meta as o12
import scratch.v2_jit_opening_closed_loop as cand_c
from scratch.v2_jit_melon_experiment import agent_H_full_jit_pipeline

OPPONENT_FNS = {
    "v2": v2.agent,
    "v1": v1.agent,
    "live_flooder": lf.agent,
    "adversarial_champion_killer": ack.agent if hasattr(ack, "agent") else ack.OpponentBot().agent if hasattr(ack, "OpponentBot") else None,
    "o12_top_meta": o12.agent if hasattr(o12, "agent") else o12.OpponentBot().agent if hasattr(o12, "OpponentBot") else None,
}

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

def run_game(args):
    opp_key, seed, seat = args
    opp_fn = OPPONENT_FNS[opp_key]
    
    agent0 = robust(cand_c.agent if seat == 0 else opp_fn)
    agent1 = robust(opp_fn if seat == 0 else cand_c.agent)
    
    cfg = {"seed": seed, "episodeSteps": 720}
    env = make("kaggriculture", configuration=cfg)
    env.run([agent0, agent1])
    
    r_c = float(env.steps[-1][seat]["reward"] or 0)
    r_opp = float(env.steps[-1][1 - seat]["reward"] or 0)
    margin = r_c - r_opp
    win = 1.0 if r_c > r_opp else (0.5 if r_c == r_opp else 0.0)
    
    return {
        "opp_key": opp_key,
        "seed": seed,
        "seat": seat,
        "r_c": r_c,
        "r_opp": r_opp,
        "margin": margin,
        "win": win
    }

def main():
    tasks = []
    
    # Phase 10: 50 seeds vs V2, both seats = 100 matched games
    dev_seeds = list(range(100, 150))
    for s in dev_seeds:
        for seat in [0, 1]:
            tasks.append(("v2", s, seat))
            
    # Phase 12: Meta opponents (10 seeds each, both seats = 20 games each)
    meta_seeds = list(range(200, 210))
    for opp in ["live_flooder", "adversarial_champion_killer", "o12_top_meta", "v1"]:
        for s in meta_seeds:
            for seat in [0, 1]:
                tasks.append((opp, s, seat))
                
    print(f"Total benchmark games scheduled for Candidate C: {len(tasks)}")
    
    with ProcessPoolExecutor(max_workers=6) as executor:
        results = list(executor.map(run_game, tasks))
        
    grouped = {}
    for r in results:
        opp = r["opp_key"]
        if opp not in grouped:
            grouped[opp] = []
        grouped[opp].append(r)
        
    summary = {}
    for opp, records in grouped.items():
        margins = [r["margin"] for r in records]
        rewards_c = [r["r_c"] for r in records]
        rewards_opp = [r["r_opp"] for r in records]
        wins = [r["win"] for r in records]
        
        n = len(records)
        mean_m = float(np.mean(margins))
        std_m = float(np.std(margins, ddof=1)) if n > 1 else 0.0
        sem_m = std_m / np.sqrt(n) if n > 1 else 0.0
        
        summary[opp] = {
            "n_games": n,
            "win_rate_pct": float(np.mean(wins) * 100.0),
            "mean_reward_c": float(np.mean(rewards_c)),
            "mean_reward_opp": float(np.mean(rewards_opp)),
            "mean_margin": mean_m,
            "median_margin": float(np.median(margins)),
            "std_margin": std_m,
            "sem_margin": sem_m,
            "ci95_low": mean_m - 1.96 * sem_m,
            "ci95_high": mean_m + 1.96 * sem_m,
            "min_margin": float(np.min(margins)),
            "max_margin": float(np.max(margins))
        }
        
    print("\n--- CANDIDATE C BENCHMARK RESULTS ---")
    print(json.dumps(summary, indent=2))
    
    with open("scratch/jit_melon_results/candidate_c_benchmark_results.json", "w") as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    main()
