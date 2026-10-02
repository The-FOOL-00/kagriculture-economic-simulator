import json

with open('research/v57/analysis/STEP697_FORENSICS.json') as f:
    d = json.load(f)

for leg in ['seed_250621_seat_0', 'seed_250617_seat_0']:
    print('='*80)
    print(leg)
    print('='*80)
    for rec in d[leg]['step_records']:
        s = rec['step']
        m = rec['pre_step']['margin']
        m_post = rec['post_step']['margin']
        m49 = rec['v49_market']['full_list']
        m44 = rec['v44_market']['full_list']
        print(f"Step {s:3d} | Pre-marg: {m:>+8.1f} | Post-marg: {m_post:>+8.1f} | V49 cash: {rec['pre_step']['cash_v49']:.1f} | V44 cash: {rec['pre_step']['cash_v44']:.1f}")
        if m49 or m44:
            print(f"  V49 mkt: {m49}")
            print(f"  V44 mkt: {m44}")
            print(f"  Pre-shed 49: {rec['pre_step']['shed_v49']}")
            print(f"  Pre-shed 44: {rec['pre_step']['shed_v44']}")
            print(f"  Post-shed 49: {rec['post_step']['shed_v49']}")
            print(f"  Post-shed 44: {rec['post_step']['shed_v44']}")
            print(f"  Pre-prices: Wool={rec['pre_step']['market_prices'].get('WOOL')} Milk={rec['pre_step']['market_prices'].get('MILK')} Egg={rec['pre_step']['market_prices'].get('EGG')} Carrot={rec['pre_step']['market_prices'].get('CARROT')}")
            print(f"  Post-prices: Wool={rec['post_step']['market_prices'].get('WOOL')} Milk={rec['post_step']['market_prices'].get('MILK')} Egg={rec['post_step']['market_prices'].get('EGG')} Carrot={rec['post_step']['market_prices'].get('CARROT')}")
            print(f"  Pre-inv: Wool={rec['pre_step']['market_inventory'].get('WOOL')} Milk={rec['pre_step']['market_inventory'].get('MILK')} Egg={rec['pre_step']['market_inventory'].get('EGG')} Carrot={rec['pre_step']['market_inventory'].get('CARROT')}")
            print(f"  Post-inv: Wool={rec['post_step']['market_inventory'].get('WOOL')} Milk={rec['post_step']['market_inventory'].get('MILK')} Egg={rec['post_step']['market_inventory'].get('EGG')} Carrot={rec['post_step']['market_inventory'].get('CARROT')}")
