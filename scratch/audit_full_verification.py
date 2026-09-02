import os
import sys
import json
import math
import hashlib
import tarfile
import tempfile
import shutil
import scipy.stats as stats
import numpy as np

def analyze_raw_matches(matches, cand_key="cand_reward", opp_key="opp_reward", seat_key="seat"):
    total = len(matches)
    margins = []
    wins = 0
    losses = 0
    ties = 0
    p0_wins = 0
    p0_total = 0
    p1_wins = 0
    p1_total = 0
    
    for m in matches:
        cr = float(m[cand_key])
        opr = float(m[opp_key])
        margin = cr - opr
        margins.append(margin)
        
        seat = m.get(seat_key)
        if seat is None and "candidate_seat" in m:
            seat = f"P{m['candidate_seat']}"
            
        if margin > 0:
            wins += 1
            if seat == "P0": p0_wins += 1
            elif seat == "P1": p1_wins += 1
        elif margin < 0:
            losses += 1
        else:
            ties += 1
            
        if seat == "P0": p0_total += 1
        elif seat == "P1": p1_total += 1

    arr = np.array(margins, dtype=np.float64)
    mean_val = float(np.mean(arr))
    median_val = float(np.median(arr))
    # Sample standard deviation (ddof=1)
    std_sample = float(np.std(arr, ddof=1)) if total > 1 else 0.0
    # Population standard deviation (ddof=0)
    std_pop = float(np.std(arr, ddof=0))
    sem = std_sample / math.sqrt(total) if total > 0 else 0.0
    
    # t-distribution 95% CI
    if total > 1:
        t_crit = float(stats.t.ppf(0.975, df=total - 1))
        ci95_t = t_crit * sem
        ci_lower = mean_val - ci95_t
        ci_upper = mean_val + ci95_t
        
        # 1-sample t-test vs 0
        t_stat, p_val_2s = stats.ttest_1samp(arr, 0.0)
        t_stat = float(t_stat)
        p_val_2s = float(p_val_2s)
        p_val_1s = p_val_2s / 2.0 if t_stat > 0 else 1.0 - (p_val_2s / 2.0)
    else:
        t_crit, ci95_t, ci_lower, ci_upper, t_stat, p_val_2s, p_val_1s = 0, 0, 0, 0, 0, 1.0, 1.0

    # z-distribution (1.96)
    ci95_z = 1.96 * sem

    wr = (wins / total) * 100.0 if total > 0 else 0.0
    p0_wr = (p0_wins / p0_total) * 100.0 if p0_total > 0 else 0.0
    p1_wr = (p1_wins / p1_total) * 100.0 if p1_total > 0 else 0.0
    
    min_margin = float(np.min(arr)) if len(arr) > 0 else 0.0
    max_margin = float(np.max(arr)) if len(arr) > 0 else 0.0
    catastrophic = int(np.sum(arr < -10000.0))

    return {
        "total": total,
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "win_rate": wr,
        "mean": mean_val,
        "median": median_val,
        "std_sample": std_sample,
        "std_pop": std_pop,
        "sem": sem,
        "t_crit": t_crit,
        "ci95_t_half": ci95_t,
        "ci95_t_lower": ci_lower,
        "ci95_t_upper": ci_upper,
        "ci95_z_half": ci95_z,
        "t_stat": t_stat,
        "p_val_2s": p_val_2s,
        "p_val_1s": p_val_1s,
        "p0_wins": p0_wins,
        "p0_total": p0_total,
        "p0_wr": p0_wr,
        "p1_wins": p1_wins,
        "p1_total": p1_total,
        "p1_wr": p1_wr,
        "min_margin": min_margin,
        "max_margin": max_margin,
        "catastrophic": catastrophic,
        "margins": margins
    }

def main():
    print("==================================================")
    print("RUNNING COMPREHENSIVE FINAL PRE-SUBMISSION AUDIT")
    print("==================================================")
    
    # 1. Audit scratch/corrected_causal_factorial_results.json
    with open("scratch/corrected_causal_factorial_results.json", "r") as f:
        fac_data = json.load(f)
        
    print("\n--- 1. FACTORIAL CELLS AUDIT ---")
    cell_stats = {}
    for cell_name, cell_obj in fac_data["cells"].items():
        matches = cell_obj["matches"]
        res = analyze_raw_matches(matches)
        cell_stats[cell_name] = res
        print(f"[{cell_name:15s}] Total={res['total']:3d} | {res['wins']:3d}W-{res['losses']:3d}L-{res['ties']:2d}T ({res['win_rate']:5.1f}% WR) | Mean={res['mean']:+9.2f} (±{res['ci95_t_half']:6.2f}) | Med={res['median']:+8.2f} | Std(s)={res['std_sample']:7.2f} | P0={res['p0_wr']:5.1f}% | P1={res['p1_wr']:5.1f}% | t={res['t_stat']:7.4f} | p={res['p_val_2s']:.3e}")

    # 2. Reconcile Factorial vs Direct H2H
    print("\n--- 2. CAUSAL RECONCILIATION ---")
    mean_A = cell_stats["Cell_A_Base"]["mean"]
    mean_B = cell_stats["Cell_B_MC"]["mean"]
    mean_C = cell_stats["Cell_C_T712"]["mean"]
    mean_D = cell_stats["Cell_D_Refined"]["mean"]
    
    delta_M_anchor = mean_B - mean_A
    delta_T_anchor = mean_C - mean_A
    combined_anchor = mean_D - mean_A
    I_anchor = mean_D - mean_B - mean_C + mean_A
    
    h2h_B_vs_A = cell_stats["H2H_B_vs_A"]["mean"]
    h2h_C_vs_A = cell_stats["H2H_C_vs_A"]["mean"]
    h2h_D_vs_B = cell_stats["H2H_D_vs_B"]["mean"]
    h2h_D_vs_C = cell_stats["H2H_D_vs_C"]["mean"]
    h2h_D_vs_A = cell_stats["H2H_D_vs_A"]["mean"]
    I_h2h = h2h_D_vs_B - h2h_C_vs_A  # (D - B) - (C - A)
    
    print(f"Anchor-relative Effects:")
    print(f"  Mean Cell A: {mean_A:+.2f}")
    print(f"  Mean Cell B: {mean_B:+.2f}")
    print(f"  Mean Cell C: {mean_C:+.2f}")
    print(f"  Mean Cell D: {mean_D:+.2f}")
    print(f"  Delta_M (B - A)     : {delta_M_anchor:+.2f}")
    print(f"  Delta_T (C - A)     : {delta_T_anchor:+.2f}")
    print(f"  Combined (D - A)    : {combined_anchor:+.2f}")
    print(f"  Interaction I_anchor: {I_anchor:+.2f}")
    print(f"\nDirect H2H Effects:")
    print(f"  H2H B vs A          : {h2h_B_vs_A:+.2f} (WR: {cell_stats['H2H_B_vs_A']['win_rate']:.1f}%)")
    print(f"  H2H C vs A          : {h2h_C_vs_A:+.2f} (WR: {cell_stats['H2H_C_vs_A']['win_rate']:.1f}%)")
    print(f"  H2H D vs B          : {h2h_D_vs_B:+.2f} (WR: {cell_stats['H2H_D_vs_B']['win_rate']:.1f}%)")
    print(f"  H2H D vs C          : {h2h_D_vs_C:+.2f} (WR: {cell_stats['H2H_D_vs_C']['win_rate']:.1f}%)")
    print(f"  H2H D vs A          : {h2h_D_vs_A:+.2f} (WR: {cell_stats['H2H_D_vs_A']['win_rate']:.1f}%)")
    print(f"  Interaction I_h2h   : {I_h2h:+.2f}")

    # 3. Interaction Statistical Significance
    # For Anchor-relative 2x2: y = mu + alpha*M + beta*T + gamma*(M*T) + epsilon
    # On 800 observations (200 in each cell A, B, C, D)
    margins_A = np.array(cell_stats["Cell_A_Base"]["margins"])
    margins_B = np.array(cell_stats["Cell_B_MC"]["margins"])
    margins_C = np.array(cell_stats["Cell_C_T712"]["margins"])
    margins_D = np.array(cell_stats["Cell_D_Refined"]["margins"])
    
    # 2x2 Factorial ANOVA on Anchor margins
    Y = np.concatenate([margins_A, margins_B, margins_C, margins_D])
    M_factor = np.concatenate([np.zeros(200), np.ones(200), np.zeros(200), np.ones(200)])
    T_factor = np.concatenate([np.zeros(200), np.zeros(200), np.ones(200), np.ones(200)])
    MT_interaction = M_factor * T_factor
    X = np.column_stack([np.ones(800), M_factor, T_factor, MT_interaction])
    
    # OLS regression
    beta, residuals, rank, s = np.linalg.lstsq(X, Y, rcond=None)
    residuals_vec = Y - X @ beta
    dof = 800 - 4
    sigma2 = np.sum(residuals_vec**2) / dof
    cov_matrix = np.linalg.inv(X.T @ X) * sigma2
    std_errors = np.sqrt(np.diag(cov_matrix))
    t_stats = beta / std_errors
    p_values = [2.0 * (1.0 - stats.t.cdf(abs(t), df=dof)) for t in t_stats]
    
    print("\n--- 3. 2x2 FACTORIAL OLS / ANOVA STATS (Anchor relative) ---")
    terms = ["Intercept (Cell A)", "Market Controller (M)", "Terminal 712 (T)", "Interaction (M*T)"]
    for t_name, b_val, se, t_val, p_val in zip(terms, beta, std_errors, t_stats, p_values):
        print(f"  {t_name:25s}: Coef = {b_val:+9.2f} | SE = {se:7.2f} | t = {t_val:7.4f} | p = {p_val:.4e}")

    # Contrast test for H2H interaction: (D vs B) - (C vs A) on paired seeds
    arr_DB = np.array(cell_stats["H2H_D_vs_B"]["margins"])
    arr_CA = np.array(cell_stats["H2H_C_vs_A"]["margins"])
    # If paired by index (both evaluated on same 200 matches)
    diff_h2h_interaction = arr_DB - arr_CA
    mean_diff_I = np.mean(diff_h2h_interaction)
    std_diff_I = np.std(diff_h2h_interaction, ddof=1)
    sem_diff_I = std_diff_I / math.sqrt(len(diff_h2h_interaction))
    t_stat_h2h_I = mean_diff_I / sem_diff_I
    p_val_h2h_I = 2.0 * (1.0 - stats.t.cdf(abs(t_stat_h2h_I), df=len(diff_h2h_interaction) - 1))
    ci95_h2h_I = stats.t.ppf(0.975, df=len(diff_h2h_interaction) - 1) * sem_diff_I
    
    print(f"\n--- 4. DIRECT H2H INTERACTION TEST ---")
    print(f"  Point Estimate: {mean_diff_I:+.2f}")
    print(f"  95% CI: [{mean_diff_I - ci95_h2h_I:+.2f}, {mean_diff_I + ci95_h2h_I:+.2f}]")
    print(f"  t-statistic: {t_stat_h2h_I:.4f} (df={len(diff_h2h_interaction)-1})")
    print(f"  p-value: {p_val_h2h_I:.4e}")

    # 4. Holdout Recomputation from scratch/corrected_holdout_and_gate_results.json
    print("\n--- 5. HOLDOUT RECOMPUTATION ---")
    with open("scratch/corrected_holdout_and_gate_results.json", "r") as f:
        hold_data = json.load(f)
        
    hold_matches = hold_data["holdout_vs_anchor"]["matches"]
    hold_res = analyze_raw_matches(hold_matches)
    
    # Seeds audit
    hold_seeds = [m["seed"] for m in hold_matches]
    unique_hold_seeds = sorted(list(set(hold_seeds)))
    dev_seeds = fac_data["seeds"]
    seed_intersection = set(dev_seeds).intersection(set(hold_seeds))
    
    print(f"  Holdout Matches: {hold_res['total']} (Expected: 200)")
    print(f"  Unique Seeds   : {len(unique_hold_seeds)} (Range: {min(unique_hold_seeds)}..{max(unique_hold_seeds)})")
    print(f"  Dev Seeds      : {len(dev_seeds)} (Range: {min(dev_seeds)}..{max(dev_seeds)})")
    print(f"  Seed Contamination: {len(seed_intersection)} overlapping seeds (Set: {seed_intersection})")
    print(f"  Wins/Losses/Ties: {hold_res['wins']}W - {hold_res['losses']}L - {hold_res['ties']}T")
    print(f"  Win Rate       : {hold_res['win_rate']:.2f}%")
    print(f"  Mean Margin    : {hold_res['mean']:+.2f}")
    print(f"  Median Margin  : {hold_res['median']:+.2f}")
    print(f"  Std Dev (sample): {hold_res['std_sample']:.2f}")
    print(f"  Std Dev (pop)  : {hold_res['std_pop']:.2f}")
    print(f"  SEM            : {hold_res['sem']:.2f}")
    print(f"  95% CI (t-dist): [{hold_res['ci95_t_lower']:+.2f}, {hold_res['ci95_t_upper']:+.2f}] (±{hold_res['ci95_t_half']:.2f})")
    print(f"  t-statistic    : {hold_res['t_stat']:.4f}")
    print(f"  p-value (2-tail): {hold_res['p_val_2s']:.3e}")
    print(f"  P0 Record      : {hold_res['p0_wins']}/{hold_res['p0_total']} ({hold_res['p0_wr']:.2f}%)")
    print(f"  P1 Record      : {hold_res['p1_wins']}/{hold_res['p1_total']} ({hold_res['p1_wr']:.2f}%)")
    print(f"  Min Margin     : {hold_res['min_margin']:+.2f}")
    print(f"  Max Margin     : {hold_res['max_margin']:+.2f}")
    print(f"  Catastrophic (< -10k): {hold_res['catastrophic']}")

    # 5. Reference Suite Audit
    print("\n--- 6. REFERENCE SUITE AUDIT ---")
    suite_stats = {}
    for opp_name, opp_obj in hold_data["reference_suite"].items():
        opp_matches = opp_obj["matches"]
        res = analyze_raw_matches(opp_matches)
        suite_stats[opp_name] = res
        print(f"  vs {opp_name:18s}: {res['wins']:2d}/{res['total']:2d} ({res['win_rate']:5.1f}% WR) | Mean: {res['mean']:+10.2f} (±{res['ci95_t_half']:7.2f}) | Med: {res['median']:+10.2f} | P0={res['p0_wr']:5.1f}% | P1={res['p1_wr']:5.1f}% | Min={res['min_margin']:+9.2f}")

    # 6. Cryptographic Hash & Byte-Identity Audit
    print("\n--- 7. ARTIFACT & CRYPTOGRAPHIC IDENTITY AUDIT ---")
    file_candidate_d = "agents/candidate_d_aethel_refined.py"
    file_slot2_staged = "candidates/slot2_aethel_refined_v2.py"
    tarball_file = "submission_slot2_aethel_refined_v2.tar.gz"
    
    with open(file_candidate_d, "rb") as f:
        bytes_cand_d = f.read()
    hash_cand_d = hashlib.sha256(bytes_cand_d).hexdigest()
    
    with open(file_slot2_staged, "rb") as f:
        bytes_slot2 = f.read()
    hash_slot2 = hashlib.sha256(bytes_slot2).hexdigest()
    
    with open(tarball_file, "rb") as f:
        bytes_tar = f.read()
    hash_tar = hashlib.sha256(bytes_tar).hexdigest()
    
    # Extract tarball in memory / tempdir
    with tempfile.TemporaryDirectory() as tmpdir:
        with tarfile.open(tarball_file, "r:gz") as tar:
            tar_members = tar.getnames()
            tar.extractall(tmpdir)
        extracted_main = os.path.join(tmpdir, "main.py")
        with open(extracted_main, "rb") as f:
            bytes_extracted = f.read()
        hash_extracted = hashlib.sha256(bytes_extracted).hexdigest()
        
    print(f"  Candidate D Hash   : {hash_cand_d}")
    print(f"  Slot 2 Staged Hash : {hash_slot2}")
    print(f"  Extracted main Hash: {hash_extracted}")
    print(f"  Tarball Hash       : {hash_tar}")
    print(f"  Tarball Members    : {tar_members}")
    print(f"  Byte Equality (Cand D == Slot2 Staged == Extracted main): {bytes_cand_d == bytes_slot2 == bytes_extracted}")

    # Save everything to scratch/final_release_audit.json
    audit_json = {
        "factorial_cell_stats": {k: {kk: vv for kk, vv in v.items() if kk != "margins"} for k, v in cell_stats.items()},
        "causal_math": {
            "mean_A": mean_A, "mean_B": mean_B, "mean_C": mean_C, "mean_D": mean_D,
            "delta_M_anchor": delta_M_anchor, "delta_T_anchor": delta_T_anchor,
            "combined_anchor": combined_anchor, "I_anchor": I_anchor,
            "h2h_B_vs_A": h2h_B_vs_A, "h2h_C_vs_A": h2h_C_vs_A,
            "h2h_D_vs_B": h2h_D_vs_B, "h2h_D_vs_C": h2h_D_vs_C,
            "h2h_D_vs_A": h2h_D_vs_A, "I_h2h": I_h2h
        },
        "anova_anchor": {
            "beta": list(beta),
            "std_errors": list(std_errors),
            "t_stats": list(t_stats),
            "p_values": list(p_values)
        },
        "interaction_h2h_test": {
            "point_estimate": mean_diff_I,
            "ci95": [mean_diff_I - ci95_h2h_I, mean_diff_I + ci95_h2h_I],
            "t_stat": t_stat_h2h_I,
            "p_value": p_val_h2h_I
        },
        "holdout_stats": {kk: vv for kk, vv in hold_res.items() if kk != "margins"},
        "holdout_seeds": {
            "count": len(unique_hold_seeds),
            "min": min(unique_hold_seeds),
            "max": max(unique_hold_seeds),
            "intersection_with_dev": list(seed_intersection)
        },
        "suite_stats": {k: {kk: vv for kk, vv in v.items() if kk != "margins"} for k, v in suite_stats.items()},
        "hashes": {
            "candidate_d": hash_cand_d,
            "slot2_staged": hash_slot2,
            "extracted_main": hash_extracted,
            "tarball": hash_tar,
            "tar_members": tar_members,
            "all_byte_identical": (bytes_cand_d == bytes_slot2 == bytes_extracted)
        }
    }
    
    with open("scratch/final_release_audit.json", "w") as f:
        json.dump(audit_json, f, indent=2)
    print("\nSaved full audit data to scratch/final_release_audit.json")

if __name__ == "__main__":
    main()
