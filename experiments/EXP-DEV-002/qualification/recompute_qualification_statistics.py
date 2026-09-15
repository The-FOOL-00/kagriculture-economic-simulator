"""
=============================================================================
EXP-DEV-002 INDEPENDENT QUALIFICATION STATISTICAL RECOMPUTATION SCRIPT
=============================================================================
Authoritative standalone verification script. Recomputes all primary, secondary,
quantile, and tail statistics directly from raw paired observations.
=============================================================================
"""

import json
import csv
import math
import os
import sys

QUAL_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_JSON = os.path.join(QUAL_DIR, "QUALIFICATION_RAW_RESULTS.json")
CSV_PATH = os.path.join(QUAL_DIR, "QUALIFICATION_PAIRED_DELTAS.csv")

def run_recomputation():
    assert os.path.exists(RAW_JSON), f"Raw JSON missing: {RAW_JSON}"
    assert os.path.exists(CSV_PATH), f"CSV missing: {CSV_PATH}"

    with open(RAW_JSON, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # 1. Parse CSV
    rows = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    assert len(rows) == 50, f"Expected 50 seeds, got {len(rows)}"

    seeds = [int(r["seed"]) for r in rows]
    deltas_v2 = [float(r["paired_margin_vs_v2"]) for r in rows]
    deltas_dmi = [float(r["paired_margin_vs_dmi"]) for r in rows]
    deltas_dev001 = [float(r["dev001_paired_margin_vs_v2"]) for r in rows]

    # Verify seed sequence
    assert seeds == list(range(50050, 50100)), "Seed sequence does not match 50050..50099"

    # Cross-check JSON vs CSV
    json_v2_deltas = [r["paired_margin"] for r in raw["results_vs_v2"]]
    assert deltas_v2 == json_v2_deltas, "JSON vs CSV deltas mismatch"

    n = len(deltas_v2)
    mean = sum(deltas_v2) / n
    sorted_d = sorted(deltas_v2)
    median = sorted_d[n // 2] if n % 2 == 1 else (sorted_d[n // 2 - 1] + sorted_d[n // 2]) / 2.0
    var = sum((x - mean) ** 2 for x in deltas_v2) / (n - 1)
    sd = math.sqrt(var)
    se = sd / math.sqrt(n)
    t_stat = mean / se if se > 0 else 0.0

    t_crit = 2.009575  # df = 49 for two-sided alpha=0.05
    ci_lower = mean - t_crit * se
    ci_upper = mean + t_crit * se

    z = abs(t_stat)
    p_val = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(z / math.sqrt(2.0))))

    trim_k = int(0.10 * n)
    trimmed_data = sorted_d[trim_k : n - trim_k]
    trimmed_mean = sum(trimmed_data) / len(trimmed_data)

    def q(p):
        idx = p * (n - 1)
        low = int(math.floor(idx))
        high = int(math.ceil(idx))
        w = idx - low
        return sorted_d[low] * (1.0 - w) + sorted_d[high] * w

    wins = sum(1 for x in deltas_v2 if x > 0)
    losses = sum(1 for x in deltas_v2 if x < 0)
    ties = sum(1 for x in deltas_v2 if x == 0)

    total_surplus = sum(deltas_v2)
    top1 = sorted_d[-1]
    top2 = sorted_d[-2] + sorted_d[-1]

    stats = {
        "n": n,
        "mean": mean,
        "median": median,
        "trimmed_mean_10": trimmed_mean,
        "sd": sd,
        "se": se,
        "t_stat": t_stat,
        "p_value": p_val,
        "ci_95": [ci_lower, ci_upper],
        "min": sorted_d[0],
        "max": sorted_d[-1],
        "p01": q(0.01),
        "p05": q(0.05),
        "p10": q(0.10),
        "p25": q(0.25),
        "p50": q(0.50),
        "p75": q(0.75),
        "p90": q(0.90),
        "p95": q(0.95),
        "p99": q(0.99),
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "win_rate_pct": wins / n * 100.0,
        "loss_rate_pct": losses / n * 100.0,
        "tie_rate_pct": ties / n * 100.0,
        "downside_frequency_pct": losses / n * 100.0,
        "total_surplus": total_surplus,
        "top1_contribution_pct": (top1 / total_surplus * 100.0) if total_surplus > 0 else 0.0,
        "top2_contribution_pct": (top2 / total_surplus * 100.0) if total_surplus > 0 else 0.0,
        "mean_ex_best": sum(sorted_d[:-1]) / (n - 1),
        "mean_ex_worst": sum(sorted_d[1:]) / (n - 1),
        "mean_ex_top2": sum(sorted_d[:-2]) / (n - 2),
    }

    out_path = os.path.join(QUAL_DIR, "QUALIFICATION_STATISTICS_RECOMPUTED.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    print(f"Recomputed statistics written to: {out_path}")
    return stats

if __name__ == "__main__":
    s = run_recomputation()
    print(json.dumps(s, indent=2))
