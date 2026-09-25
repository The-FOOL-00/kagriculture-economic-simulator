import json
import numpy as np

with open('candidates/v32_p12_options/reports/p12_master_benchmark_results.json', 'r') as f:
    d = json.load(f)

raw = d['raw']
a7_legs = [r for r in raw if r['policy_name'] == 'P12_Search_Gated']
a7_cash = [r['a7_cash'] for r in a7_legs]

print("=" * 110)
print("A7 BASELINE STATISTICS (60 legs: 5 fresh DEV seeds 249677-249681, 6 opponents, seats 0 & 1)")
print("=" * 110)
print(f"Mean:   ${np.mean(a7_cash):>10,.2f}")
print(f"Median: ${np.median(a7_cash):>10,.2f}")
print(f"P25:    ${np.percentile(a7_cash, 25):>10,.2f}")
print(f"P75:    ${np.percentile(a7_cash, 75):>10,.2f}")
print(f"Min:    ${np.min(a7_cash):>10,.2f}")
print(f"Max:    ${np.max(a7_cash):>10,.2f}")

print("\n" + "=" * 110)
print("POLICY SUMMARIES ACROSS ALL 60 LEGS")
print("=" * 110)
for pol, s in d['policy_summaries'].items():
    print(f"Policy: {pol}")
    print(f"  Mean Cash:         ${s['cand_mean']:>10,.2f}  (A7: ${s['a7_mean']:>10,.2f})")
    print(f"  Median Cash:       ${s['cand_median']:>10,.2f}  (A7: ${s['a7_median']:>10,.2f})")
    print(f"  P25 / P75:         ${s['cand_p25']:>10,.2f} / ${s['cand_p75']:>10,.2f}")
    print(f"  Min Cash:          ${s['cand_min']:>10,.2f}")
    print(f"  Paired Delta Mean: ${s['paired_delta_mean']:>+10,.2f}")
    print(f"  Paired Delta Med:  ${s['paired_delta_median']:>+10,.2f}")
    print(f"  Min Delta (Tail):  ${s['paired_delta_min']:>+10,.2f}")
    print(f"  Max Delta:         ${s['paired_delta_max']:>+10,.2f}")
    print(f"  W / L / T vs Opp:  {s['wins']} / {s['losses']} / {s['ties']}")
    print(f"  Activations:       {s['total_activations']} / {s['legs']}")
    print()

print("=" * 110)
print("OPPONENT-BY-OPPONENT BREAKDOWN (Paired Delta vs A7)")
print("=" * 110)
opps = ['E2_A7', 'E0_V3', 'E8_DMITRII', 'SYN_AGG', 'V54', 'E1_V22R1']
for opp in opps:
    print(f"--- Opponent: {opp} (10 legs) ---")
    for pol in ['P12_Search_Gated', 'P12_Supervised_Selector', 'P12_PPO_Selector']:
        s = d['opp_breakdown'][pol][opp]
        print(f"  {pol:<24} | Delta Mean: ${s['paired_delta_mean']:>+10,.2f} | Med: ${s['paired_delta_median']:>+10,.2f} | Min: ${s['paired_delta_min']:>+10,.2f} | Max: ${s['paired_delta_max']:>+10,.2f} | W/L/T: {s['wins']}/{s['losses']}/{s['ties']} | Opts: {s['total_activations']}/10")
