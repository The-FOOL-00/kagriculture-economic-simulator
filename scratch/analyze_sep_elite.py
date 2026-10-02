import json, gzip
from pathlib import Path
from collections import Counter, defaultdict

TOP = {'DSM', 'Majkel1337'}
files = list(Path('research/v60/data/sep_replays').glob('*.json.gz'))
print(f'Analyzing {len(files)} episodes...')

stats = defaultdict(lambda: {
    'worker_counts': [], 'market_buys': Counter(), 'market_sells': Counter(),
    'farmer_acts': Counter(), 'animal_buys': Counter(), 'scores': []
})

for f in files:
    try:
        d = json.loads(gzip.open(f).read())
        teams = d.get('info', {}).get('TeamNames', [])
        rewards = d.get('rewards', [0, 0])
        steps = d.get('steps', [])
        for i, team in enumerate(teams):
            if team not in TOP:
                continue
            stats[team]['scores'].append(rewards[i] if i < len(rewards) else 0)
            for step in steps:
                if i >= len(step):
                    continue
                act = step[i].get('action', {})
                if not isinstance(act, dict):
                    continue
                hands = act.get('hands', [])
                if hands:
                    stats[team]['worker_counts'].append(len(hands))
                farmer = act.get('farmer', [])
                if farmer:
                    stats[team]['farmer_acts'][farmer[0]] += 1
                for m in act.get('market', []):
                    if not m:
                        continue
                    mtype = m[0]
                    if mtype == 'BUY_ANIMAL' and len(m) > 1:
                        stats[team]['animal_buys'][m[1]] += 1
                    elif mtype == 'SELL' and len(m) > 1:
                        stats[team]['market_sells'][m[1]] += 1
                    elif mtype == 'BUY_PRODUCT' and len(m) > 1:
                        stats[team]['market_buys'][m[1]] += 1
                    elif mtype == 'HIRE':
                        stats[team]['market_buys']['HIRE'] += 1
    except Exception:
        pass

for team in TOP:
    s = stats[team]
    avg_w = sum(s['worker_counts']) / len(s['worker_counts']) if s['worker_counts'] else 0
    avg_score = sum(s['scores']) / len(s['scores']) if s['scores'] else 0
    print(f'\n=== {team} ===')
    print(f'  Avg final score :  {avg_score:.0f}')
    print(f'  Avg worker count:  {avg_w:.1f}')
    print(f'  Farmer actions  :  {dict(s["farmer_acts"].most_common(8))}')
    print(f'  Animals bought  :  {dict(s["animal_buys"].most_common())}')
    print(f'  Sells           :  {dict(s["market_sells"].most_common())}')
    print(f'  Buys / Hires    :  {dict(s["market_buys"].most_common())}')
