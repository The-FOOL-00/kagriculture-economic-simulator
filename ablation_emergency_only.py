"""
Quick Emergency Liquidity ablation — 100 paired seeds vs Control.
This is the MOST IMPORTANT single ablation (Part 7).
"""
import sys, os
sys.path.insert(0, r'c:\Users\Sundareswaran\Kagriculture')
from tournament_engine import run_paired_tournament

ROOT = r'c:\Users\Sundareswaran\Kagriculture'
def apath(f): return os.path.join(ROOT, 'agents', f)

if __name__ == '__main__':
    ctrl  = apath('slot4_control_frozen_v2.py')
    emerg = apath('ablation_b_emergency_only.py')
    seeds = list(range(50000, 50100))

    print('=== EMERGENCY LIQUIDITY vs CONTROL (100 seeds, 200 paired matches) ===')
    r = run_paired_tournament(emerg, ctrl, seeds=seeds, num_pairs=100, max_workers=6)
    rr = r.get('results', [])
    p0 = [x for x in rr if not x['swapped']]
    p1 = [x for x in rr if x['swapped']]
    p0wr = sum(1 for x in p0 if x['win']==1.0) / max(1, len(p0)) * 100
    p1wr = sum(1 for x in p1 if x['win']==1.0) / max(1, len(p1)) * 100
    cat  = sum(1 for x in rr if x['margin'] < -10000)
    ci_lo, ci_hi = r['ci_95']

    print(f"\n  Emergency vs Control:")
    print(f"  Win Rate:   {r['win_rate']:.1f}% [{ci_lo:.1f}%-{ci_hi:.1f}%]")
    print(f"  P0 WR:      {p0wr:.1f}%  ({len(p0)} games)")
    print(f"  P1 WR:      {p1wr:.1f}%  ({len(p1)} games)")
    print(f"  Mean Cash:  ${r['mean_us']:,.0f} vs ${r['mean_opp']:,.0f}")
    print(f"  Margin:     {r['margin']:+,.0f} +/- {r['std_margin']:,.0f}")
    print(f"  Worst Loss: {r['worst_drawdown']:+,.0f}")
    print(f"  Catastrophic: {cat} ({100*cat/max(1,r['games']):.1f}%)")
    print(f"  Total Games: {r['games']}")

    if r['win_rate'] > 55:
        print("\n  *** RESULT: Emergency Liquidity EXPLAINS H2H advantage ***")
        print("  *** Market predictor adds little on top of this ***")
    elif r['win_rate'] > 50:
        print("\n  RESULT: Emergency Liquidity provides modest improvement")
    else:
        print("\n  RESULT: Emergency Liquidity provides NO improvement vs Control")
        print("  The 66% H2H result must be explained by something else.")
