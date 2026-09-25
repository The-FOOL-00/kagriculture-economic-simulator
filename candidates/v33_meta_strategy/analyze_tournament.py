# SPDX-License-Identifier: MIT
"""Analyze tournament results from route_matchup_matrix.json."""

from __future__ import annotations
import json
import numpy as np


def main():
    with open("route_matchup_matrix.json", "r", encoding="utf-8") as f:
        d = json.load(f)

    routes = d["routes"]
    matrix = d["matrix"]

    print("=================== PAIRWISE WIN-LOSS RECORD (Row vs Col) ===================")
    header = f"{'Route':<12}" + "".join([f"{r:<14}" for r in routes]) + f"{'Overall W-L-T':<16}{'WinRate':<10}"
    print(header)
    print("-" * len(header))

    overall_stats = {}

    for r1 in routes:
        row_str = f"{r1:<12}"
        tot_w, tot_l, tot_t = 0, 0, 0
        cash_deltas = []
        for r2 in routes:
            if r1 == r2:
                row_str += f"{'--':<14}"
            else:
                cell = matrix[r1][r2]
                w, l, t = cell["wins"], cell["losses"], cell["ties"]
                tot_w += w
                tot_l += l
                tot_t += t
                cash_deltas.append(cell["mean_delta"])
                wr = cell["win_rate"] * 100
                cell_str = f"{w}-{l}-{t} ({wr:.0f}%)"
                row_str += f"{cell_str:<14}"
        tot_matches = tot_w + tot_l + tot_t
        overall_wr = (tot_w / tot_matches * 100) if tot_matches > 0 else 0
        overall_stats[r1] = {"w": tot_w, "l": tot_l, "t": tot_t, "wr": overall_wr, "mean_delta": float(np.mean(cash_deltas))}
        record_str = f"{tot_w}-{tot_l}-{tot_t}"
        row_str += f"{record_str:<16}{overall_wr:.1f}%"
        print(row_str)

    print("\n=================== PAIRWISE MEAN CASH DELTAS ($) ===================")
    header = f"{'Route':<12}" + "".join([f"{r:<14}" for r in routes]) + f"{'Mean Delta':<14}"
    print(header)
    print("-" * len(header))
    for r1 in routes:
        row_str = f"{r1:<12}"
        for r2 in routes:
            if r1 == r2:
                row_str += f"{'--':<14}"
            else:
                delta = matrix[r1][r2]["mean_delta"]
                delta_str = f"{delta:+,.0f}"
                row_str += f"{delta_str:<14}"
        m_delta_str = f"{overall_stats[r1]['mean_delta']:+,.0f}"
        row_str += f"{m_delta_str:<14}"
        print(row_str)

    print("\n=================== PAIRWISE MEAN FINAL CASH ($) ===================")
    header = f"{'Route':<12}" + "".join([f"{r:<14}" for r in routes]) + f"{'Overall Mean':<14}"
    print(header)
    print("-" * len(header))
    for r1 in routes:
        row_str = f"{r1:<12}"
        cashes = []
        for r2 in routes:
            if r1 == r2:
                row_str += f"{'--':<14}"
            else:
                cash = matrix[r1][r2]["mean_cash"]
                cashes.append(cash)
                cash_str = f"{cash:,.0f}"
                row_str += f"{cash_str:<14}"
        m_cash_str = f"{np.mean(cashes):,.0f}"
        row_str += f"{m_cash_str:<14}"
        print(row_str)

    # Check for non-transitivity cycles
    print("\n=================== NON-TRANSITIVITY CYCLE SEARCH ===================")
    edges = []
    for r1 in routes:
        for r2 in routes:
            if r1 == r2:
                continue
            cell = matrix[r1][r2]
            if cell["wins"] > cell["losses"] and cell["win_rate"] >= 0.60:
                edges.append((r1, r2, cell["win_rate"], cell["mean_delta"]))

    print(f"Significant dominance edges (win rate >= 60%):")
    for r1, r2, wr, md in edges:
        print(f"  {r1} -> {r2} (WinRate: {wr*100:.0f}%, Mean Delta: ${md:+,.0f})")

    # Cycle detection
    cycles = []
    for a in routes:
        for b in routes:
            if b == a:
                continue
            if any(e[0] == a and e[1] == b for e in edges):
                for c in routes:
                    if c in (a, b):
                        continue
                    if any(e[0] == b and e[1] == c for e in edges):
                        if any(e[0] == c and e[1] == a for e in edges):
                            cycle = tuple(sorted([a, b, c]))
                            if cycle not in cycles:
                                cycles.append(cycle)
                                print(f"*** NON-TRANSITIVE 3-CYCLE FOUND: {a} -> {b} -> {c} -> {a} ***")

    if not cycles:
        print("No simple 3-cycles found with win rate >= 60%.")


if __name__ == "__main__":
    main()
