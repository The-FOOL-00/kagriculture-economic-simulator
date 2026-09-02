import os
import sys
import importlib.util
import kaggle_environments
import pandas as pd
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

def run_single_simulation(args):
    agent1_path, agent2_path, name1, name2, seed, p0_is_1 = args
    
    # Load agent 1
    spec1 = importlib.util.spec_from_file_location("mod1", agent1_path)
    m1 = importlib.util.module_from_spec(spec1)
    spec1.loader.exec_module(m1)
    a1 = getattr(m1, "kaggle_agent", getattr(m1, "agent", getattr(m1, "main", None)))
    if a1 is None and hasattr(m1, "ApexGrandmasterV4"):
        inst = m1.ApexGrandmasterV4()
        a1 = lambda obs, cfg=None: inst(obs, cfg)

    # Load agent 2
    spec2 = importlib.util.spec_from_file_location("mod2", agent2_path)
    m2 = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(m2)
    a2 = getattr(m2, "kaggle_agent", getattr(m2, "agent", getattr(m2, "main", None)))
    if a2 is None and hasattr(m2, "ApexGrandmasterV4"):
        inst = m2.ApexGrandmasterV4()
        a2 = lambda obs, cfg=None: inst(obs, cfg)

    pair = [a1, a2] if p0_is_1 else [a2, a1]
    
    env = kaggle_environments.make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env.reset()
    state = env.run(pair)
    r0 = float(state[-1][0]["reward"])
    r1 = float(state[-1][1]["reward"])
    
    score1 = r0 if p0_is_1 else r1
    score2 = r1 if p0_is_1 else r0
    seat1 = "P0" if p0_is_1 else "P1"
    
    return {
        "name1": name1,
        "name2": name2,
        "seed": seed,
        "seat1": seat1,
        "score1": score1,
        "score2": score2,
        "margin1": score1 - score2,
        "win1": 1 if score1 > score2 else 0,
        "loss1": 1 if score1 < score2 else 0,
        "tie": 1 if score1 == score2 else 0
    }

def main():
    agents = {
        "Apex_V4": os.path.abspath("main.py"),
        "Closer_Cleo": os.path.abspath("replays/raw/reference_agents/closer_cleo.py"),
        "Slotter_Silas": os.path.abspath("replays/raw/reference_agents/slotter_silas.py"),
        "Ledger_Lena": os.path.abspath("replays/raw/reference_agents/ledger_lena.py"),
        "Broker_Bea": os.path.abspath("replays/raw/reference_agents/broker_bea.py"),
        "Rancher_Rita": os.path.abspath("replays/raw/reference_agents/rancher_rita.py"),
        "Melon_Mateo": os.path.abspath("replays/raw/reference_agents/melon_mateo.py")
    }
    
    seeds = [1001, 2024, 3037, 4099, 5012, 6077, 7088, 8099, 9011, 12345]
    
    matchups = [
        ("Apex_V4", "Closer_Cleo"),
        ("Apex_V4", "Slotter_Silas"),
        ("Apex_V4", "Broker_Bea"),
        ("Apex_V4", "Rancher_Rita"),
        ("Apex_V4", "Melon_Mateo"),
        ("Closer_Cleo", "Slotter_Silas"),
        ("Closer_Cleo", "Ledger_Lena"),
        ("Closer_Cleo", "Broker_Bea")
    ]
    
    tasks = []
    for n1, n2 in matchups:
        for s in seeds:
            tasks.append((agents[n1], agents[n2], n1, n2, s, True))
            tasks.append((agents[n1], agents[n2], n1, n2, s, False))
            
    print(f"Executing {len(tasks)} games across {os.cpu_count()} CPU cores in parallel...", flush=True)
    
    results = []
    with ProcessPoolExecutor(max_workers=min(8, os.cpu_count() or 4)) as pool:
        futures = {pool.submit(run_single_simulation, t): t for t in tasks}
        completed = 0
        for f in as_completed(futures):
            res = f.result()
            results.append(res)
            completed += 1
            if completed % 10 == 0 or completed == len(tasks):
                print(f"Completed {completed}/{len(tasks)} games...", flush=True)
                
    df = pd.DataFrame(results)
    os.makedirs("scratch", exist_ok=True)
    df.to_csv("scratch/comprehensive_arena_results.csv", index=False)
    
    print("\n=======================================================", flush=True)
    print("=== TOURNAMENT / ARENA RESULTS SUMMARY ===", flush=True)
    print("=======================================================", flush=True)
    
    summary = []
    for (n1, n2), grp in df.groupby(["name1", "name2"]):
        total = len(grp)
        wins = grp["win1"].sum()
        losses = grp["loss1"].sum()
        ties = grp["tie"].sum()
        mean_score1 = grp["score1"].mean()
        mean_score2 = grp["score2"].mean()
        mean_margin = grp["margin1"].mean()
        win_rate = (wins / total) * 100.0
        
        # Paired margin per seed
        paired_margins = []
        for s, sgrp in grp.groupby("seed"):
            p0_m = sgrp[sgrp["seat1"] == "P0"]["margin1"].values[0]
            p1_m = sgrp[sgrp["seat1"] == "P1"]["margin1"].values[0]
            paired_margins.append((p0_m + p1_m) / 2.0)
            
        summary.append({
            "Matchup": f"{n1} vs {n2}",
            "Games": total,
            "W/L/T": f"{wins}/{losses}/{ties}",
            "Win Rate": f"{win_rate:.1f}%",
            "Score 1": f"{mean_score1:7.1f}",
            "Score 2": f"{mean_score2:7.1f}",
            "Mean Margin": f"{mean_margin:+8.1f}",
            "Paired Margin": f"{np.mean(paired_margins):+8.1f} (+/- {np.std(paired_margins):.1f})"
        })
        
    sum_df = pd.DataFrame(summary)
    print(sum_df.to_string(index=False), flush=True)
    sum_df.to_csv("scratch/matchup_summary.csv", index=False)

if __name__ == "__main__":
    main()
