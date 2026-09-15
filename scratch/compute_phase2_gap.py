import json
import numpy as np

def compute_phase2_gap():
    with open("scratch/200seed_validation_raw.json") as f:
        data_ab = json.load(f)
    with open("scratch/v2_200seed_raw.json") as f:
        data_c = json.load(f)

    seeds = sorted([int(s) for s in data_ab["Baseline"].keys()])
    n_seeds = len(seeds)

    arms = {
        "CL": [data_ab["Baseline"][str(s)] for s in seeds],
        "M1": [data_ab["Gated_M1"][str(s)] for s in seeds],
        "V2": [data_c[str(s)] for s in seeds]
    }

    # Verify seed alignment
    assert len(arms["CL"]) == 200 and len(arms["M1"]) == 200 and len(arms["V2"]) == 200

    metrics = [
        ("Terminal Reward ($)", lambda x: x["reward"]),
        ("Strawberry Rev ($)", lambda x: x["straw_rev"]),
        ("Wool Rev ($)", lambda x: x["wool_rev"]),
        ("Milk Rev ($)", lambda x: x["milk_rev"]),
        ("Wheat Rev ($)", lambda x: x["wheat_rev"]),
        ("Melon Rev ($)", lambda x: x["melon_rev"]),
        ("Fertilizer Rev ($)", lambda x: x["fert_rev"]),
        ("Egg Rev ($)", lambda x: x["egg_rev"]),
        ("Total Gross Rev ($)", lambda x: x["total_rev"]),
        ("Total Expenditures ($)", lambda x: x["total_exp"]),
        ("Strawberry Sold (u)", lambda x: x["qty_sold"].get("STRAWBERRY", 0)),
        ("Wool Sold (u)", lambda x: x["qty_sold"].get("WOOL", 0)),
        ("Milk Sold (u)", lambda x: x["qty_sold"].get("MILK", 0)),
        ("Wheat Sold (u)", lambda x: x["qty_sold"].get("WHEAT", 0)),
        ("Melon Sold (u)", lambda x: x["qty_sold"].get("MELON", 0)),
        ("Fertilizer Sold (u)", lambda x: x["qty_sold"].get("FERTILIZER", 0)),
        ("Egg Sold (u)", lambda x: x["qty_sold"].get("EGG", 0)),
        ("Worker Movement Actions", lambda x: x["actions_count"].get("MOVE", 0)),
        ("Fertilize Actions", lambda x: x["actions_count"].get("FERTILIZE", 0)),
        ("Water Actions", lambda x: x["actions_count"].get("WATER", 0)),
        ("Feed Actions", lambda x: x["actions_count"].get("FEED", 0)),
        ("Care Actions", lambda x: x["actions_count"].get("CARE", 0)),
        ("Collect Fert Actions", lambda x: x["actions_count"].get("COLLECT_FERT", 0)),
        ("Worker Pass (Idle) Actions", lambda x: x["actions_count"].get("PASS", 0)),
    ]

    report = {}
    print("=" * 115)
    print(f"EXACT 200-SEED GAP ANALYSIS: CL BASELINE vs M1 GATED vs FROZEN V2 (N={n_seeds})")
    print("=" * 115)
    print(f"{'METRIC':<27} | {'CL BASELINE':<16} | {'M1 GATED':<16} | {'FROZEN V2':<16} | {'GAP (V2 - M1)':<16} | {'% GAP':<8}")
    print("-" * 115)

    for lbl, fn in metrics:
        vals_cl = np.array([fn(x) for x in arms["CL"]])
        vals_m1 = np.array([fn(x) for x in arms["M1"]])
        vals_v2 = np.array([fn(x) for x in arms["V2"]])

        m_cl, med_cl, s_cl = float(np.mean(vals_cl)), float(np.median(vals_cl)), float(np.std(vals_cl, ddof=1))
        m_m1, med_m1, s_m1 = float(np.mean(vals_m1)), float(np.median(vals_m1)), float(np.std(vals_m1, ddof=1))
        m_v2, med_v2, s_v2 = float(np.mean(vals_v2)), float(np.median(vals_v2)), float(np.std(vals_v2, ddof=1))

        diff_v2_m1 = m_v2 - m_m1
        pct_diff = (diff_v2_m1 / m_m1 * 100.0) if m_m1 != 0 else 0.0

        report[lbl] = {
            "CL": {"mean": m_cl, "median": med_cl, "std": s_cl},
            "M1": {"mean": m_m1, "median": med_m1, "std": s_m1},
            "V2": {"mean": m_v2, "median": med_v2, "std": s_v2},
            "gap_v2_m1": diff_v2_m1,
            "pct_gap": pct_diff
        }

        # formatting
        is_curr = "$" in lbl
        is_act = "Action" in lbl or "Movement" in lbl
        is_qty = "Sold (u)" in lbl

        if is_curr:
            fmt = lambda v: f"${v:>13,.2f}"
            gap_fmt = f"${diff_v2_m1:>+13,.2f}"
        elif is_qty:
            fmt = lambda v: f"{v:>14.2f}u"
            gap_fmt = f"{diff_v2_m1:>+14.2f}u"
        else:
            fmt = lambda v: f"{v:>14.1f}"
            gap_fmt = f"{diff_v2_m1:>+14.1f}"

        print(f"{lbl:<27} | {fmt(m_cl)} | {fmt(m_m1)} | {fmt(m_v2)} | {gap_fmt} | {pct_diff:>+7.1f}%")

    with open("scratch/exact_v2_vs_m1_gap_200seeds.json", "w") as f:
        json.dump(report, f, indent=2)

if __name__ == "__main__":
    compute_phase2_gap()
