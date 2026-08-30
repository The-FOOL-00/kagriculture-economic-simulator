import os, sys, time, json, hashlib
import numpy as np
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

def load_agent(path):
    import importlib.util
    mod_name = "mod_" + hashlib.md5(path.encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(mod_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, "agent", getattr(mod, "act", None))

def run_paired_match(agent_a_path, agent_b_path, seed, max_steps=720):
    # Run Game 1: A as P0, B as P1
    # We must instantiate fresh agents for each match to prevent state leakage
    agent_a1 = load_agent(agent_a_path)
    agent_b1 = load_agent(agent_b_path)
    env1 = make("kaggriculture", configuration={"episodeSteps": max_steps, "seed": seed}, debug=False)
    env1.run([agent_a1, agent_b1])
    r0_g1 = float(env1.steps[-1][0].reward or 0.0)
    r1_g1 = float(env1.steps[-1][1].reward or 0.0)

    # Run Game 2: B as P0, A as P1
    agent_a2 = load_agent(agent_a_path)
    agent_b2 = load_agent(agent_b_path)
    env2 = make("kaggriculture", configuration={"episodeSteps": max_steps, "seed": seed}, debug=False)
    env2.run([agent_b2, agent_a2])
    r0_g2 = float(env2.steps[-1][0].reward or 0.0) # B
    r1_g2 = float(env2.steps[-1][1].reward or 0.0) # A

    return {
        "seed": seed,
        "g1_p0_a": r0_g1,
        "g1_p1_b": r1_g1,
        "g2_p0_b": r0_g2,
        "g2_p1_a": r1_g2,
    }

def run_tournament_pairing(name_a, path_a, name_b, path_b, seeds):
    hash_a = get_hash(path_a)
    hash_b = get_hash(path_b)
    print(f"\n--- PAIRING: {name_a} vs {name_b} ---")
    print(f"  Agent A ({name_a}): {path_a} (sha256: {hash_a[:12]}...)")
    print(f"  Agent B ({name_b}): {path_b} (sha256: {hash_b[:12]}...)")
    print(f"  Running {len(seeds)} paired seeds ({2 * len(seeds)} total games)...")
    
    t0 = time.time()
    results = []
    for s in seeds:
        res = run_paired_match(path_a, path_b, s)
        results.append(res)
        
    elapsed = time.time() - t0
    
    # Process stats
    p0_wins = 0 # A as P0
    p1_wins = 0 # A as P1
    total_wins = 0
    cash_a = []
    cash_b = []
    margins = []
    
    for r in results:
        # G1: A as P0
        ca_1 = r["g1_p0_a"]
        cb_1 = r["g1_p1_b"]
        cash_a.append(ca_1)
        cash_b.append(cb_1)
        m1 = ca_1 - cb_1
        margins.append(m1)
        w1 = 1.0 if ca_1 > cb_1 else (0.5 if ca_1 == cb_1 else 0.0)
        p0_wins += w1
        total_wins += w1
        
        # G2: A as P1
        ca_2 = r["g2_p1_a"]
        cb_2 = r["g2_p0_b"]
        cash_a.append(ca_2)
        cash_b.append(cb_2)
        m2 = ca_2 - cb_2
        margins.append(m2)
        w2 = 1.0 if ca_2 > cb_2 else (0.5 if ca_2 == cb_2 else 0.0)
        p1_wins += w2
        total_wins += w2
        
    total_games = 2 * len(seeds)
    p0_wr = (p0_wins / len(seeds)) * 100.0
    p1_wr = (p1_wins / len(seeds)) * 100.0
    pooled_wr = (total_wins / total_games) * 100.0
    low_ci, upp_ci = wilson_score_interval(total_wins, total_games)
    mean_margin = float(np.mean(margins))
    mean_cash_a = float(np.mean(cash_a))
    mean_cash_b = float(np.mean(cash_b))
    
    print(f"  Results across {total_games} games ({elapsed:.1f}s):")
    print(f"    P0 WR (A as P0): {p0_wr:5.1f}% ({p0_wins}/{len(seeds)})")
    print(f"    P1 WR (A as P1): {p1_wr:5.1f}% ({p1_wins}/{len(seeds)})")
    print(f"    Pooled WR:       {pooled_wr:5.1f}% ({total_wins}/{total_games}) | 95% CI: [{low_ci:.1f}%, {upp_ci:.1f}%]")
    print(f"    Mean Cash A:     ${mean_cash_a:8,.2f}")
    print(f"    Mean Cash B:     ${mean_cash_b:8,.2f}")
    print(f"    Net Margin:      ${mean_margin:+8,.2f}")
    print(f"    Worst Loss:      ${np.min(margins):+8,.2f}")
    
    return {
        "agent_a": {"name": name_a, "path": path_a, "sha256": hash_a},
        "agent_b": {"name": name_b, "path": path_b, "sha256": hash_b},
        "num_paired_seeds": len(seeds),
        "total_games": total_games,
        "p0_wr": p0_wr,
        "p1_wr": p1_wr,
        "pooled_wr": pooled_wr,
        "ci_95": [low_ci, upp_ci],
        "mean_cash_a": mean_cash_a,
        "mean_cash_b": mean_cash_b,
        "mean_margin": mean_margin,
        "worst_loss": float(np.min(margins)),
        "elapsed_seconds": elapsed,
        "match_details": results
    }

if __name__ == "__main__":
    print("Forensic Harness Initialized.")
