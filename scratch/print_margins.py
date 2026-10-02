import json

with open('research/v57/analysis/STEP697_FORENSICS.json') as f:
    d = json.load(f)

for leg in ['seed_250621_seat_0', 'seed_250617_seat_0']:
    print('='*80)
    print('LEG:', leg)
    print('='*80)
    for rec in d[leg]['step_records']:
        s = rec['step']
        m = rec['pre_step']['margin']
        m_post = rec['post_step']['margin']
        m49 = rec['v49_market']['full_list']
        m44 = rec['v44_market']['full_list']
        print(f"Step {s:3d}: Marg {m:>+7.1f} -> {m_post:>+7.1f} | 49: {rec['pre_step']['cash_v49']} -> {rec['post_step']['cash_v49']} | 44: {rec['pre_step']['cash_v44']} -> {rec['post_step']['cash_v44']}")
        if m49 != m44:
            print("   DIFF MKT:")
            print(f"   49: {m49}")
            print(f"   44: {m44}")
