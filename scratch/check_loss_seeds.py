import sys, os
sys.path.insert(0, 'external_repos/kaggriculture-cppsim')
sys.path.insert(0, 'candidates/closed_loop_architecture')
sys.path.insert(0, 'extracted_agents/dmitrii_lb2800')
sys.path.insert(0, 'scratch')
from forensic_logger_v2 import play_forensic_match

loss_seeds = [50081, 50078, 50022, 50040, 50036, 50108, 50058]
for s in loss_seeds:
    res = play_forensic_match(s, 0)
    v2 = res['v2']
    dm = res['dm']
    w_diff = v2['total_sells_qty'].get('WHEAT', 0) - dm['total_sells_qty'].get('WHEAT', 0)
    str_diff = v2['total_sells_qty'].get('STRAWBERRY', 0) - dm['total_sells_qty'].get('STRAWBERRY', 0)
    wl_diff = v2['total_sells_qty'].get('WOOL', 0) - dm['total_sells_qty'].get('WOOL', 0)
    margin = round(res['paired_margin'] * 2, 1)
    print(f"Seed {s}: combined_margin={margin:+6.0f}  WHEAT diff={w_diff:+3d}  STRAW diff={str_diff:+3d}  WOOL diff={wl_diff:+3d}")
