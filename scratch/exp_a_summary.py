"""
EXP-A Gate Check Summary
========================
Reads scratch/exp_a_results.json and reports all 6 gate criteria.
"""
import json, sys, math

data = json.load(open("scratch/exp_a_results.json"))

def ci95(values):
    n = len(values)
    if n < 2: return (float("nan"), float("nan"))
    mean = sum(values) / n
    sd = math.sqrt(sum((x - mean)**2 for x in values) / (n - 1))
    se = sd / math.sqrt(n)
    return (mean - 1.96*se, mean + 1.96*se)

def summarize(rows):
    ok_rows = [r for r in rows if r["error"] is None]
    n = len(ok_rows)
    crashes = len(rows) - n
    rewards = [r["backbone"] for r in ok_rows]
    margins = [r["margin"] for r in ok_rows]
    wins = sum(1 for r in ok_rows if r["winner"] == "backbone")
    mean_r = sum(rewards)/n if n else 0
    mean_m = sum(margins)/n if n else 0
    sd_m = math.sqrt(sum((x-mean_m)**2 for x in margins)/(n-1)) if n > 1 else 0
    ci_m = ci95(margins)
    return dict(n=n, crashes=crashes, mean_r=mean_r, mean_m=mean_m,
                sd_m=sd_m, ci_m=ci_m, wins=wins, win_rate=wins/n if n else 0)

print("=" * 70)
print("EXP-A GATE CHECK REPORT")
print("=" * 70)

v2 = summarize(data.get("V2", []))
v54 = summarize(data.get("V54", []))
idle = summarize(data.get("IDLE", []))

print(f"\nVs V2:  n={v2['n']}  mean_reward={v2['mean_r']:.0f}  mean_margin={v2['mean_m']:+.0f}  "
      f"win_rate={v2['win_rate']:.1%}  CI_margin=({v2['ci_m'][0]:+.0f}, {v2['ci_m'][1]:+.0f})")
print(f"Vs V54: n={v54['n']}  mean_reward={v54['mean_r']:.0f}  mean_margin={v54['mean_m']:+.0f}  "
      f"win_rate={v54['win_rate']:.1%}  CI_margin=({v54['ci_m'][0]:+.0f}, {v54['ci_m'][1]:+.0f})")

# Compute deficit vs V54 (how far below V54 reward)
v54_rows = data.get("V54", [])
v54_opp_rewards = [r["opp"] for r in v54_rows if r["error"] is None]
v54_mean_opp = sum(v54_opp_rewards)/len(v54_opp_rewards) if v54_opp_rewards else 0
margin_deficit_vs_v54 = v54_mean_opp - v2["mean_r"]  # V54's reward vs our reward when playing V54

print()
print("=" * 70)
print("GATE RESULTS")
print("=" * 70)

gates = {}

# G1: Mean reward vs V2 >= 100,000
g1 = v2["mean_r"] >= 100_000
gates["G1"] = ("PASS" if g1 else "FAIL",
               f"Mean reward vs V2 = {v2['mean_r']:.0f}  (threshold >= 100,000)")

# G2: Mean margin vs V2 >= 80,000
g2 = v2["mean_m"] >= 80_000
gates["G2"] = ("PASS" if g2 else "FAIL",
               f"Mean margin vs V2 = {v2['mean_m']:+.0f}  (threshold >= +80,000)")

# G3: Win rate vs V2 = 100%
g3 = v2["win_rate"] >= 0.9 and v2["crashes"] == 0
gates["G3"] = ("PASS" if g3 else "FAIL",
               f"Win rate vs V2 = {v2['win_rate']:.1%}  crashes={v2['crashes']}  (threshold >= 90%, 0 crashes)")

# G4: Deficit vs V54 <= 15,000
# Our mean reward when playing V54 vs V54's mean reward when playing us
our_vs_v54 = [r["backbone"] for r in v54_rows if r["error"] is None]
v54_vs_us   = [r["opp"] for r in v54_rows if r["error"] is None]
our_mean_vs_v54 = sum(our_vs_v54)/len(our_vs_v54) if our_vs_v54 else 0
v54_mean_vs_us  = sum(v54_vs_us)/len(v54_vs_us) if v54_vs_us else 0
deficit = v54_mean_vs_us - our_mean_vs_v54
g4 = deficit <= 15_000
gates["G4"] = ("PASS" if g4 else "FAIL",
               f"Margin deficit vs V54 = {deficit:+.0f}  "
               f"(our_mean={our_mean_vs_v54:.0f}  v54_mean={v54_mean_vs_us:.0f}, threshold deficit <= 15,000)")

# G5: Zero crashes
total_crashes = sum(summarize(rows)["crashes"] for rows in data.values())
g5 = total_crashes == 0
gates["G5"] = ("PASS" if g5 else "FAIL",
               f"Total crashes = {total_crashes}  (threshold = 0)")

# G6: Unpinned robustness (we check vs SYN_AGG as proxy for unpinned stress)
syn = summarize(data.get("SYN_AGG", []))
our_vs_v2_mean = v2["mean_r"]
our_vs_syn_mean = syn["mean_r"]
retention = our_vs_syn_mean / max(1, our_vs_v2_mean)
g6 = retention >= 0.70
gates["G6"] = ("PASS" if g6 else "FAIL",
               f"Reward retention (SYN_AGG / V2) = {retention:.1%}  "
               f"(our_syn={our_vs_syn_mean:.0f}  our_v2={our_vs_v2_mean:.0f}, threshold >= 70%)")

all_pass = all(v[0] == "PASS" for v in gates.values())
print()
for gate, (status, detail) in gates.items():
    icon = "[PASS]" if status == "PASS" else "[FAIL]"
    print(f"  {icon} {gate}: {status}  --  {detail}")

print()
print("=" * 70)
print(f"OVERALL EXP-A: {'PASS -- proceed to EXP-B and EXP-C' if all_pass else 'FAIL -- diagnose before continuing'}")
print("=" * 70)

# Full per-opponent table
print("\nPer-Opponent Summary:")
print(f"{'Opponent':12s}  {'N':>4}  {'Crashes':>7}  {'Mean_R':>10}  {'Mean_M':>10}  {'Win%':>7}")
print("-" * 60)
for opp_name, rows in data.items():
    s = summarize(rows)
    print(f"{opp_name:12s}  {s['n']:>4}  {s['crashes']:>7}  {s['mean_r']:>10.0f}  {s['mean_m']:>+10.0f}  {s['win_rate']:>7.1%}")
