import os
import sys
import math
import json
import statistics
import importlib.util
from kaggle_environments.utils import Struct
from kaggle_environments import make
import kagsim

print("================================================================", flush=True)
print("RUNNING RIGOROUS AGENT BENCHMARKS & SEAT SYMMETRY (RULES 8 & 9)", flush=True)
print("================================================================", flush=True)

# Engine setup
env = make("kaggriculture", configuration={"episodeSteps": 720})
cfg = env.configuration

# Load agents
def load_agent(name, filepath):
    spec = importlib.util.spec_from_file_location(name, filepath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, "agent")

# Agent paths
AGENT_PATHS = {
    "V66": os.path.abspath(r"external_repos\kaggriculture-v66-agent\main.py"),
    "V54": os.path.abspath(r"external_repos\lixingtao123-Kaggriculture\variant_v54_h3q4\main.py"),
    "V2": os.path.abspath(r"agents\slot4_control_frozen_v2.py"),
    "Titan": os.path.abspath(r"candidates\slot1_titan_control.py"),
    "Okami": os.path.abspath(r"external_repos\okami001-Kaggriculture\main.py")
}

# Add v66 dir to sys.path
sys.path.insert(0, os.path.abspath(r"external_repos\kaggriculture-v66-agent"))

agents = {
    "V66": load_agent("v66", AGENT_PATHS["V66"]),
    "V54": load_agent("v54", AGENT_PATHS["V54"]),
    "V2": load_agent("v2", AGENT_PATHS["V2"]),
    "Titan": load_agent("titan", AGENT_PATHS["Titan"]),
    "Okami": load_agent("okami", AGENT_PATHS["Okami"]),
}

import hashlib
AGENT_HASHES = {}
for name, p in AGENT_PATHS.items():
    AGENT_HASHES[name] = hashlib.sha256(open(p, "rb").read()).hexdigest()

def call_agent(fn, obs, configuration):
    try:
        return fn(obs, configuration)
    except TypeError:
        return fn(obs)

SEEDS = [42, 101, 202, 303, 404, 505, 606, 707, 808, 909]

MATCHUPS = [
    ("V66", "V2"),
    ("V66", "V54"),
    ("V66", "Titan"),
    ("V54", "V2"),
    ("Okami", "V2")
]

def run_single_game(agent_a_name, agent_b_name, seed):
    fn_a = agents[agent_a_name]
    fn_b = agents[agent_b_name]
    
    game = kagsim.Game(seed)
    err = None
    for t in range(720):
        try:
            o0 = Struct(**game.observe(0))
            o1 = Struct(**game.observe(1))
            a0 = call_agent(fn_a, o0, cfg)
            a1 = call_agent(fn_b, o1, cfg)
            game.step(a0 if isinstance(a0, dict) else {}, a1 if isinstance(a1, dict) else {})
        except Exception as e:
            err = f"step {t}: {e}"
            break
            
    r0 = game.reward(0)
    r1 = game.reward(1)
    return {
        "seed": seed,
        "seat0_agent": agent_a_name,
        "seat1_agent": agent_b_name,
        "seat0_reward": r0,
        "seat1_reward": r1,
        "margin_a_minus_b": r0 - r1,
        "winner": agent_a_name if r0 > r1 else (agent_b_name if r1 > r0 else "TIE"),
        "error": err
    }

def compute_stats(margins, wins_a, wins_b, ties, n):
    if n == 0:
        return {}
    mean_m = statistics.mean(margins)
    med_m = statistics.median(margins)
    stdev_m = statistics.stdev(margins) if n > 1 else 0.0
    sem = stdev_m / math.sqrt(n) if n > 1 else 0.0
    ci_95 = 1.96 * sem
    return {
        "n_games": n,
        "wins_a": wins_a,
        "wins_b": wins_b,
        "ties": ties,
        "win_rate_a": wins_a / n,
        "win_rate_b": wins_b / n,
        "tie_rate": ties / n,
        "mean_margin": mean_m,
        "median_margin": med_m,
        "stdev_margin": stdev_m,
        "margin_ci95": [mean_m - ci_95, mean_m + ci_95]
    }

raw_results = {}
summary_results = {}

for name_a, name_b in MATCHUPS:
    pair_key = f"{name_a}_vs_{name_b}"
    print(f"\n=======================================================", flush=True)
    print(f"MATCHUP: {name_a} vs {name_b}", flush=True)
    print(f"=======================================================", flush=True)
    
    # 1. Orientation 1: A as seat 0, B as seat 1
    games_s0 = []
    print(f"--- Orientation 1: {name_a} (Seat 0) vs {name_b} (Seat 1) ---", flush=True)
    for s in SEEDS:
        res = run_single_game(name_a, name_b, s)
        games_s0.append(res)
        print(f"  Seed {s:4d}: {name_a}={res['seat0_reward']:8.1f} | {name_b}={res['seat1_reward']:8.1f} | Margin={res['margin_a_minus_b']:+8.1f} -> Winner: {res['winner']}", flush=True)
        
    # 2. Orientation 2: B as seat 0, A as seat 1
    games_s1 = []
    print(f"--- Orientation 2: {name_b} (Seat 0) vs {name_a} (Seat 1) ---", flush=True)
    for s in SEEDS:
        res = run_single_game(name_b, name_a, s)
        margin_from_a = res['seat1_reward'] - res['seat0_reward']
        winner_from_a = name_a if res['seat1_reward'] > res['seat0_reward'] else (name_b if res['seat0_reward'] > res['seat1_reward'] else "TIE")
        res["perspective_a"] = {
            "reward_a": res['seat1_reward'],
            "reward_b": res['seat0_reward'],
            "margin_a_minus_b": margin_from_a,
            "winner": winner_from_a
        }
        games_s1.append(res)
        print(f"  Seed {s:4d}: {name_b}={res['seat0_reward']:8.1f} | {name_a}={res['seat1_reward']:8.1f} | Margin (A-B)={margin_from_a:+8.1f} -> Winner: {winner_from_a}", flush=True)

    # Orientation 1 stats
    margins_s0 = [g['margin_a_minus_b'] for g in games_s0]
    wins_a_s0 = sum(1 for g in games_s0 if g['winner'] == name_a)
    wins_b_s0 = sum(1 for g in games_s0 if g['winner'] == name_b)
    ties_s0 = sum(1 for g in games_s0 if g['winner'] == 'TIE')
    stats_s0 = compute_stats(margins_s0, wins_a_s0, wins_b_s0, ties_s0, len(SEEDS))
    
    # Orientation 2 stats
    margins_s1 = [g['perspective_a']['margin_a_minus_b'] for g in games_s1]
    wins_a_s1 = sum(1 for g in games_s1 if g['perspective_a']['winner'] == name_a)
    wins_b_s1 = sum(1 for g in games_s1 if g['perspective_a']['winner'] == name_b)
    ties_s1 = sum(1 for g in games_s1 if g['perspective_a']['winner'] == 'TIE')
    stats_s1 = compute_stats(margins_s1, wins_a_s1, wins_b_s1, ties_s1, len(SEEDS))
    
    # Pooled stats
    pooled_margins = margins_s0 + margins_s1
    pooled_wins_a = wins_a_s0 + wins_a_s1
    pooled_wins_b = wins_b_s0 + wins_b_s1
    pooled_ties = ties_s0 + ties_s1
    stats_pooled = compute_stats(pooled_margins, pooled_wins_a, pooled_wins_b, pooled_ties, len(SEEDS) * 2)
    
    print(f"\n>>> Summary for {name_a} vs {name_b}:", flush=True)
    print(f"    Seat 0 (A as P0): Win Rate = {stats_s0['win_rate_a']*100:.1f}%, Mean Margin = {stats_s0['mean_margin']:+,.1f}", flush=True)
    print(f"    Seat 1 (A as P1): Win Rate = {stats_s1['win_rate_a']*100:.1f}%, Mean Margin = {stats_s1['mean_margin']:+,.1f}", flush=True)
    print(f"    POOLED (20 games): Win Rate = {stats_pooled['win_rate_a']*100:.1f}%, Mean Margin = {stats_pooled['mean_margin']:+,.1f}", flush=True)

    raw_results[pair_key] = {
        "agent_a": {"name": name_a, "path": AGENT_PATHS[name_a], "sha256": AGENT_HASHES[name_a]},
        "agent_b": {"name": name_b, "path": AGENT_PATHS[name_b], "sha256": AGENT_HASHES[name_b]},
        "orientation_a_p0_b_p1": games_s0,
        "orientation_b_p0_a_p1": games_s1
    }
    
    summary_results[pair_key] = {
        "agent_a": name_a,
        "agent_b": name_b,
        "orientation_a_as_seat0": stats_s0,
        "orientation_a_as_seat1": stats_s1,
        "pooled": stats_pooled
    }

# Save raw and summary JSON
with open(r"forensic_verification\benchmark_raw\agent_matchups_raw.json", "w", encoding="utf-8") as f:
    json.dump(raw_results, f, indent=2)

with open(r"forensic_verification\benchmark_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary_results, f, indent=2)

print("\nBenchmark runs finished and persisted to:", flush=True)
print("  - forensic_verification/benchmark_raw/agent_matchups_raw.json", flush=True)
print("  - forensic_verification/benchmark_summary.json", flush=True)
