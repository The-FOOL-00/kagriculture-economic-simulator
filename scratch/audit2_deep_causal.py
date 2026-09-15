import json

def analyze():
    with open('scratch/worst_25_detailed_analysis.json') as f:
        w25 = json.load(f)

    for e in w25:
        s = e['seed']
        d = e['delta']
        c_r = e['cand_reward']
        q_r = e['q50_reward']
        rank = e['rank']
        
        # Determine classification
        # Look at largest revenue/expense driver
        rev_d = e['rev_deltas']
        exp_d = e['exp_deltas']
        qty_d = e['qty_deltas']
        act_d = e['action_deltas']
        
        drivers = []
        for k in ['STRAWBERRY', 'WOOL', 'MILK', 'MELON', 'FERTILIZER', 'WHEAT']:
            v = rev_d.get(k, 0)
            if abs(v) > 200:
                drivers.append((k, v, qty_d.get(k, 0)))
        drivers.sort(key=lambda x: abs(x[1]), reverse=True)
        
        # Check market prices
        # e.g. price per unit = rev / qty
        c_led = e['c_led']
        q_led = e['q_led']
        c_qty = e['c_qty']
        q_qty = e['q_qty']

        price_effects = {}
        for comm in ['STRAWBERRY', 'WOOL', 'MILK', 'MELON', 'FERTILIZER', 'WHEAT']:
            c_p = (c_led.get(f'REV_{comm}', 0) / c_qty.get(comm, 1)) if c_qty.get(comm, 0) > 0 else 0
            q_p = (q_led.get(f'REV_{comm}', 0) / q_qty.get(comm, 1)) if q_qty.get(comm, 0) > 0 else 0
            price_effects[comm] = (c_p, q_p, c_p - q_p)

        # Classification logic:
        # If quantities are identical or nearly identical (<=1 unit diff) but revenue diff is large -> MARKET (price variance)
        # If strawberry quantity is significantly lower -> STRAWBERRY
        # If wool/milk quantity significantly lower -> ANIMAL
        # If melon quantity significantly lower -> MELON
        # If wheat quantity significantly lower -> WHEAT
        # If expense diff is the main driver -> EXPENSE / CAPITAL
        total_qty_diff = sum(abs(v) for v in qty_d.values())
        
        classification = "OTHER"
        if total_qty_diff <= 2 and abs(rev_d['TOTAL_REV_D']) > 500:
            classification = "MARKET"
        elif abs(rev_d.get('STRAWBERRY', 0)) >= 1000 and abs(qty_d.get('STRAWBERRY', 0)) >= 3:
            classification = "STRAWBERRY"
        elif (abs(rev_d.get('WOOL', 0)) >= 800 and abs(qty_d.get('WOOL', 0)) >= 3) or (abs(rev_d.get('MILK', 0)) >= 800 and abs(qty_d.get('MILK', 0)) >= 3):
            classification = "ANIMAL"
        elif abs(rev_d.get('MELON', 0)) >= 800 and abs(qty_d.get('MELON', 0)) >= 3:
            classification = "MELON"
        elif abs(rev_d.get('WHEAT', 0)) >= 800 and abs(qty_d.get('WHEAT', 0)) >= 5:
            classification = "WHEAT"
        elif abs(exp_d['TOTAL_EXP_D']) > 500:
            classification = "EXPENSE"
        else:
            # Check largest single revenue delta
            if drivers:
                top_d = drivers[0][0]
                if abs(drivers[0][2]) <= 1:
                    classification = "MARKET"
                else:
                    classification = top_d
            else:
                classification = "MARKET"

        print(f"Rank {rank:2d} | Seed {s} | Delta: ${d:9.2f} | Cand: ${c_r:9.2f} | Q50: ${q_r:9.2f} | Class: {classification:<10} | Drivers: {drivers[:2]}")
        e['classification'] = classification
        e['price_effects'] = price_effects

    with open('scratch/worst_25_classified.json', 'w') as f:
        json.dump(w25, f, indent=2)

if __name__ == '__main__':
    analyze()
