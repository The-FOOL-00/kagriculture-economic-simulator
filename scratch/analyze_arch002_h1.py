"""
EXP-ARCH-002 H1 Statistical and Forensic Analysis Script
Strictly adheres to 02_PREREGISTRATION.md §15-§22.
"""
import os
import json
import math
import numpy as np
from scipy import stats

RAW_RESULTS_FILE = r"experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/RAW_RESULTS.json"

def clopper_pearson(k, n, alpha=0.05):
    """Exact Clopper-Pearson binomial confidence interval."""
    if k == 0:
        low = 0.0
    else:
        low = stats.beta.ppf(alpha / 2, k, n - k + 1)
    if k == n:
        high = 1.0
    else:
        high = stats.beta.ppf(1 - alpha / 2, k + 1, n - k)
    return low, high

def main():
    if not os.path.exists(RAW_RESULTS_FILE):
        print(f"File not found: {RAW_RESULTS_FILE}")
        return

    with open(RAW_RESULTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    seeds_data = data.get("seeds", [])
    n_seeds = len(seeds_data)
    print("=" * 80)
    print(f"EXP-ARCH-002 H1 — FULL AUDIT & STATISTICAL ANALYSIS (N={n_seeds} seeds)")
    print("=" * 80)

    # 1. INTEGRITY AUDIT
    seeds = [s["seed"] for s in seeds_data]
    unique_seeds = set(seeds)
    expected_seeds = set(range(320000, 320500))

    dup_count = len(seeds) - len(unique_seeds)
    missing = expected_seeds - unique_seeds
    unauthorized = unique_seeds - expected_seeds
    dev007_overlap = unique_seeds.intersection(set(range(310000, 310500)))
    holdout_overlap = unique_seeds.intersection(set(range(214200, 214250)))

    print("\n--- 1. INTEGRITY & QUARANTINE AUDIT ---")
    print(f"Authorized Cohort: [320000, 320499] (N=500)")
    print(f"Executed Seeds: {n_seeds}")
    print(f"Unique Seeds: {len(unique_seeds)}")
    print(f"Duplicate Seeds: {dup_count}")
    print(f"Missing Seeds: {len(missing)}")
    print(f"Unauthorized Seeds: {len(unauthorized)}")
    print(f"DEV-007 Overlap: {len(dev007_overlap)} (Must be 0)")
    print(f"Final Holdout Overlap: {len(holdout_overlap)} (Must be 0)")

    # Purity checks across all games
    all_games = []
    for s in seeds_data:
        all_games.append(s["game_a"])
        all_games.append(s["game_b"])

    n_games = len(all_games)
    print(f"Total Games Executed: {n_games} (Expected: {n_seeds * 2})")

    pure_pre_e_all = all(g.get("pure_pre_e_pass", False) for g in all_games)
    pure_verbatim_all = all(g.get("pure_verbatim_pass", False) for g in all_games if g.get("activated", False))
    pure_step_all = all(g.get("pure_step_pass", False) for g in all_games)

    print(f"P-PURE Pre-E Action Bit-Identity (0 to 711): {'PASS (100%)' if pure_pre_e_all else 'FAIL'}")
    print(f"P-PURE Step-718/Window Verbatim Markets: {'PASS (100%)' if pure_verbatim_all else 'FAIL'}")
    print(f"P-PURE Non-Activated Step Purity (Delta==0): {'PASS (100%)' if pure_step_all else 'FAIL'}")

    # 2. PAIRED PERFORMANCE (ESTIMAND 1)
    deltas = np.array([s["delta_paired"] for s in seeds_data], dtype=float)
    h1_scores_a = np.array([s["h1_score_a"] for s in seeds_data], dtype=float)
    base_scores_a = np.array([s["base_score_a"] for s in seeds_data], dtype=float)
    h1_scores_b = np.array([s["h1_score_b"] for s in seeds_data], dtype=float)
    base_scores_b = np.array([s["base_score_b"] for s in seeds_data], dtype=float)

    h1_all_scores = np.concatenate([h1_scores_a, h1_scores_b])
    base_all_scores = np.concatenate([base_scores_a, base_scores_b])

    mean_delta = np.mean(deltas)
    median_delta = np.median(deltas)
    sd_delta = np.std(deltas, ddof=1)
    se_delta = sd_delta / math.sqrt(n_seeds)

    t_stat = mean_delta / se_delta if se_delta > 0 else 0.0
    p_val_2sided = 2.0 * stats.t.sf(abs(t_stat), df=n_seeds - 1)
    t_crit = stats.t.ppf(0.975, df=n_seeds - 1)
    ci_lo = mean_delta - t_crit * se_delta
    ci_hi = mean_delta + t_crit * se_delta

    trimmed_mean_10 = stats.trim_mean(deltas, 0.10)

    # Percentiles using linear interpolation
    pcts = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    pct_vals = np.percentile(deltas, pcts, method="linear")

    wins = int(np.sum(deltas > 0))
    losses = int(np.sum(deltas < 0))
    ties = int(np.sum(deltas == 0))
    nonzero = wins + losses

    win_rate = wins / n_seeds
    loss_rate = losses / n_seeds
    tie_rate = ties / n_seeds

    min_delta = float(np.min(deltas))
    max_delta = float(np.max(deltas))

    # Robustness views
    sorted_deltas = np.sort(deltas)
    mean_ex_best = np.mean(sorted_deltas[:-1]) if n_seeds > 1 else mean_delta
    mean_ex_top2 = np.mean(sorted_deltas[:-2]) if n_seeds > 2 else mean_delta

    print("\n--- 2. PRIMARY ESTIMAND: UNCONDITIONAL PAIRED DELTA (H1 - Baseline) ---")
    print(f"Mean Delta (Delta_bar):   {mean_delta:+.4f}")
    print(f"Median Delta:             {median_delta:+.4f}")
    print(f"Sample SD (ddof=1):       {sd_delta:.4f}")
    print(f"Standard Error (SE):      {se_delta:.4f}")
    print(f"t-statistic (df={n_seeds-1}):     {t_stat:+.4f}")
    print(f"Two-sided p-value:        {p_val_2sided:.6e}")
    print(f"95% Confidence Interval:  [{ci_lo:+.4f}, {ci_hi:+.4f}]")
    print(f"10% Trimmed Mean:         {trimmed_mean_10:+.4f}")
    print(f"Min / Max Delta:          {min_delta:+.2f} / {max_delta:+.2f}")
    print(f"Wins / Losses / Ties:     {wins} ({win_rate*100:.2f}%) / {losses} ({loss_rate*100:.2f}%) / {ties} ({tie_rate*100:.2f}%)")
    print(f"Nonzero Count:            {nonzero} ({nonzero/n_seeds*100:.2f}%)")
    print(f"Mean ex-best:             {mean_ex_best:+.4f}")
    print(f"Mean ex-top2:             {mean_ex_top2:+.4f}")

    print("\nPercentiles (linear):")
    for p, val in zip(pcts, pct_vals):
        print(f"  p{p:02d}: {val:+.2f}")

    print("\nAggregate Absolute Scores (Coins):")
    print(f"  H1 Mean Score:       {np.mean(h1_all_scores):.2f} (SD={np.std(h1_all_scores, ddof=1):.2f})")
    print(f"  Baseline Mean Score: {np.mean(base_all_scores):.2f} (SD={np.std(base_all_scores, ddof=1):.2f})")

    # 3. TAIL-HARM & EXCURSION CENSUS
    large_excursions = [s for s in seeds_data if abs(s["delta_paired"]) >= 2000.0]
    tail_harm_violated = (min_delta < -800.0)

    print("\n--- 3. TAIL-RISK & HARM AUDIT ---")
    print(f"Loss Rate: {loss_rate*100:.2f}% (Threshold: <= 5.00%)")
    print(f"Minimum Paired Delta: {min_delta:+.2f} (Threshold: >= -$800.00)")
    print(f"Tail-Harm Bar (< -$800.00): {'VIOLATED' if tail_harm_violated else 'SATISFIED'}")
    print(f"Large Excursions (|Delta| >= $2000): {len(large_excursions)}")

    # 4. MECHANISM EXPOSURE & CONDITIONAL CONTRAST
    exposed_seeds = [s for s in seeds_data if s["exposed"]]
    k_exposed = len(exposed_seeds)
    p_act = k_exposed / n_seeds
    cp_lo, cp_hi = clopper_pearson(k_exposed, n_seeds)

    activated_games = [g for g in all_games if g.get("activated", False)]
    n_activated_games = len(activated_games)

    print("\n--- 4. MECHANISM EXPOSURE ENDPOINTS ---")
    print(f"Activated Games: {n_activated_games}/{n_games} ({n_activated_games/n_games*100:.2f}%)")
    print(f"Exposed Seeds (k): {k_exposed}/{n_seeds} ({p_act*100:.2f}%)")
    print(f"Exact Clopper-Pearson 95% CI on Exposure: [{cp_lo*100:.2f}%, {cp_hi*100:.2f}%]")

    # Reason code histogram across all 1000 games
    reasons = {}
    for g in all_games:
        r = g.get("reason", "UNKNOWN")
        reasons[r] = reasons.get(r, 0) + 1

    print("\nReason Code Histogram (N=1000 games):")
    for r, count in sorted(reasons.items(), key=lambda x: -x[1]):
        print(f"  {r:35s}: {count:4d} ({count/n_games*100:.2f}%)")

    # Conditional Contrast on Exposed Seeds
    if k_exposed > 0:
        cond_deltas = np.array([s["delta_paired"] for s in exposed_seeds], dtype=float)
        cond_mean = np.mean(cond_deltas)
        cond_median = np.median(cond_deltas)
        cond_sd = np.std(cond_deltas, ddof=1) if k_exposed > 1 else 0.0
        cond_se = cond_sd / math.sqrt(k_exposed) if k_exposed > 1 else 0.0
        cond_min = float(np.min(cond_deltas))
        cond_max = float(np.max(cond_deltas))
        cond_wins = int(np.sum(cond_deltas > 0))
        cond_losses = int(np.sum(cond_deltas < 0))
        cond_ties = int(np.sum(cond_deltas == 0))
        exposed_harm_count = cond_losses

        if k_exposed > 1 and cond_se > 0:
            cond_t_crit = stats.t.ppf(0.975, df=k_exposed - 1)
            cond_ci = [cond_mean - cond_t_crit * cond_se, cond_mean + cond_t_crit * cond_se]
        else:
            cond_ci = [cond_mean, cond_mean]

        print("\nConditional Contrast (k exposed seeds only):")
        print(f"  Mean Conditional Delta:   {cond_mean:+.4f}")
        print(f"  Median Conditional Delta: {cond_median:+.4f}")
        print(f"  SD / SE:                  {cond_sd:.4f} / {cond_se:.4f}")
        print(f"  95% CI (Student-t):       [{cond_ci[0]:+.4f}, {cond_ci[1]:+.4f}]")
        print(f"  Min / Max:                {cond_min:+.2f} / {cond_max:+.2f}")
        print(f"  Wins / Losses / Ties:     {cond_wins} / {cond_losses} / {cond_ties}")
        print(f"  Exposed-Seed Harm Count:  {exposed_harm_count}")
    else:
        print("\nConditional Contrast: k=0 (Mechanism unexposed)")
        cond_mean = 0.0
        exposed_harm_count = 0

    # 5. SEARCH & OVERLAY TELEMETRY (for activated games)
    if activated_games:
        sims = [g["simulations"] for g in activated_games if g.get("simulations") is not None]
        ms = [g["planning_ms"] for g in activated_games if g.get("planning_ms") is not None]
        workers_changed = [len(g.get("changed_workers", [])) for g in activated_games]
        gains = [g["stock_value_gain"] for g in activated_games if g.get("stock_value_gain") is not None]
        fert_reaped = [g["fertilizer_reaped"] for g in activated_games if g.get("fertilizer_reaped") is not None]

        print("\n--- 5. SEARCH & OVERLAY TELEMETRY (Activated Games) ---")
        print(f"  Mean Simulations Evaluated: {np.mean(sims):.2f} (Max: {np.max(sims)})")
        print(f"  Mean Planning Time:         {np.mean(ms):.2f} ms (Max: {np.max(ms):.2f} ms)")
        print(f"  Mean Workers Modified:      {np.mean(workers_changed):.2f} (Max: {np.max(workers_changed)})")
        print(f"  Mean Modeled Stock Gain:    {np.mean(gains):+.2f}")
        print(f"  Total Fertilizer Units Reaped: {sum(fert_reaped)}")

    # 6. ROUTE DISTRIBUTIONS
    routes = {}
    for g in all_games:
        rt = g.get("route", "unknown")
        routes[rt] = routes.get(rt, 0) + 1

    print("\nRoute Distribution (N=1000 games):")
    for rt, cnt in sorted(routes.items(), key=lambda x: -x[1]):
        print(f"  {rt:20s}: {cnt:4d} ({cnt/n_games*100:.2f}%)")

    # 7. OUTLIER FORENSICS (Top 5 Positive, Top 5 Negative)
    sorted_by_delta = sorted(seeds_data, key=lambda s: s["delta_paired"])
    worst_5 = sorted_by_delta[:5]
    best_5 = sorted_by_delta[-5:][::-1]

    print("\n--- 6. OUTLIER CENSUS ---")
    print("Top 5 Positive Seeds (Largest Gains):")
    for s in best_5:
        print(f"  Seed {s['seed']}: Delta={s['delta_paired']:+8.2f} (a: {s['delta_a']:+8.2f}, b: {s['delta_b']:+8.2f}) | "
              f"Exp={s['exposed']} | Act_a={s['activated_a']} ({s['reason_a']}) | Act_b={s['activated_b']} ({s['reason_b']}) | Routes: {s['route_a']}/{s['route_b']}")

    print("\nTop 5 Negative Seeds (Largest Losses):")
    for s in worst_5:
        print(f"  Seed {s['seed']}: Delta={s['delta_paired']:+8.2f} (a: {s['delta_a']:+8.2f}, b: {s['delta_b']:+8.2f}) | "
              f"Exp={s['exposed']} | Act_a={s['activated_a']} ({s['reason_a']}) | Act_b={s['activated_b']} ({s['reason_b']}) | Routes: {s['route_a']}/{s['route_b']}")

    # 8. PREREGISTERED DECISION EVALUATION (§21)
    print("\n" + "=" * 80)
    print("--- 7. PREREGISTERED DECISION EVALUATION (§21) ---")
    print("=" * 80)

    # Mechanism Pattern
    if k_exposed <= 2:
        mech_pattern = "C"
        mech_desc = "C. mechanism untestable (k <= 2)"
    elif cond_mean > 0 and exposed_harm_count == 0 and min_delta >= 0:
        mech_pattern = "A"
        mech_desc = "A. mechanism supported (k >= 3, cond_mean > 0, zero exposed harm, min >= 0)"
    else:
        mech_pattern = "B"
        mech_desc = f"B. mechanism weakened (k={k_exposed} >= 3, cond_mean={cond_mean:+.2f}, exposed_harm={exposed_harm_count}, min_delta={min_delta:+.2f})"

    # Overall Pattern
    if p_val_2sided < 0.05 and mean_delta > 0 and min_delta >= -800.0:
        overall_pattern = "D"
        overall_desc = "D. overall improved (p < 0.05, mean > 0, min >= -$800)"
    elif (p_val_2sided < 0.05 and mean_delta < 0) or (min_delta < -800.0):
        overall_pattern = "F"
        overall_desc = f"F. overall harmed (p={p_val_2sided:.4f}, mean={mean_delta:+.2f}, min={min_delta:+.2f} < -$800)"
    else:
        overall_pattern = "E"
        overall_desc = f"E. overall neutral (mean={mean_delta:+.2f}, p={p_val_2sided:.4f}, min={min_delta:+.2f})"

    combined_pair = f"{mech_pattern} + {overall_pattern}"
    print(f"\nMechanism Pattern: {mech_desc}")
    print(f"Overall Pattern:   {overall_desc}")
    print(f"Combined Result Pair: **{combined_pair}**")

    # Scientific Success
    sci_success = (mech_pattern == "A")
    print(f"\nSCIENTIFIC SUCCESS GATE (Pattern A): {'PASS' if sci_success else 'FAIL'}")

    # Competitive Success
    comp_mean_ok = (mean_delta >= 500.0)
    comp_ci_ok = (ci_lo > 0.0)
    comp_min_ok = (min_delta >= -800.0)
    comp_loss_ok = (loss_rate <= 0.05)
    comp_success = sci_success and comp_mean_ok and comp_ci_ok and comp_min_ok and comp_loss_ok

    print("\nCOMPETITIVE SUCCESS GATE:")
    print(f"  - Scientific Success (Pattern A):       {'PASS' if sci_success else 'FAIL'}")
    print(f"  - Mean Delta >= +$500:                  {'PASS' if comp_mean_ok else 'FAIL'} ({mean_delta:+.2f})")
    print(f"  - Lower 95% CI > $0:                    {'PASS' if comp_ci_ok else 'FAIL'} ({ci_lo:+.2f})")
    print(f"  - Minimum Delta >= -$800:               {'PASS' if comp_min_ok else 'FAIL'} ({min_delta:+.2f})")
    print(f"  - Loss Rate <= 5%:                      {'PASS' if comp_loss_ok else 'FAIL'} ({loss_rate*100:.2f}%)")
    print(f"COMPETITIVE SUCCESS OVERALL:             {'PASS' if comp_success else 'FAIL'}")
    print("=" * 80)

if __name__ == "__main__":
    main()
