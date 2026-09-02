import os
import sys
import importlib.util
import kaggle_environments
import pandas as pd
import numpy as np
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

def test_gate_0_and_1():
    print("\n=======================================================", flush=True)
    print("=== GATE 0 & 1: ENGINE FIXTURE, SAFETY & TIMING TEST ===", flush=True)
    print("=======================================================", flush=True)
    
    spec = importlib.util.spec_from_file_location("main_mod", "main.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    candidate = getattr(mod, "kaggle_agent", getattr(mod, "agent", None))
    assert candidate is not None, "No candidate callable found!"
    
    env = kaggle_environments.make("kaggriculture", configuration={"seed": 42, "episodeSteps": 720})
    env.reset()
    
    # Test step 0 execution time
    t0 = time.perf_counter()
    obs0 = env.steps[-1][0]["observation"]
    obs0["player"] = 0
    obs0["step"] = 0
    act0 = candidate(obs0, env.configuration)
    dt0 = time.perf_counter() - t0
    
    assert isinstance(act0, dict), "Action must be dict"
    assert "farmer" in act0 and "hands" in act0 and "market" in act0
    print(f"Step 0 Action generated in {dt0*1000:.3f} ms. Keys: {sorted(act0.keys())}", flush=True)
    
    # Run full 720-step game against self
    t_start = time.perf_counter()
    state = env.run([candidate, candidate])
    t_total = time.perf_counter() - t_start
    
    score0 = state[-1][0]["reward"]
    score1 = state[-1][1]["reward"]
    status0 = state[-1][0]["status"]
    status1 = state[-1][1]["status"]
    
    assert status0 == "DONE" and status1 == "DONE", f"Statuses not DONE: {status0}, {status1}"
    print(f"Full 720-step match completed in {t_total:.2f}s ({t_total/720*1000:.3f} ms/step).", flush=True)
    print(f"Scores: P0={score0:.0f}, P1={score1:.0f} | Statuses: {status0}, {status1}", flush=True)
    print(">>> GATE 0 & 1 PASSED WITH ZERO EXCEPTIONS! <<<\n", flush=True)

def run_single_simulation(args):
    agent1_path, agent2_path, name1, name2, seed, p0_is_1 = args
    
    spec1 = importlib.util.spec_from_file_location("mod1", agent1_path)
    m1 = importlib.util.module_from_spec(spec1)
    spec1.loader.exec_module(m1)
    a1 = getattr(m1, "kaggle_agent", getattr(m1, "agent", getattr(m1, "main", None)))
    if a1 is None and hasattr(m1, "ApexGrandmasterV4"):
        inst = m1.ApexGrandmasterV4()
        a1 = lambda obs, cfg=None: inst(obs, cfg)

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

def run_gate_2_tournament():
    print("=======================================================", flush=True)
    print("=== GATE 2: 160-GAME TOURNAMENT ARENA BENCHMARK ===", flush=True)
    print("=======================================================", flush=True)
    
    agents = {
        "Aethel_Prime_V1": os.path.abspath("main.py"),
        "Apex_V4_Control": os.path.abspath("candidates/apex_v4_submission_backup.py"),
        "Closer_Cleo": os.path.abspath("replays/raw/reference_agents/closer_cleo.py"),
        "Broker_Bea": os.path.abspath("replays/raw/reference_agents/broker_bea.py"),
        "Slotter_Silas": os.path.abspath("replays/raw/reference_agents/slotter_silas.py"),
        "Rancher_Rita": os.path.abspath("replays/raw/reference_agents/rancher_rita.py")
    }
    
    seeds = [1001, 2024, 3037, 4099, 5012, 6077, 7088, 8099, 9011, 12345]
    
    matchups = [
        ("Aethel_Prime_V1", "Apex_V4_Control"),
        ("Aethel_Prime_V1", "Closer_Cleo"),
        ("Aethel_Prime_V1", "Broker_Bea"),
        ("Aethel_Prime_V1", "Slotter_Silas"),
        ("Aethel_Prime_V1", "Rancher_Rita")
    ]
    
    tasks = []
    for n1, n2 in matchups:
        for s in seeds:
            tasks.append((agents[n1], agents[n2], n1, n2, s, True))
            tasks.append((agents[n1], agents[n2], n1, n2, s, False))
            
    print(f"Running {len(tasks)} tournament games across {os.cpu_count()} CPU cores...", flush=True)
    
    results = []
    with ProcessPoolExecutor(max_workers=min(8, os.cpu_count() or 4)) as pool:
        futures = {pool.submit(run_single_simulation, t): t for t in tasks}
        completed = 0
        for f in as_completed(futures):
            res = f.result()
            results.append(res)
            completed += 1
            if completed % 10 == 0 or completed == len(tasks):
                print(f"Completed {completed}/{len(tasks)} tournament games...", flush=True)
                
    df = pd.DataFrame(results)
    df.to_csv("scratch/aethel_prime_tournament_results.csv", index=False)
    
    print("\n=======================================================", flush=True)
    print("=== AETHEL-PRIME V1 TOURNAMENT VERDICT ===", flush=True)
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
            "Aethel Score": f"{mean_score1:7.1f}",
            "Opp Score": f"{mean_score2:7.1f}",
            "Mean Margin": f"{mean_margin:+8.1f}",
            "Paired Margin": f"{np.mean(paired_margins):+8.1f} (+/- {np.std(paired_margins):.1f})"
        })
        
    sum_df = pd.DataFrame(summary)
    print(sum_df.to_string(index=False), flush=True)
    sum_df.to_csv("scratch/aethel_prime_verdict.csv", index=False)

if __name__ == "__main__":
    test_gate_0_and_1()
    run_gate_2_tournament()
