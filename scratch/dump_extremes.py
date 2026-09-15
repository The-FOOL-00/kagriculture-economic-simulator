import json

with open('scratch/200seed_validation_raw.json') as f:
    data = json.load(f)

seeds = sorted([int(s) for s in data['Baseline'].keys()])
items = []
for s in seeds:
    b = data['Baseline'][str(s)]
    g = data['Gated_M1'][str(s)]
    sb = sum(1 for x in b['unlocked_shops'] if x in ('BRUNCH_SPOT', 'ICE_CREAM_SHOP', 'SMOOTHIE_SHOP', 'FARMERS_MARKET'))
    sg = sum(1 for x in g['unlocked_shops'] if x in ('BRUNCH_SPOT', 'ICE_CREAM_SHOP', 'SMOOTHIE_SHOP', 'FARMERS_MARKET'))
    mb = sum(1 for x in b['unlocked_shops'] if x in ('PIZZA_SHOP', 'ICE_CREAM_SHOP', 'SMOOTHIE_SHOP'))
    mg = sum(1 for x in g['unlocked_shops'] if x in ('PIZZA_SHOP', 'ICE_CREAM_SHOP', 'SMOOTHIE_SHOP'))
    
    items.append({
        'seed': s,
        'd_rew': g['reward'] - b['reward'],
        'd_str_rev': g['straw_rev'] - b['straw_rev'],
        'd_mlk_rev': g['milk_rev'] - b['milk_rev'],
        'd_woo_rev': g['wool_rev'] - b['wool_rev'],
        'd_frt_rev': g['fert_rev'] - b['fert_rev'],
        'd_wht_rev': g['wheat_rev'] - b['wheat_rev'],
        'd_mel_rev': g['melon_rev'] - b['melon_rev'],
        'd_exp': g['total_exp'] - b['total_exp'],
        'd_str_shp': sg - sb,
        'd_mlk_shp': mg - mb,
        'base_sp': b['straw_avg_p'], 'gated_sp': g['straw_avg_p'],
        'base_mp': b['milk_avg_p'], 'gated_mp': g['milk_avg_p']
    })

items_sorted = sorted(items, key=lambda x: x['d_rew'])

def dump(title, subset):
    print(f"=== {title} ===")
    for x in subset:
        print(f"Seed {x['seed']}: DeltaReward={x['d_rew']:+8.0f} | dStrawRev={x['d_str_rev']:+8.0f} | dMilkRev={x['d_mlk_rev']:+8.0f} | dWoolRev={x['d_woo_rev']:+7.0f} | dFertRev={x['d_frt_rev']:+6.0f} | dWheatRev={x['d_wht_rev']:+6.0f} | dMelonRev={x['d_mel_rev']:+6.0f} | dExp={x['d_exp']:+6.0f} | dShops: Straw={x['d_str_shp']:+2d} Milk={x['d_mlk_shp']:+2d} | AvgPrice Straw(B/G): {x['base_sp']:.1f}/{x['gated_sp']:.1f} | AvgPrice Milk(B/G): {x['base_mp']:.1f}/{x['gated_mp']:.1f}")

dump("10 WORST SEEDS", items_sorted[:10])
dump("10 BEST SEEDS", items_sorted[-10:][::-1])
