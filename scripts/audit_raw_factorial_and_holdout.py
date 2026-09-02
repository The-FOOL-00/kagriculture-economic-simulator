import json
import math
import statistics
from pathlib import Path

def audit_factorial_results(json_path):
    print("=" * 90)
    print(f"DEEP FORENSIC AUDIT OF FACTORIAL RESULTS: {json_path}")
    print("=" * 90)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Engine Version Stated: {data.get('engine_version')}")
    print(f"Number of Seeds Stated: {data.get('num_seeds')}")
    print(f"Total Games Per Cell Stated: {data.get('total_games_per_cell')}")

    seeds_list = data.get("seeds", [])
    print(f"Distinct Seeds in seeds array: {len(seeds_list)} (Unique: {len(set(seeds_list))})")

    # Check for duplicate seeds
    if len(seeds_list) != len(set(seeds_list)):
        print("  [ERROR] Duplicate seeds found in development seed list!")
    else:
        print("  [PASS] Zero duplicate seeds in development list.")

    cells = data.get("cells", {})
    recomputed_cells = {}

    for cell_key, cell_data in cells.items():
        print(f"\n----------------------------------------------------------------------")
        print(f"AUDITING CELL: {cell_key}")
        print(f"Candidate: {cell_data.get('candidate')} vs Opponent: {cell_data.get('opponent')}")
        print(f"----------------------------------------------------------------------")

        matches = cell_data.get("matches", [])
        print(f"Raw Match Records Count: {len(matches)}")

        wins = 0
        losses = 0
        ties = 0
        p0_wins = 0
        p0_count = 0
        p1_wins = 0
        p1_count = 0
        margins = []
        invalid_actions_total = 0
        exceptions_total = 0
        catastrophic_count = 0
        worst_margin = 0.0

        seed_counts = {}
        seat_pairs = {}

        for m in matches:
            s = m["seed"]
            seat = m["seat"]
            cand_r = float(m["cand_reward"])
            opp_r = float(m["opp_reward"])
            margin = float(m["margin"])
            err = m.get("error")
            inv_cnt = int(m.get("invalid_count", 0))

            # Verify margin formula
            computed_margin = cand_r - opp_r
            if abs(margin - computed_margin) > 1e-3:
                print(f"  [ERROR] Margin mismatch for seed {s} {seat}: stored {margin}, computed {computed_margin}")

            margins.append(margin)

            # Verify win/loss/tie definition
            if cand_r > opp_r:
                wins += 1
                if seat == "P0":
                    p0_wins += 1
                else:
                    p1_wins += 1
            elif cand_r < opp_r:
                losses += 1
            else:
                ties += 1

            if seat == "P0":
                p0_count += 1
            else:
                p1_count += 1

            seed_counts[s] = seed_counts.get(s, 0) + 1
            if s not in seat_pairs:
                seat_pairs[s] = set()
            seat_pairs[s].add(seat)

            if inv_cnt > 0:
                invalid_actions_total += inv_cnt
            if err is not None:
                exceptions_total += 1
            if margin < -10000.0:
                catastrophic_count += 1
            if margin < worst_margin:
                worst_margin = margin

        total = len(matches)
        win_rate = (wins / total) * 100.0 if total > 0 else 0.0
        p0_wr = (p0_wins / p0_count) * 100.0 if p0_count > 0 else 0.0
        p1_wr = (p1_wins / p1_count) * 100.0 if p1_count > 0 else 0.0

        mean_m = statistics.mean(margins)
        median_m = statistics.median(margins)
        std_m = statistics.stdev(margins)
        sem_m = std_m / math.sqrt(total)
        ci95_m = 1.96 * sem_m

        # Check pairing symmetry
        fully_paired = sum(1 for s, seats in seat_pairs.items() if seats == {"P0", "P1"})

        print(f"Independently Recomputed Metrics:")
        print(f"  Total Matches: {total} (Wins: {wins}, Losses: {losses}, Ties: {ties})")
        print(f"  Win Rate: {win_rate:.2f}% (P0 WR: {p0_wr:.2f}%, P1 WR: {p1_wr:.2f}%)")
        print(f"  Mean Margin: {mean_m:+.2f} (+/-{ci95_m:.2f}) [Std: {std_m:.2f}, SEM: {sem_m:.2f}]")
        print(f"  Median Margin: {median_m:+.2f}")
        print(f"  Worst Margin: {worst_margin:+.2f}")
        print(f"  Catastrophic Losses (< -$10k): {catastrophic_count}")
        print(f"  Invalid Actions: {invalid_actions_total}, Exceptions: {exceptions_total}")
        print(f"  Unique Seeds in Cell: {len(seed_counts)} (Fully Paired P0+P1: {fully_paired})")

        # Compare with stored summary in JSON
        print(f"\nStored Summary Comparison:")
        print(f"  Stored Wins: {cell_data.get('wins')} vs Recomputed: {wins} (Match: {cell_data.get('wins') == wins})")
        print(f"  Stored Losses: {cell_data.get('losses')} vs Recomputed: {losses} (Match: {cell_data.get('losses') == losses})")
        print(f"  Stored Ties: {cell_data.get('ties')} vs Recomputed: {ties} (Match: {cell_data.get('ties') == ties})")
        print(f"  Stored Win Rate: {cell_data.get('win_rate')} vs Recomputed: {win_rate:.2f}% (Diff: {abs(cell_data.get('win_rate') - win_rate):.6f})")
        print(f"  Stored Mean: {cell_data.get('mean_margin')} vs Recomputed: {mean_m:.2f} (Diff: {abs(cell_data.get('mean_margin') - mean_m):.6f})")
        print(f"  Stored Median: {cell_data.get('median_margin')} vs Recomputed: {median_m:.2f} (Diff: {abs(cell_data.get('median_margin') - median_m):.6f})")
        print(f"  Stored CI95: {cell_data.get('ci95')} vs Recomputed: {ci95_m:.2f} (Diff: {abs(cell_data.get('ci95') - ci95_m):.6f})")

        recomputed_cells[cell_key] = {
            "wins": wins,
            "losses": losses,
            "ties": ties,
            "total": total,
            "win_rate": win_rate,
            "mean_margin": mean_m,
            "median_margin": median_m,
            "std_margin": std_m,
            "ci95": ci95_m,
            "margins": margins
        }

    # Now causal decomposition
    print("\n" + "=" * 90)
    print("INDEPENDENT RECOMPUTATION OF FACTORIAL EFFECTS & INTERACTION")
    print("=" * 90)

    # Key cells
    cA = recomputed_cells["Cell_A_Base"]
    cB = recomputed_cells["Cell_B_MC"]
    cC = recomputed_cells["Cell_C_T712"]
    cD = recomputed_cells["Cell_D_Refined"]

    A_mean = cA["mean_margin"]
    B_mean = cB["mean_margin"]
    C_mean = cC["mean_margin"]
    D_mean = cD["mean_margin"]

    delta_M = B_mean - A_mean
    delta_T = C_mean - A_mean
    combined = D_mean - A_mean
    interaction = D_mean - B_mean - C_mean + A_mean

    print(f"Cell A (Baseline):      ${A_mean:+10.2f} (WR: {cA['win_rate']:.1f}%)")
    print(f"Cell B (Market Only):   ${B_mean:+10.2f} (WR: {cB['win_rate']:.1f}%)")
    print(f"Cell C (Terminal Only): ${C_mean:+10.2f} (WR: {cC['win_rate']:.1f}%)")
    print(f"Cell D (Combined):      ${D_mean:+10.2f} (WR: {cD['win_rate']:.1f}%)")

    print(f"\nMain & Interaction Effects:")
    print(f"  Delta M (Market Effect)      = B - A         = ${delta_M:+10.2f}")
    print(f"  Delta T (Terminal Effect)    = C - A         = ${delta_T:+10.2f}")
    print(f"  Combined (Full Effect)       = D - A         = ${combined:+10.2f}")
    print(f"  Interaction Effect (Synergy) = D - B - C + A = ${interaction:+10.2f}")

    # Check Direct Pairwise H2H if present
    h2h_keys = [k for k in cells.keys() if k.startswith("H2H_")]
    if h2h_keys:
        print("\nDirect Head-to-Head Recomputed Values:")
        for hk in h2h_keys:
            info = recomputed_cells[hk]
            print(f"  {hk:25s}: {info['wins']}W - {info['losses']}L - {info['ties']}T ({info['win_rate']:.1f}%) | Mean: {info['mean_margin']:+.2f} (+/-{info['ci95']:.2f}) | Median: {info['median_margin']:+.2f}")

    return recomputed_cells

def audit_holdout_results(json_path):
    print("\n" + "=" * 90)
    print(f"DEEP FORENSIC AUDIT OF HOLDOUT & REFERENCE SUITE: {json_path}")
    print("=" * 90)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Holdout
    holdout = data.get("holdout_vs_anchor", {})
    print("\n--- 1. HOLDOUT VALIDATION VS AETHEL ANCHOR ---")
    
    matches = holdout.get("matches", [])
    print(f"Raw Holdout Matches: {len(matches)}")

    h_wins = 0
    h_losses = 0
    h_ties = 0
    h_p0_wins = 0
    h_p0_cnt = 0
    h_p1_wins = 0
    h_p1_cnt = 0
    h_margins = []
    h_worst = 0.0
    h_seeds = set()
    h_seat_pairs = {}

    for m in matches:
        s = m["seed"]
        seat = m["seat"]
        cand_r = float(m["cand_reward"])
        opp_r = float(m["opp_reward"])
        margin = float(m["margin"])

        h_seeds.add(s)
        if s not in h_seat_pairs:
            h_seat_pairs[s] = set()
        h_seat_pairs[s].add(seat)

        if abs(margin - (cand_r - opp_r)) > 1e-3:
            print(f"  [ERROR] Holdout margin mismatch in seed {s} {seat}")

        h_margins.append(margin)

        if cand_r > opp_r:
            h_wins += 1
            if seat == "P0":
                h_p0_wins += 1
            else:
                h_p1_wins += 1
        elif cand_r < opp_r:
            h_losses += 1
        else:
            h_ties += 1

        if seat == "P0":
            h_p0_cnt += 1
        else:
            h_p1_cnt += 1

        if margin < h_worst:
            h_worst = margin

    h_total = len(matches)
    h_wr = (h_wins / h_total) * 100.0
    h_p0_wr = (h_p0_wins / h_p0_cnt) * 100.0
    h_p1_wr = (h_p1_wins / h_p1_cnt) * 100.0
    h_mean = statistics.mean(h_margins)
    h_med = statistics.median(h_margins)
    h_std = statistics.stdev(h_margins)
    h_ci95 = 1.96 * (h_std / math.sqrt(h_total))
    h_paired = sum(1 for s, st in h_seat_pairs.items() if st == {"P0", "P1"})

    print(f"Independently Recomputed Holdout Metrics:")
    print(f"  Matches: {h_total} (Wins: {h_wins}, Losses: {h_losses}, Ties: {h_ties})")
    print(f"  Win Rate: {h_wr:.2f}% (P0: {h_p0_wr:.2f}%, P1: {h_p1_wr:.2f}%)")
    print(f"  Mean Margin: {h_mean:+.2f} (+/-{h_ci95:.2f}) [Std: {h_std:.2f}]")
    print(f"  Median Margin: {h_med:+.2f}")
    print(f"  Worst Loss: {h_worst:+.2f}")
    print(f"  Unique Seeds: {len(h_seeds)} (Range: {min(h_seeds)}..{max(h_seeds)}, Fully Paired: {h_paired})")

    # Check Reference Suite
    ref_suite = data.get("reference_suite", {})
    print("\n--- 2. REFERENCE SUITE OPPONENT BENCHMARKS ---")
    for opp_name, odata in ref_suite.items():
        o_matches = odata.get("matches", [])
        o_wins = sum(1 for m in o_matches if m["cand_reward"] > m["opp_reward"])
        o_losses = sum(1 for m in o_matches if m["cand_reward"] < m["opp_reward"])
        o_ties = sum(1 for m in o_matches if m["cand_reward"] == m["opp_reward"])
        o_margins = [m["margin"] for m in o_matches]
        o_p0_wins = sum(1 for m in o_matches if m["seat"] == "P0" and m["cand_reward"] > m["opp_reward"])
        o_p0_cnt = sum(1 for m in o_matches if m["seat"] == "P0")
        o_p1_wins = sum(1 for m in o_matches if m["seat"] == "P1" and m["cand_reward"] > m["opp_reward"])
        o_p1_cnt = sum(1 for m in o_matches if m["seat"] == "P1")

        o_total = len(o_matches)
        o_wr = (o_wins / o_total) * 100.0 if o_total > 0 else 0.0
        o_p0_wr = (o_p0_wins / o_p0_cnt) * 100.0 if o_p0_cnt > 0 else 0.0
        o_p1_wr = (o_p1_wins / o_p1_cnt) * 100.0 if o_p1_cnt > 0 else 0.0
        o_mean = statistics.mean(o_margins) if o_margins else 0.0
        o_med = statistics.median(o_margins) if o_margins else 0.0
        o_std = statistics.stdev(o_margins) if len(o_margins) > 1 else 0.0
        o_ci = 1.96 * (o_std / math.sqrt(o_total)) if o_total > 0 else 0.0
        
        print(f"  {opp_name:20s}: {o_total:2d} matches | {o_wins:2d}W - {o_losses:2d}L - {o_ties:2d}T ({o_wr:5.1f}%) | Mean: {o_mean:+10.2f} (+/-{o_ci:6.2f}) | Median: {o_med:+10.2f} | P0: {o_p0_wr:5.1f}% | P1: {o_p1_wr:5.1f}%")

    # Gate verification
    gate_details = data.get("gate_details", [])
    print("\n--- 3. GATE VERIFICATION IN JSON ---")
    for g in gate_details:
        print(f"  [{g.get('status')}] {g.get('name')}: {g.get('detail')}")

if __name__ == "__main__":
    audit_factorial_results("scratch/corrected_causal_factorial_results.json")
    audit_holdout_results("scratch/corrected_holdout_and_gate_results.json")
