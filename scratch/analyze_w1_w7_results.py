import json
import numpy as np
from scipy import stats
from collections import defaultdict

with open("scratch/counterfactual_matrix_100seeds_results.json") as f:
    data = json.load(f)

detailed = data["detailed"]
agents = list(detailed.keys())
seeds = sorted([int(s) for s in detailed["M1_Baseline"].keys()])

def compute_bootstrap_ci(diffs, n_boot=2000, ci=0.95):
    boot_means = [np.mean(np.random.choice(diffs, size=len(diffs), replace=True)) for _ in range(n_boot)]
    alpha = (1 - ci) / 2
    return float(np.percentile(boot_means, alpha * 100)), float(np.percentile(boot_means, (1 - alpha) * 100))

m1_rews = np.array([detailed["M1_Baseline"][str(s)]["reward"] for s in seeds])
q50_rews = np.array([detailed["Raw_Q50"][str(s)]["reward"] for s in seeds])

print("===================================================================================================")
print("PHASE 4: FULL STATISTICAL REPORT FOR W1-W7 COUNTERFACTUAL MATRIX (N=100)")
print("===================================================================================================")

for ag in agents:
    rews = np.array([detailed[ag][str(s)]["reward"] for s in seeds])
    m_rew = float(np.mean(rews))
    med_rew = float(np.median(rews))
    sd_rew = float(np.std(rews))

    # Vs M1
    diff_m1 = rews - m1_rews
    del_m1 = float(np.mean(diff_m1))
    ci_m1 = compute_bootstrap_ci(diff_m1)
    t_m1, p_t_m1 = stats.ttest_rel(rews, m1_rews)
    w_m1, p_w_m1 = stats.wilcoxon(rews, m1_rews) if np.any(diff_m1 != 0) else (0, 1.0)
    win_m1 = float(np.sum(diff_m1 > 0) / len(seeds) * 100)

    # Vs Q50
    diff_q50 = rews - q50_rews
    del_q50 = float(np.mean(diff_q50))
    ci_q50 = compute_bootstrap_ci(diff_q50)
    t_q50, p_t_q50 = stats.ttest_rel(rews, q50_rews)
    w_q50, p_w_q50 = stats.wilcoxon(rews, q50_rews) if np.any(diff_q50 != 0) else (0, 1.0)
    win_q50 = float(np.sum(diff_q50 > 0) / len(seeds) * 100)

    # Commodities
    straw = np.mean([detailed[ag][str(s)]["sold_qty"].get("STRAWBERRY", 0) for s in seeds])
    wheat = np.mean([detailed[ag][str(s)]["sold_qty"].get("WHEAT", 0) for s in seeds])
    milk = np.mean([detailed[ag][str(s)]["sold_qty"].get("MILK", 0) for s in seeds])
    wool = np.mean([detailed[ag][str(s)]["sold_qty"].get("WOOL", 0) for s in seeds])

    print(f"\n--- {ag} ---")
    print(f"  Reward: Mean=${m_rew:,.2f} | Median=${med_rew:,.2f} | SD=${sd_rew:,.2f}")
    print(f"  Vs M1:  Delta=${del_m1:+,.2f} | 95% CI=[${ci_m1[0]:+,.1f}, ${ci_m1[1]:+,.1f}] | Win={win_m1:.1f}% | p(t)={p_t_m1:.4f} | p(W)={p_w_m1:.4f}")
    print(f"  Vs Q50: Delta=${del_q50:+,.2f} | 95% CI=[${ci_q50[0]:+,.1f}, ${ci_q50[1]:+,.1f}] | Win={win_q50:.1f}% | p(t)={p_t_q50:.4f} | p(W)={p_w_q50:.4f}")
    print(f"  Commodities Sold: Straw={straw:.2f} | Wheat={wheat:.2f} | Milk={milk:.2f} | Wool={wool:.2f}")

    sorted_diff_q50 = sorted([(s, float(diff_q50[i])) for i, s in enumerate(seeds)], key=lambda x: x[1])
    worst_10 = sorted_diff_q50[:10]
    best_10 = sorted_diff_q50[-10:]
    print(f"  Worst 5 seeds vs Q50: {worst_10[:5]}")
    print(f"  Best 5 seeds vs Q50:  {best_10[-5:]}")
