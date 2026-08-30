"""Quick batch sweep script — 50 seeds, 100 paired matches per batch."""
import sys, os
sys.path.insert(0, r'c:\Users\Sundareswaran\Kagriculture')
from tournament_engine import run_paired_tournament

ROOT = r'c:\Users\Sundareswaran\Kagriculture'
def apath(f): return os.path.join(ROOT, 'agents', f)

configs = [
    (4,  'ablation_batch_4.py'),
    (8,  'ablation_c_batch8_only.py'),
    (12, 'ablation_batch_12.py'),
    (14, 'ablation_batch_14.py'),
    (18, 'ablation_batch_18.py'),
    (24, 'ablation_batch_24.py'),
]

if __name__ == '__main__':
    ctrl  = apath('slot4_control_frozen_v2.py')
    seeds = list(range(50000, 50050))
    print('=== BATCH SWEEP VS CONTROL (50 seeds, 100 paired matches each) ===')
    for b, fname in configs:
        r = run_paired_tournament(apath(fname), ctrl, seeds=seeds, num_pairs=50, max_workers=6)
        rr = r.get('results', [])
        p0 = [x for x in rr if not x['swapped']]
        p1 = [x for x in rr if x['swapped']]
        p0wr = sum(1 for x in p0 if x['win']==1.0) / max(1, len(p0)) * 100
        p1wr = sum(1 for x in p1 if x['win']==1.0) / max(1, len(p1)) * 100
        cat  = sum(1 for x in rr if x['margin'] < -10000)
        wr = r['win_rate']
        ci_lo, ci_hi = r['ci_95']
        marg = r['margin']
        worst = r['worst_drawdown']
        print(f"  Batch {b:2d}: WR={wr:5.1f}% [{ci_lo:.1f}-{ci_hi:.1f}]  P0={p0wr:.0f}%  P1={p1wr:.0f}%  Margin={marg:+.0f}  Worst={worst:+.0f}  Catastrophic={cat}")
