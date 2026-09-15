"""
Section 11: Unified Agent Comparison
Compares our best existing policies against reconstructed V54 and V66:
1. Slot 1 (Aethel V1)
2. Aethel V2
3. M1 (Fertilizer Gated)
4. L_Minimal (Labor Minimal)
5. B1 (Research B Only)
6. Reconstructed V54
7. Reconstructed V66

Evaluated across 10 fixed seeds (2000-2009):
- Solo vs IDLE
- H2H vs V54
Outputs:
- research/v54_v66_vs_our_agents.csv
"""
import sys, os, json, csv, statistics, importlib.util
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import defaultdict

AGENTS = {
    "Aethel_V1":   "agents/candidate_a_aethel_v1.py",
    "Aethel_V2":   "agents/slot4_control_frozen_v2.py",
    "M1_FertGate": "candidates/candidate_cl_fert_gated.py",
    "L_Minimal":   "candidates/candidate_cl_labor_minimal_v1.py",
    "B1_Modular":  "candidates/research_b_only_v1.py",
    "V54":         "external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py",
    "V66":         "external_repos/kaggriculture-v66-agent/main.py",
}

SEEDS = list(range(2000, 2010))

def _run_match_task(task):
    agent_name, agent_path, opp_name, seed = task
    from kaggle_environments import make
    
    # Load agent 0
    d0 = os.path.dirname(os.path.abspath(agent_path))
    if d0 not in sys.path: sys.path.insert(0, d0)
    spec0 = importlib.util.spec_from_file_location("a0_mod", agent_path)
    m0 = importlib.util.module_from_spec(spec0)
    spec0.loader.exec_module(m0)
    fn0 = getattr(m0, "agent", None) or getattr(m0, "_kaggle_submission_entrypoint", None)
    if fn0 is None and hasattr(m0, "ResearchBOnlyV1"):
        inst = m0.ResearchBOnlyV1()
        fn0 = lambda obs, cfg=None: inst(obs, cfg)
        
    # Load agent 1 (IDLE or V54)
    if opp_name == "IDLE":
        fn1 = lambda obs, cfg=None: {"market": [], "farmer": ["PASS"], "hands": []}
    else:
        v54_p = "external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py"
        d1 = os.path.dirname(os.path.abspath(v54_p))
        if d1 not in sys.path: sys.path.insert(0, d1)
        spec1 = importlib.util.spec_from_file_location("v54_mod", v54_p)
        m1 = importlib.util.module_from_spec(spec1)
        spec1.loader.exec_module(m1)
        fn1 = getattr(m1, "agent", None)
        
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.run([fn0, fn1])
    
    r0 = float(env.steps[-1][0].reward or 0.0)
    r1 = float(env.steps[-1][1].reward or 0.0)
    
    # Extract end state metrics
    farm0 = env.steps[-1][0].observation.farms[0]
    cows = sum(1 for row in farm0["tiles"] for t in row if isinstance(t, dict) and t.get("animal") == "COW")
    sheep = sum(1 for row in farm0["tiles"] for t in row if isinstance(t, dict) and t.get("animal") == "SHEEP")
    quads = len(farm0["unlocked_quadrants"])
    
    return agent_name, opp_name, seed, r0, r1, cows, sheep, quads

if __name__ == "__main__":
    os.makedirs("research", exist_ok=True)
    os.makedirs("scratch", exist_ok=True)
    
    tasks = []
    for a_name, a_path in AGENTS.items():
        for opp in ["IDLE", "V54"]:
            for seed in SEEDS:
                tasks.append((a_name, a_path, opp, seed))
                
    print(f"Running Unified Comparison: {len(tasks)} matches across 8 parallel workers...")
    
    raw_results = defaultdict(lambda: defaultdict(list))
    
    with ProcessPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(_run_match_task, t) for t in tasks]
        done = 0
        for f in as_completed(futures):
            a_name, opp_name, seed, r0, r1, cows, sheep, quads = f.result()
            raw_results[a_name][opp_name].append({
                "seed": seed, "r0": r0, "r1": r1, "cows": cows, "sheep": sheep, "quads": quads
            })
            done += 1
            if done % 20 == 0:
                print(f"  ... {done}/{len(tasks)} completed")
                
    print("Writing research/v54_v66_vs_our_agents.csv...")
    csv_path = "research/v54_v66_vs_our_agents.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Agent", "Solo_Reward_IDLE", "H2H_Reward_vs_V54", "Opp_Reward_V54", "Margin_vs_V54", "WinRate_vs_V54", "Mean_Cows", "Mean_Sheep", "Mean_Quads", "Generation_Archetype"])
        
        archetypes = {
            "Aethel_V1": "Early Heuristic / Strawb-Heavy",
            "Aethel_V2": "Conservative Frozen Controller",
            "M1_FertGate": "Closed-Loop Gated Fertilizer",
            "L_Minimal": "Low-Labor Budget Controller",
            "B1_Modular": "Modular Economic Solver",
            "V54": "Self-Sufficient Wheat Feed + Front-Running",
            "V66": "Meta-Classifier + Adaptive Q2 Router",
        }
        
        for a_name in AGENTS:
            idle_rows = raw_results[a_name]["IDLE"]
            v54_rows = raw_results[a_name]["V54"]
            
            m_idle = statistics.mean([x["r0"] for x in idle_rows])
            m_v54_r0 = statistics.mean([x["r0"] for x in v54_rows])
            m_v54_r1 = statistics.mean([x["r1"] for x in v54_rows])
            margin = m_v54_r0 - m_v54_r1
            win_rate = sum(1 for x in v54_rows if x["r0"] > x["r1"]) / len(v54_rows)
            cows = statistics.mean([x["cows"] for x in v54_rows])
            sheep = statistics.mean([x["sheep"] for x in v54_rows])
            quads = statistics.mean([x["quads"] for x in v54_rows])
            arch = archetypes.get(a_name, "Unknown")
            
            writer.writerow([a_name, f"{m_idle:.0f}", f"{m_v54_r0:.0f}", f"{m_v54_r1:.0f}", f"{margin:+.0f}", f"{win_rate:.1%}", f"{cows:.1f}", f"{sheep:.1f}", f"{quads:.1f}", arch])
            print(f"{a_name:12s} | Solo: {m_idle:7.0f} | vs V54: {m_v54_r0:7.0f} vs {m_v54_r1:7.0f} ({margin:+7.0f}, Win {win_rate:.0%}) | Cows={cows:.1f}, Sheep={sheep:.1f}, Quads={quads:.1f} | {arch}")
            
    print(f"Saved to {csv_path}")
