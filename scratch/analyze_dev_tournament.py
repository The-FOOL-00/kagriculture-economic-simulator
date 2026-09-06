import json
import numpy as np
import scipy.stats as stats

with open("scratch/jit_melon_results/dev_tournament_results.json", "r") as f:
    data = json.load(f)

# Split data into H vs V2 and A (V2 control) vs V2
h_games = [r for r in data if r["treatment"] == "H"]
a_games = [r for r in data if r["treatment"] == "A"]

print(f"Total H games: {len(h_games)}")
print(f"Total A games: {len(a_games)}")

def analyze_suite(games, label):
    rewards = [g["reward_us"] for g in games]
    opp_rewards = [g["reward_opp"] for g in games]
    margins = [g["margin"] for g in games]
    wins = [g["win"] for g in games]
    starvations = [g["starvation_events"] for g in games]
    min_feeds = [g["min_feed_seen"] for g in games]
    
    # Paired stats
    mean_score = np.mean(rewards)
    mean_opp_score = np.mean(opp_rewards)
    mean_margin = np.mean(margins)
    median_margin = np.median(margins)
    std_margin = np.std(margins, ddof=1)
    sem_margin = stats.sem(margins)
    ci95 = stats.t.interval(0.95, len(margins)-1, loc=mean_margin, scale=sem_margin)
    t_stat, p_val = stats.ttest_1samp(margins, 0.0)
    
    win_rate = np.mean(wins) * 100.0
    p5_margin = np.percentile(margins, 5)
    worst_loss = np.min(margins)
    best_win = np.max(margins)
    catastrophic_losses = sum(1 for m in margins if m < -20000) / len(margins) * 100.0
    
    # Seat breakdown
    s0_games = [g for g in games if not g["swapped"]]
    s1_games = [g for g in games if g["swapped"]]
    s0_wr = np.mean([g["win"] for g in s0_games]) * 100.0
    s1_wr = np.mean([g["win"] for g in s1_games]) * 100.0
    s0_margin = np.mean([g["margin"] for g in s0_games])
    s1_margin = np.mean([g["margin"] for g in s1_games])
    
    print(f"\n=======================================================")
    print(f"RESULTS FOR: {label} (N={len(games)} games)")
    print(f"=======================================================")
    print(f"Mean Score:            ${mean_score:,.1f}")
    print(f"Opponent Mean Score:   ${mean_opp_score:,.1f}")
    print(f"Mean Margin:           ${mean_margin:+,.1f}")
    print(f"Median Margin:         ${median_margin:+,.1f}")
    print(f"Win Rate:              {win_rate:.2f}% (Seat 0: {s0_wr:.1f}%, Seat 1: {s1_wr:.1f}%)")
    print(f"Seat 0 Margin:         ${s0_margin:+,.1f}")
    print(f"Seat 1 Margin:         ${s1_margin:+,.1f}")
    print(f"Std Deviation:         ${std_margin:,.1f}")
    print(f"95% Confidence Int:    [${ci95[0]:+,.1f}, ${ci95[1]:+,.1f}]")
    print(f"t-statistic:           {t_stat:.3f}")
    print(f"p-value:               {p_val:.4e}")
    print(f"5th Percentile Margin: ${p5_margin:+,.1f}")
    print(f"Worst Loss:            ${worst_loss:+,.1f}")
    print(f"Best Win:              ${best_win:+,.1f}")
    print(f"Catastrophic Loss (< -20k): {catastrophic_losses:.2f}%")
    print(f"Starvation Events:     {sum(starvations)} (Mean: {np.mean(starvations):.2f})")
    print(f"Min Feed Inventory:    {np.min(min_feeds)}")

analyze_suite(h_games, "TREATMENT H (Day-0 JIT Melon Pipeline)")
analyze_suite(a_games, "TREATMENT A (Frozen V2 Control Self-Play)")
