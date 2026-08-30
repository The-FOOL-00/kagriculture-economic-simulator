import os, sys, math, json, multiprocessing, time
from collections import defaultdict
import kaggle_environments
from kaggle_environments import make

def run_single_match(args):
    agent0_path, agent1_path, seed, max_steps = args
    
    # Load agents dynamically
    import importlib.util
    
    def load_agent(p):
        spec = importlib.util.spec_from_file_location(f"mod_{os.path.basename(p).replace('.py','')}_{id(p)}", p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if hasattr(mod, 'agent'): return mod.agent
        if hasattr(mod, 'my_agent'): return mod.my_agent
        raise AttributeError(f"No agent found in {p}")
        
    a0 = load_agent(agent0_path)
    a1 = load_agent(agent1_path)
    
    env = make("kaggriculture", configuration={"episodeSteps": max_steps, "seed": seed}, debug=False)
    env.run([a0, a1])
    
    s0 = env.state[0]
    s1 = env.state[1]
    
    r0 = s0.reward if s0.reward is not None else 0
    r1 = s1.reward if s1.reward is not None else 0
    
    return {
        "seed": seed,
        "p0_path": agent0_path,
        "p1_path": agent1_path,
        "r0": r0,
        "r1": r1,
        "margin_01": r0 - r1,
        "winner": 0 if r0 > r1 else (1 if r1 > r0 else -1)
    }

def run_paired_tournament(cand_path, opp_path, seeds, max_steps=720, workers=None):
    if workers is None:
        workers = min(multiprocessing.cpu_count(), 16)
        
    tasks = []
    for s in seeds:
        tasks.append((cand_path, opp_path, s, max_steps))
        tasks.append((opp_path, cand_path, s, max_steps))
        
    with multiprocessing.Pool(workers) as pool:
        results = pool.map(run_single_match, tasks)
        
    p0_wins = 0
    p0_losses = 0
    p0_ties = 0
    p0_margins = []
    p0_cand_rewards = []
    p0_opp_rewards = []
    
    p1_wins = 0
    p1_losses = 0
    p1_ties = 0
    p1_margins = []
    p1_cand_rewards = []
    p1_opp_rewards = []
    
    for r in results:
        if r["p0_path"] == cand_path: # Cand was P0
            p0_cand_rewards.append(r["r0"])
            p0_opp_rewards.append(r["r1"])
            p0_margins.append(r["margin_01"])
            if r["winner"] == 0: p0_wins += 1
            elif r["winner"] == 1: p0_losses += 1
            else: p0_ties += 1
        else: # Cand was P1
            p1_cand_rewards.append(r["r1"])
            p1_opp_rewards.append(r["r0"])
            p1_margins.append(r["r1"] - r["r0"])
            if r["winner"] == 1: p1_wins += 1
            elif r["winner"] == 0: p1_losses += 1
            else: p1_ties += 1
            
    total_cand_wins = p0_wins + p1_wins
    total_cand_losses = p0_losses + p1_losses
    total_ties = p0_ties + p1_ties
    total_matches = len(results)
    
    pooled_wr = total_cand_wins / total_matches if total_matches > 0 else 0
    p0_wr = p0_wins / len(seeds) if len(seeds) > 0 else 0
    p1_wr = p1_wins / len(seeds) if len(seeds) > 0 else 0
    
    all_cand_rewards = p0_cand_rewards + p1_cand_rewards
    all_opp_rewards = p0_opp_rewards + p1_opp_rewards
    all_margins = p0_margins + p1_margins
    
    mean_cand_cash = sum(all_cand_rewards) / len(all_cand_rewards)
    mean_opp_cash = sum(all_opp_rewards) / len(all_opp_rewards)
    mean_margin = sum(all_margins) / len(all_margins)
    
    sorted_margins = sorted(all_margins)
    median_margin = sorted_margins[len(sorted_margins)//2]
    worst_loss = min(all_margins)
    worst_win = max(all_margins)
    
    # Wilson 95% CI
    z = 1.95996
    n = total_matches
    p = pooled_wr
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    spread = z * math.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denom
    ci_low = max(0.0, center - spread)
    ci_high = min(1.0, center + spread)
    
    return {
        "candidate": cand_path,
        "opponent": opp_path,
        "matches": total_matches,
        "seeds_count": len(seeds),
        "cand_wins": total_cand_wins,
        "cand_losses": total_cand_losses,
        "ties": total_ties,
        "pooled_wr": pooled_wr,
        "ci_95": [ci_low, ci_high],
        "p0_wr": p0_wr,
        "p1_wr": p1_wr,
        "mean_cand_cash": mean_cand_cash,
        "mean_opp_cash": mean_opp_cash,
        "mean_margin": mean_margin,
        "median_margin": median_margin,
        "worst_loss": worst_loss,
        "worst_win": worst_win
    }

if __name__ == '__main__':
    print("Testing master tournament runner on 2 seeds...")
    res = run_paired_tournament(
        r'c:\Users\Sundareswaran\Kagriculture\main.py',
        r'c:\Users\Sundareswaran\Kagriculture\agents\ground_truth_control_current_engine.py',
        [10000, 10001]
    )
    print("Test result:", json.dumps(res, indent=2))
