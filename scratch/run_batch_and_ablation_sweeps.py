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

def run_pairing(name_a, path_a, name_b, path_b, seeds, max_workers=6):
    hash_a = get_hash(path_a)
    hash_b = get_hash(path_b)
    
    tasks = []
    for s in seeds:
        tasks.append((path_a, path_b, s, 720, False))
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
    
    print(f"| {name_a:24s} | {p0_wr:5.1f}% | {p1_wr:5.1f}% | {pooled_wr:5.1f}% | [{low_ci:4.1f}%, {upp_ci:4.1f}%] | ${mean_cash_a:7,.0f} | ${mean_margin:+7,.0f} | ${np.min(margins):+7,.0f} |")
    
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
    seeds_50 = [50000 + i for i in range(50)]
    
    print("\n" + "=" * 95)
    print("PART 16: RIGOROUS BATCH SIZE SWEEP (4, 8, 12, 14, 16, 18, 20, 24) vs CONTROL")
    print("=" * 95)
    print(f"| {'Candidate':24s} | {'P0 WR':6s} | {'P1 WR':6s} | {'Pooled':6s} | {'95% CI':14s} | {'Cash':8s} | {'Margin':8s} | {'Worst':8s} |")
    print("|" + "-" * 26 + "|" + "-" * 8 + "|" + "-" * 8 + "|" + "-" * 8 + "|" + "-" * 16 + "|" + "-" * 10 + "|" + "-" * 10 + "|" + "-" * 10 + "|")
    
    batch_results = []
    for b in [4, 8, 12, 14, 16, 18, 20, 24]:
        p = os.path.join(root, "agents", f"ablation_batch_{b}.py")
        res = run_pairing(f"Batch {b}", p, "Control v2", ctrl, seeds_50)
        batch_results.append(res)
        
    print("\n" + "=" * 95)
    print("PART 15: APEX COMPONENT ABLATION SUITE vs CONTROL")
    print("=" * 95)
    print(f"| {'Ablation':24s} | {'P0 WR':6s} | {'P1 WR':6s} | {'Pooled':6s} | {'95% CI':14s} | {'Cash':8s} | {'Margin':8s} | {'Worst':8s} |")
    print("|" + "-" * 26 + "|" + "-" * 8 + "|" + "-" * 8 + "|" + "-" * 8 + "|" + "-" * 16 + "|" + "-" * 10 + "|" + "-" * 10 + "|" + "-" * 10 + "|")
    
    ablations = [
        ("Apex Base (v2 Full)", os.path.join(root, "scratch", "clean_ablations", "apex_base.py")),
        ("- No 2-Day Buffer (4d)", os.path.join(root, "scratch", "clean_ablations", "apex_no_2day_feed.py")),
        ("- No Batch 24 (b=14)", os.path.join(root, "scratch", "clean_ablations", "apex_no_batch24.py")),
        ("- No Cycle-2 Melons", os.path.join(root, "scratch", "clean_ablations", "apex_no_cycle2_melon.py")),
        ("- No Day-0 Land (Late)", os.path.join(root, "scratch", "clean_ablations", "apex_no_day0_land.py")),
        ("- No Emergency Liq", os.path.join(root, "scratch", "clean_ablations", "apex_no_emergency.py")),
    ]
    
    ablation_results = []
    for name, p in ablations:
        res = run_pairing(name, p, "Control v2", ctrl, seeds_50)
        ablation_results.append(res)
        
    out_path = os.path.join(root, "scratch", "batch_and_ablation_results.json")
    with open(out_path, "w") as f:
        json.dump({"batch_sweep": batch_results, "ablation_suite": ablation_results}, f, indent=2)
    print(f"\nSaved batch sweep and ablation results to: {out_path}")

if __name__ == "__main__":
    main()
