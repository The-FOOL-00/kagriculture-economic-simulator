import json
import numpy as np

def analyze_raw(fname):
    with open(fname, 'r') as f:
        data = json.load(f)
    raw = data['raw_results']
    print(f"\n================ Raw Analysis for {fname} ================")
    # group by (seed, opponent, seat)
    grouped = {}
    for r in raw:
        key = (r['seed'], r['opponent'], r['seat'])
        if key not in grouped:
            grouped[key] = {}
        grouped[key][r['policy']] = r
    
    # Check outcomes
    loss_keys = []
    deltas = { 'V38_HEURISTIC': [], 'V38_BC': [], 'V38_PPO': [] }
    for key, pdict in grouped.items():
        v35 = pdict.get('V35')
        if not v35:
            continue
        v35_won = (v35['win'] == 1.0)
        v35_cash = v35['cand_cash']
        if not v35_won:
            loss_keys.append((key, v35['cand_cash'], v35['opp_cash']))
        for pol in ['V38_HEURISTIC', 'V38_BC', 'V38_PPO']:
            cand = pdict.get(pol)
            if cand:
                delta = cand['cand_cash'] - v35_cash
                deltas[pol].append(delta)
    
    print(f"Total paired scenarios: {len(grouped)}")
    print(f"V35 non-wins ({len(loss_keys)}):")
    for k, my_c, opp_c in loss_keys:
        print(f"  Seed {k[0]}, Opp {k[1]}, Seat {k[2]}: V35 Cash=${my_c:.1f}, Opp Cash=${opp_c:.1f}")
        for pol in ['V38_HEURISTIC', 'V38_BC', 'V38_PPO']:
            c = grouped[k].get(pol)
            if c:
                print(f"    {pol:15s}: Cash=${c['cand_cash']:.1f}, Won={c['win']}, Interventions={c.get('interventions', 0)}")

    for pol, dlist in deltas.items():
        if len(dlist) > 0:
            arr = np.array(dlist)
            print(f"{pol:15s} paired cash delta: Mean={np.mean(arr):.4f}, Std={np.std(arr):.4f}, Min={np.min(arr):.4f}, Max={np.max(arr):.4f}")

analyze_raw('scratch/v38/tournament_dev_results.json')
analyze_raw('scratch/v38/tournament_fresh_results.json')
