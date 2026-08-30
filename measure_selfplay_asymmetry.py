"""
CONTROL SELF-PLAY ASYMMETRY TEST
Run control vs control to measure the intrinsic P0/P1 bias in seeds 50000-50099.
This establishes the baseline before attributing win rates to any strategy.
"""
import sys, os
sys.path.insert(0, r'c:\Users\Sundareswaran\Kagriculture')
from tournament_engine import run_paired_tournament

ROOT = r'c:\Users\Sundareswaran\Kagriculture'
def apath(f): return os.path.join(ROOT, 'agents', f)

if __name__ == '__main__':
    ctrl = apath('slot4_control_frozen_v2.py')
    seeds = list(range(50000, 50100))

    print('=== CONTROL SELF-PLAY: Measuring P0/P1 Baseline Asymmetry ===')
    print('(ctrl vs ctrl — any non-50% result is pure seed-level asymmetry)\n')

    r = run_paired_tournament(ctrl, ctrl, seeds=seeds, num_pairs=100, max_workers=6)
    rr = r.get('results', [])
    p0 = [x for x in rr if not x['swapped']]
    p1 = [x for x in rr if x['swapped']]
    p0wr = sum(1 for x in p0 if x['win'] == 1.0) / max(1, len(p0)) * 100
    p1wr = sum(1 for x in p1 if x['win'] == 1.0) / max(1, len(p1)) * 100
    pool_wr = r['win_rate']
    ci_lo, ci_hi = r['ci_95']

    print(f"  P0 Win Rate (ctrl as P0): {p0wr:.1f}%  ({len(p0)} games)")
    print(f"  P1 Win Rate (ctrl as P1): {p1wr:.1f}%  ({len(p1)} games)")
    print(f"  Pooled WR:                {pool_wr:.1f}% [{ci_lo:.1f}%-{ci_hi:.1f}%]")
    print(f"  Mean Cash (us):           ${r['mean_us']:,.0f}")
    print(f"  Mean Cash (opp):          ${r['mean_opp']:,.0f}")
    print(f"  Mean Margin:              {r['margin']:+,.0f}")
    print(f"  Side Asymmetry:           {p0wr - p1wr:+.1f}pp  (P0 advantage)")
    print()
    if abs(p0wr - p1wr) > 10:
        print(f"  *** STRONG BASELINE ASYMMETRY: {p0wr-p1wr:.1f}pp ***")
        print(f"  *** Seeds 50000-50099 structurally favour P0 ***")
        print(f"  *** Any candidate showing <{p0wr:.0f}% P0 WR is WORSE than control ***")
        print(f"  *** Any candidate showing >{p1wr:.0f}% P1 WR is BETTER than control ***")
        print()
        print(f"  IMPLICATION: The Emergency agent's 55% pooled WR (P0=66%, P1=44%)")
        print(f"  must be compared against this baseline, not against 50%.")
