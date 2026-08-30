import os, sys, time, json, hashlib
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
from kaggle_environments import make

def get_hash(fp):
    h = hashlib.sha256()
    with open(fp, 'rb') as f:
        while c := f.read(8192):
            h.update(c)
    return h.hexdigest()

def wilson_score_interval(wins, total, confidence=0.95):
    if total == 0: return 0.0, 0.0
    z = 1.95996
    p = wins / total
    denom = 1.0 + (z**2) / total
    center = (p + (z**2) / (2 * total)) / denom
    spread = (z / denom) * np.sqrt((p * (1.0 - p) / total) + ((z**2) / (4 * (total**2))))
    return max(0.0, center - spread) * 100.0, min(1.0, center + spread) * 100.0

def _run_single_match(task):
    agent0_path, agent1_path, seed, max_steps, swapped = task
    # Load dynamically in process
    import importlib.util
    def load(p):
        mod_name = "mod_" + hashlib.md5(p.encode()).hexdigest()
        spec = importlib.util.spec_from_file_location(mod_name, p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return getattr(mod, "agent", getattr(mod, "act", None))

    try:
        a0 = load(agent0_path)
        a1 = load(agent1_path)
        cfg = {"episodeSteps": max_steps, "seed": seed}
        env = make("kaggriculture", configuration=cfg, debug=False)
        t0 = time.time()
        env.run([a0, a1])
        elapsed = time.time() - t0
        final_step = env.steps[-1]
        r0 = float(final_step[0].reward or 0.0)
        r1 = float(final_step[1].reward or 0.0)
        
        r_us = r1 if swapped else r0
        r_opp = r0 if swapped else r1
        win = 1.0 if r_us > r_opp else (0.0 if r_opp > r_us else 0.5)
        margin = r_us - r_opp
        return {
            "seed": seed, "swapped": swapped, "r_us": r_us, "r_opp": r_opp,
            "margin": margin, "win": win, "elapsed": elapsed, "error": None
        }
    except Exception as e:
        return {
            "seed": seed, "swapped": swapped, "r_us": 0.0, "r_opp": 0.0,
            "margin": 0.0, "win": 0.0, "elapsed": 0.0, "error": str(e)
        }

def run_pairing_parallel(name_a, path_a, name_b, path_b, seeds, max_workers=6):
    hash_a = get_hash(path_a)
    hash_b = get_hash(path_b)
    
    tasks = []
    for s in seeds:
        # A as P0 (swapped=False)
        tasks.append((path_a, path_b, s, 720, False))
        # A as P1 (swapped=True)
        tasks.append((path_b, path_a, s, 720, True))
        
    t0 = time.time()
    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_run_single_match, t) for t in tasks]
        for f in as_completed(futures):
            results.append(f.result())
            
    elapsed = time.time() - t0
    
    p0_matches = [r for r in results if not r["swapped"]]
    p1_matches = [r for r in results if r["swapped"]]
    
    p0_wins = sum(r["win"] for r in p0_matches)
    p1_wins = sum(r["win"] for r in p1_matches)
    total_wins = p0_wins + p1_wins
    total_games = len(results)
    
    cash_a = [r["r_us"] for r in results]
    cash_b = [r["r_opp"] for r in results]
    margins = [r["margin"] for r in results]
    
    p0_wr = (p0_wins / len(p0_matches)) * 100.0
    p1_wr = (p1_wins / len(p1_matches)) * 100.0
    pooled_wr = (total_wins / total_games) * 100.0
    low_ci, upp_ci = wilson_score_interval(total_wins, total_games)
    mean_margin = float(np.mean(margins))
    mean_cash_a = float(np.mean(cash_a))
    mean_cash_b = float(np.mean(cash_b))
    
    print(f"\n======================================================================")
    print(f"PAIRING: {name_a} (Candidate) vs {name_b} (Opponent)")
    print(f"  Candidate SHA256: {hash_a[:16]}... ({path_a})")
    print(f"  Opponent SHA256:  {hash_b[:16]}... ({path_b})")
    print(f"  Games: {total_games} ({len(seeds)} paired seeds) | Time: {elapsed:.1f}s")
    print(f"  P0 Win Rate (A as P0): {p0_wr:5.1f}% ({p0_wins}/{len(p0_matches)})")
    print(f"  P1 Win Rate (A as P1): {p1_wr:5.1f}% ({p1_wins}/{len(p1_matches)})")
    print(f"  Side Asymmetry:        {p0_wr - p1_wr:+5.1f}pp")
    print(f"  Pooled Win Rate:       {pooled_wr:5.1f}% ({total_wins}/{total_games}) | 95% CI: [{low_ci:.1f}%, {upp_ci:.1f}%]")
    print(f"  Mean Cash A:           ${mean_cash_a:8,.2f}")
    print(f"  Mean Cash B:           ${mean_cash_b:8,.2f}")
    print(f"  Net Margin (A - B):    ${mean_margin:+8,.2f}")
    print(f"  Worst Margin:          ${np.min(margins):+8,.2f}")
    print(f"======================================================================")
    
    return {
        "candidate": {"name": name_a, "path": path_a, "sha256": hash_a},
        "opponent": {"name": name_b, "path": path_b, "sha256": hash_b},
        "num_seeds": len(seeds),
        "total_games": total_games,
        "p0_wr": p0_wr,
        "p1_wr": p1_wr,
        "asymmetry_pp": p0_wr - p1_wr,
        "pooled_wr": pooled_wr,
        "ci_95": [low_ci, upp_ci],
        "mean_cash_a": mean_cash_a,
        "mean_cash_b": mean_cash_b,
        "mean_margin": mean_margin,
        "worst_loss": float(np.min(margins)),
        "elapsed_seconds": elapsed
    }

def main():
    root = r"c:\Users\Sundareswaran\Kagriculture"
    ctrl = os.path.join(root, "agents", "slot4_control_frozen_v2.py")
    ctrl_clone = os.path.join(root, "agents", "ground_truth_control_current_engine.py")
    b14_clean = os.path.join(root, "agents", "ablation_batch_14.py")
    b14_gen = os.path.join(root, "generated_agents_1_32_7", "sweep_batch_14.py")
    titan_canonical = os.path.join(root, "opponents", "o1_titan.py")
    titan_old = os.path.join(root, "candidates", "slot1_titan_control.py")
    apex_v2 = os.path.join(root, "main.py")

    seeds_50 = [50000 + i for i in range(50)]
    
    all_experiments = []
    
    print("STARTING FORENSIC BENCHMARK VALIDATION SUITE...")
    
    # 1. Behavioral Equivalence: Control vs Control Clone
    r1 = run_pairing_parallel("Control v2", ctrl, "Control Clone (Ground Truth)", ctrl_clone, seeds_50)
    all_experiments.append(r1)
    
    # 2. Batch-14 Clone vs Control (Clean Clone)
    r2 = run_pairing_parallel("Batch 14 Clean", b14_clean, "Control v2", ctrl, seeds_50)
    all_experiments.append(r2)
    
    # 3. Batch-14 Generated Template vs Control (Why old report failed)
    r3 = run_pairing_parallel("Batch 14 Generated", b14_gen, "Control v2", ctrl, seeds_50)
    all_experiments.append(r3)
    
    # 4. Control vs Canonical Titan (o1_titan.py)
    r4 = run_pairing_parallel("Control v2", ctrl, "Canonical Titan (o1_titan)", titan_canonical, seeds_50)
    all_experiments.append(r4)
    
    # 5. Control vs Old Pure-Crop Titan (slot1_titan_control.py)
    r5 = run_pairing_parallel("Control v2", ctrl, "Old Titan (slot1_titan_control)", titan_old, seeds_50)
    all_experiments.append(r5)
    
    # 6. Apex v2 vs Control v2
    r6 = run_pairing_parallel("Apex v2 (main.py)", apex_v2, "Control v2", ctrl, seeds_50)
    all_experiments.append(r6)
    
    # 7. Apex v2 vs Canonical Titan (o1_titan.py)
    r7 = run_pairing_parallel("Apex v2 (main.py)", apex_v2, "Canonical Titan (o1_titan)", titan_canonical, seeds_50)
    all_experiments.append(r7)
    
    # 8. Apex v2 vs Old Pure-Crop Titan (slot1_titan_control.py)
    r8 = run_pairing_parallel("Apex v2 (main.py)", apex_v2, "Old Titan (slot1_titan_control)", titan_old, seeds_50)
    all_experiments.append(r8)
    
    out_path = os.path.join(root, "scratch", "forensic_suite_results.json")
    with open(out_path, "w") as f:
        json.dump(all_experiments, f, indent=2)
    print(f"\nAll forensic experiments saved to {out_path}")

if __name__ == "__main__":
    main()
