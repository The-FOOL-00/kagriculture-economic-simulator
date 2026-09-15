"""
PHASE 15: LIVE OPPONENT DISTRIBUTION BENCHMARK
Evaluates ClosedLoopV2 and ClosedLoopV3 against top leaderboard archetypes:
1. o1_titan (Titan Livestock / Crop Grandmaster)
2. replay_whyme_labs (Rank 5 Champion Replay)
Across 10 representative test seeds.
"""
import os, sys, json
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))
sys.path.insert(0, os.path.join(BASE_DIR, "opponents"))

import kagsim
from closed_loop_v2 import ClosedLoopAgentV2
from closed_loop_v3 import ClosedLoopAgentV3
import o1_titan
import replay_whyme_labs

def evaluate_vs_bot(agent_cls, bot_func, seeds):
    margins = []
    wins = 0
    scores = []
    for s in seeds:
        for seat in [0, 1]:
            g = kagsim.Game(s)
            ag = agent_cls()
            if seat == 0:
                while not g.done:
                    g.step(ag.act(g.observe(0)), bot_func(g.observe(1)))
                r_ag = g.reward(0); r_bot = g.reward(1)
            else:
                while not g.done:
                    g.step(bot_func(g.observe(0)), ag.act(g.observe(1)))
                r_ag = g.reward(1); r_bot = g.reward(0)
            margins.append(r_ag - r_bot)
            scores.append(r_ag)
            if r_ag > r_bot: wins += 1
    n = len(margins)
    return {
        "mean_score": round(sum(scores) / n, 2),
        "mean_margin": round(sum(margins) / n, 2),
        "win_rate": round(wins / n, 4),
        "worst_loss": round(min(margins), 2)
    }

def run_opponent_benchmark():
    test_seeds = list(range(50000, 50010)) # 10 seeds x 2 seats = 20 games
    print("Running opponent benchmark against o1_titan and replay_whyme_labs...", flush=True)
    
    res_v2_titan = evaluate_vs_bot(ClosedLoopAgentV2, o1_titan.agent, test_seeds)
    print(f"V2 vs Titan: Win Rate={res_v2_titan['win_rate']:.1%} | Margin={res_v2_titan['mean_margin']:+,.0f} | Cash=${res_v2_titan['mean_score']:,.0f}")
    
    res_v3_titan = evaluate_vs_bot(ClosedLoopAgentV3, o1_titan.agent, test_seeds)
    print(f"V3 vs Titan: Win Rate={res_v3_titan['win_rate']:.1%} | Margin={res_v3_titan['mean_margin']:+,.0f} | Cash=${res_v3_titan['mean_score']:,.0f}")
    
    res_v2_whyme = evaluate_vs_bot(ClosedLoopAgentV2, replay_whyme_labs.agent, test_seeds)
    print(f"V2 vs Whyme Labs: Win Rate={res_v2_whyme['win_rate']:.1%} | Margin={res_v2_whyme['mean_margin']:+,.0f} | Cash=${res_v2_whyme['mean_score']:,.0f}")
    
    res_v3_whyme = evaluate_vs_bot(ClosedLoopAgentV3, replay_whyme_labs.agent, test_seeds)
    print(f"V3 vs Whyme Labs: Win Rate={res_v3_whyme['win_rate']:.1%} | Margin={res_v3_whyme['mean_margin']:+,.0f} | Cash=${res_v3_whyme['mean_score']:,.0f}")
    
    out_path = os.path.join(BASE_DIR, "scratch", "live_opponent_benchmark_results.json")
    with open(out_path, "w") as f:
        json.dump({
            "v2_vs_titan": res_v2_titan,
            "v3_vs_titan": res_v3_titan,
            "v2_vs_whyme": res_v2_whyme,
            "v3_vs_whyme": res_v3_whyme
        }, f, indent=2)

if __name__ == "__main__":
    run_opponent_benchmark()
