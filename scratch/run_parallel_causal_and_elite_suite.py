import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
import json
import numpy as np
from concurrent.futures import ProcessPoolExecutor

ELITES = [
    ("Replay Crop Dusta", "opponents/replay_crop_dusta.py"),
    ("Replay Whyme Labs", "opponents/replay_whyme_labs.py"),
    ("Replay Kawatta Taido", "opponents/replay_kawatta_taido.py"),
    ("Replay MTN", "opponents/replay_mtn.py"),
    ("Replay Yuan800", "opponents/replay_yuan800.py"),
    ("Candidate Aethel V1 (Live Slot 1)", "agents/candidate_a_aethel_v1.py"),
    ("Slot 2 Aethel Refined V2 (Live Slot 2)", "candidates/slot2_aethel_refined_v2.py"),
]

CANDIDATES = [
    ("Candidate V2 Adaptive Overlay", "candidates/candidate_v2_adaptive_overlay.py"),
    ("Frozen V2 Baseline", "candidates/slot2_aethel_refined_v2.py"),
    ("CL-Aethel Grandmaster", "candidates/candidate_cl_aethel_grandmaster.py")
]

SEEDS_ELITE = [42, 101, 215, 333, 404, 555, 1000, 2024]

def elite_worker(task):
    c_name, e_name, p0, p1, s, seat = task
    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": s})
    env.run([p0, p1])
    r0 = env.steps[-1][0]["reward"]
    r1 = env.steps[-1][1]["reward"]
    if seat == 0:
        c_score = r0
        e_score = r1
    else:
        c_score = r1
        e_score = r0
    margin = c_score - e_score
    return c_name, e_name, c_score, e_score, margin

def run_elite_replays_parallel():
    print("\n================================================================================")
    print("PHASE 14 & 15: ELITE REPLAYS & DIRECT HEAD-TO-HEAD (PARALLELIZED)")
    print("================================================================================")
    
    tasks = []
    for c_name, c_path in CANDIDATES:
        for e_name, e_path in ELITES:
            for s in SEEDS_ELITE:
                # Seat 0
                tasks.append((c_name, e_name, c_path, e_path, s, 0))
                # Seat 1
                tasks.append((c_name, e_name, e_path, c_path, s, 1))
                
    print(f"Executing {len(tasks)} matched tournament games across 8 workers...")
    
    results_raw = {}
    for c_name, _ in CANDIDATES:
        results_raw[c_name] = {e_name: {"cand_scores": [], "opp_scores": [], "margins": []} for e_name, _ in ELITES}
        
    with ProcessPoolExecutor(max_workers=8) as executor:
        for c_name, e_name, c_score, e_score, margin in executor.map(elite_worker, tasks):
            results_raw[c_name][e_name]["cand_scores"].append(c_score)
            results_raw[c_name][e_name]["opp_scores"].append(e_score)
            results_raw[c_name][e_name]["margins"].append(margin)
            
    summary = {}
    for c_name in results_raw:
        print(f"\n--- Results for {c_name} ---")
        summary[c_name] = {}
        for e_name in results_raw[c_name]:
            d = results_raw[c_name][e_name]
            cand_s = d["cand_scores"]
            opp_s = d["opp_scores"]
            margins = d["margins"]
            wins = sum(1 for m in margins if m > 0)
            losses = sum(1 for m in margins if m < 0)
            ties = sum(1 for m in margins if m == 0)
            n_matches = len(margins)
            wr = wins / n_matches
            mean_c = float(np.mean(cand_s))
            mean_e = float(np.mean(opp_s))
            mean_m = float(np.mean(margins))
            wlt_str = f"{wins}-{losses}-{ties}"
            print(f"  vs {e_name:<38}: W-L-T={wlt_str:<8} (WR={wr*100:5.1f}%), Cand=${mean_c:>9.2f}, Opp=${mean_e:>9.2f}, Margin=+${mean_m:>9.2f}")
            summary[c_name][e_name] = {
                "n": n_matches,
                "W-L-T": wlt_str,
                "win_rate": wr,
                "mean_cand": mean_c,
                "mean_opp": mean_e,
                "mean_margin": mean_m,
                "p5_cand": float(np.percentile(cand_s, 5)),
                "p10_cand": float(np.percentile(cand_s, 10))
            }
            
    with open('scratch/overlay_elite_replays_results.json', 'w') as f:
        json.dump(summary, f, indent=2)
    return summary

if __name__ == '__main__':
    run_elite_replays_parallel()
