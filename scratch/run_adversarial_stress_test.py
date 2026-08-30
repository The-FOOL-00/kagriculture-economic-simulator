import os
import sys
import time
import math
import json
import numpy as np
from concurrent.futures import ProcessPoolExecutor
from kaggle_environments import make

project_root = r"c:\Users\Sundareswaran\Kagriculture"
adv_dir = os.path.join(project_root, "scratch", "adversaries")

def generate_adversaries():
    os.makedirs(adv_dir, exist_ok=True)
    with open(os.path.join(project_root, "agents", "apex_v2_frozen.py"), "r", encoding="utf-8") as f:
        apex_code = f.read()

    # Adversary 1: Predatory Early-Melon Frontrunner
    adv1_code = apex_code.replace(
        'target_melons=15,\n        cycle2_melons=8,',
        'target_melons=20,\n        cycle2_melons=12,'
    ).replace(
        'if age >= 10 or t.get("yield_units", 0) >= 6',
        'if age >= 9 or t.get("yield_units", 0) >= 4'
    )
    with open(os.path.join(adv_dir, "adv1_melon_predator.py"), "w", encoding="utf-8") as f:
        f.write(adv1_code)

    # Adversary 2: Wheat Market Cornerer
    adv2_code = apex_code.replace(
        'feed_buffer_days=2,',
        'feed_buffer_days=5,'
    ).replace(
        'to_buy = min(deficit, max_affordable, 15)',
        'to_buy = min(deficit, max_affordable, 30)'
    )
    with open(os.path.join(adv_dir, "adv2_wheat_cornerer.py"), "w", encoding="utf-8") as f:
        f.write(adv2_code)

    # Adversary 3: Micro-Batch Price Sinker
    adv3_code = apex_code.replace(
        'sell_batch=24,',
        'sell_batch=2,'
    ).replace(
        'if step % 4 == 0 or step >= 680:',
        'if True:'
    )
    with open(os.path.join(adv_dir, "adv3_price_sinker.py"), "w", encoding="utf-8") as f:
        f.write(adv3_code)

    # Adversary 4: Cow Juggernaut
    adv4_code = apex_code.replace(
        'target_cows=8,\n        target_sheep=4,',
        'target_cows=12,\n        target_sheep=4,'
    )
    with open(os.path.join(adv_dir, "adv4_cow_juggernaut.py"), "w", encoding="utf-8") as f:
        f.write(adv4_code)

def wilson_ci(wins, total, confidence=0.95):
    if total == 0: return 0.0, 0.0
    z = 1.95996
    p = wins / total
    denom = 1.0 + (z**2) / total
    center = (p + (z**2) / (2 * total)) / denom
    spread = (z / denom) * math.sqrt((p * (1.0 - p) / total) + ((z**2) / (4 * (total**2))))
    return max(0.0, center - spread) * 100.0, min(1.0, center + spread) * 100.0

def _run_single_match(item):
    a0_path, a1_path, seed, cand_is_p0 = item
    cfg = {"episodeSteps": 720, "seed": seed}
    env = make("kaggriculture", configuration=cfg, debug=False)
    
    t0 = time.time()
    try:
        env.run([a0_path, a1_path])
        elapsed = time.time() - t0
        last = env.steps[-1]
        r0 = float(last[0].reward or 0.0)
        r1 = float(last[1].reward or 0.0)
        
        if cand_is_p0:
            r_cand = r0
            r_opp = r1
        else:
            r_cand = r1
            r_opp = r0
            
        margin = r_cand - r_opp
        win = 1.0 if r_cand > r_opp else (0.0 if r_opp > r_cand else 0.5)
        return {
            "seed": seed, "cand_is_p0": cand_is_p0,
            "r_cand": r_cand, "r_opp": r_opp,
            "margin": margin, "win": win,
            "elapsed": elapsed, "error": None
        }
    except Exception as e:
        return {
            "seed": seed, "cand_is_p0": cand_is_p0,
            "r_cand": 0.0, "r_opp": 0.0,
            "margin": 0.0, "win": 0.0,
            "elapsed": 0.0, "error": str(e)
        }

def main():
    print("=" * 120, flush=True)
    print("PART 18: ADVERSARIAL STRESS TEST: ACTIVELY TRYING TO BREAK APEX V2", flush=True)
    print("=" * 120, flush=True)

    generate_adversaries()
    apex_path = os.path.join(project_root, "agents", "apex_v2_frozen.py")
    adversaries = [
        ("ADV 1: Predatory Early-Melon Frontrunner", os.path.join(adv_dir, "adv1_melon_predator.py")),
        ("ADV 2: Wheat Market Cornerer (Feed Hoarder)", os.path.join(adv_dir, "adv2_wheat_cornerer.py")),
        ("ADV 3: Micro-Batch Market Price Sinker (Dumping)", os.path.join(adv_dir, "adv3_price_sinker.py")),
        ("ADV 4: Cow Juggernaut (12 Cows / 4 Sheep)", os.path.join(adv_dir, "adv4_cow_juggernaut.py")),
    ]

    seeds = [50000 + i for i in range(50)]
    results = []

    with ProcessPoolExecutor(max_workers=6) as executor:
        for label, adv_path in adversaries:
            tasks = []
            for s in seeds:
                tasks.append((apex_path, adv_path, s, True))  # Apex as P0
                tasks.append((adv_path, apex_path, s, False)) # Apex as P1

            t_start = time.time()
            futures = [executor.submit(_run_single_match, t) for t in tasks]
            matches = [f.result() for f in futures]
            elapsed = time.time() - t_start

            p0_res = [r for r in matches if r["cand_is_p0"]]
            p1_res = [r for r in matches if not r["cand_is_p0"]]

            p0_wins = sum(1 for r in p0_res if r["win"] == 1.0)
            p1_wins = sum(1 for r in p1_res if r["win"] == 1.0)
            total_wins = p0_wins + p1_wins
            total_games = len(matches)

            p0_wr = (p0_wins / len(p0_res)) * 100.0 if p0_res else 0.0
            p1_wr = (p1_wins / len(p1_res)) * 100.0 if p1_res else 0.0
            pooled_wr = (total_wins / total_games) * 100.0 if total_games else 0.0
            w_low, w_high = wilson_ci(total_wins, total_games)

            margins = [r["margin"] for r in matches]
            cand_cash = [r["r_cand"] for r in matches]
            opp_cash = [r["r_opp"] for r in matches]

            mean_margin = float(np.mean(margins))
            median_margin = float(np.median(margins))
            mean_cand = float(np.mean(cand_cash))
            mean_opp = float(np.mean(opp_cash))
            worst = float(np.min(margins))

            print(f"{label:50s} | Apex WR: {pooled_wr:5.1f}% | CI: [{w_low:4.1f}%, {w_high:4.1f}%] | P0: {p0_wr:4.1f}% | P1: {p1_wr:4.1f}% | Margin: {mean_margin:+7.0f} | Apex: ${mean_cand:6,.0f} vs Adv: ${mean_opp:6,.0f} | Worst: ${worst:7,.0f} ({elapsed:.1f}s)", flush=True)

            results.append({
                "label": label, "adversary_file": os.path.basename(adv_path),
                "apex_wr": pooled_wr, "ci_95": [w_low, w_high],
                "p0_wr": p0_wr, "p1_wr": p1_wr,
                "mean_margin": mean_margin, "median_margin": median_margin,
                "mean_apex_cash": mean_cand, "mean_adv_cash": mean_opp,
                "worst_drawdown": worst, "elapsed_sec": elapsed
            })

    out_json = os.path.join(project_root, "scratch", "adversary_stress_results.json")
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nAdversary stress test results saved to: {out_json}", flush=True)

if __name__ == "__main__":
    main()
