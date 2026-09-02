import json
import os
import sys
import importlib.util
import kaggle_environments
import pandas as pd
import numpy as np

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Helper to load agent from file
def load_agent(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if hasattr(mod, "agent"):
        return mod.agent
    elif hasattr(mod, "kaggle_agent"):
        return mod.kaggle_agent
    elif hasattr(mod, "ApexGrandmasterV4"):
        inst = mod.ApexGrandmasterV4()
        return lambda obs, cfg=None: inst(obs, cfg)
    elif hasattr(mod, "main"):
        return mod.main
    raise ValueError(f"No agent callable found in {path}")

# Load Route A and B from worked_example_routes.json
def load_worked_routes():
    with open("replays/raw/destbreso/worked_example_routes.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    route_a = data["A"]["route"]
    route_b = data["B"]["route"]
    
    def agent_a(obs, cfg=None):
        step = min(int(obs.get("step", 0) or 0), len(route_a) - 1)
        return route_a[step]
        
    def agent_b(obs, cfg=None):
        step = min(int(obs.get("step", 0) or 0), len(route_b) - 1)
        return route_b[step]
        
    return agent_a, agent_b

def run_matchup(agent1, agent2, name1, name2, seed):
    env = kaggle_environments.make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    
    # Run P0=agent1, P1=agent2
    env.reset()
    state = env.run([agent1, agent2])
    reward0 = state[-1][0]["reward"]
    reward1 = state[-1][1]["reward"]
    
    # Run P0=agent2, P1=agent1 (paired on same seed)
    env.reset()
    state_rev = env.run([agent2, agent1])
    reward1_rev = state_rev[-1][0]["reward"]
    reward0_rev = state_rev[-1][1]["reward"]
    
    return {
        "seed": seed,
        "name1": name1,
        "name2": name2,
        "as_P0_score1": reward0,
        "as_P0_score2": reward1,
        "as_P0_margin1": reward0 - reward1,
        "as_P1_score1": reward0_rev,
        "as_P1_score2": reward1_rev,
        "as_P1_margin1": reward0_rev - reward1_rev,
        "paired_margin1": ((reward0 - reward1) + (reward0_rev - reward1_rev)) / 2.0,
        "paired_wins1": (1 if reward0 > reward1 else 0) + (1 if reward0_rev > reward1_rev else 0)
    }

def main():
    print("=== LOADING CANDIDATE AGENTS ===")
    agents = {}
    
    # 1. Apex V4
    try:
        agents["Apex_V4"] = load_agent("main.py", "apex_v4")
        print("Loaded Apex_V4 from main.py")
    except Exception as e:
        print(f"Error loading Apex_V4: {e}")
        
    # 2. Closer Cleo
    try:
        agents["Closer_Cleo"] = load_agent("replays/raw/reference_agents/closer_cleo.py", "closer_cleo")
        print("Loaded Closer_Cleo (Tier 9)")
    except Exception as e:
        print(f"Error loading Closer_Cleo: {e}")
        
    # 3. Slotter Silas
    try:
        agents["Slotter_Silas"] = load_agent("replays/raw/reference_agents/slotter_silas.py", "slotter_silas")
        print("Loaded Slotter_Silas (Tier 7)")
    except Exception as e:
        print(f"Error loading Slotter_Silas: {e}")
        
    # 4. Route A & Route B
    try:
        route_a, route_b = load_worked_routes()
        agents["Route_A_Utkarsh"] = route_a
        agents["Route_B_Mohamed"] = route_b
        print("Loaded Route_A (Rank 2) & Route_B (Rank 9)")
    except Exception as e:
        print(f"Error loading Routes: {e}")
        
    # Run test arena across 10 distinct seeds
    test_seeds = [1001, 2024, 3037, 4099, 5012, 6077, 7088, 8099, 9011, 12345]
    
    matchups = [
        ("Apex_V4", "Closer_Cleo"),
        ("Apex_V4", "Route_A_Utkarsh"),
        ("Apex_V4", "Slotter_Silas"),
        ("Closer_Cleo", "Route_A_Utkarsh"),
        ("Closer_Cleo", "Route_B_Mohamed")
    ]
    
    all_results = []
    
    for n1, n2 in matchups:
        if n1 not in agents or n2 not in agents:
            continue
        print(f"\n==========================================")
        print(f"MATCHUP: {n1} vs {n2} (10 Seeds x 2 Seats = 20 Games)")
        print(f"==========================================")
        pair_margins = []
        wins1 = 0
        total_games = 0
        
        for seed in test_seeds:
            res = run_matchup(agents[n1], agents[n2], n1, n2, seed)
            all_results.append(res)
            pair_margins.append(res["paired_margin1"])
            wins1 += res["paired_wins1"]
            total_games += 2
            print(f"Seed {seed:5d} | P0 Margin: {res['as_P0_margin1']:+8.0f} (Scores: {res['as_P0_score1']:6.0f} vs {res['as_P0_score2']:6.0f}) | P1 Margin: {res['as_P1_margin1']:+8.0f} (Scores: {res['as_P1_score1']:6.0f} vs {res['as_P1_score2']:6.0f}) | Paired: {res['paired_margin1']:+8.0f}")
            
        mean_paired = np.mean(pair_margins)
        std_paired = np.std(pair_margins)
        win_rate = (wins1 / total_games) * 100.0
        print(f"\n---> {n1} vs {n2} RESULT:")
        print(f"     Win Rate: {win_rate:.1f}% ({wins1}/{total_games})")
        print(f"     Mean Paired Margin: {mean_paired:+.1f} (+/- {std_paired:.1f})")

    df = pd.DataFrame(all_results)
    os.makedirs("scratch", exist_ok=True)
    df.to_csv("scratch/initial_arena_benchmark.csv", index=False)

if __name__ == "__main__":
    main()
