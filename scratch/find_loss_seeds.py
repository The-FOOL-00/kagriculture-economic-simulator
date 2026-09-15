"""Check existing results for large loss seeds."""
import json, os

for fname in os.listdir('scratch'):
    if not fname.endswith('.json'):
        continue
    fl = fname.lower()
    if not any(x in fl for x in ['dmitrii', 'h2h', 'bench', 'v2', 'audit']):
        continue
    try:
        d = json.load(open(f'scratch/{fname}'))
        if isinstance(d, dict) and 'matches' in d:
            matches = d['matches']
            losses = [m for m in matches if isinstance(m, dict) and m.get('margin', 0) < -1000]
            n = len(matches)
            print(f"{fname}: {n} matches, {len(losses)} large losses")
            if losses:
                worst = sorted(losses, key=lambda x: x.get('margin', 0))[:5]
                print("  Worst:", [(m.get('seed'), m.get('margin', '?')) for m in worst])
        elif isinstance(d, list) and len(d) > 0 and isinstance(d[0], dict):
            losses = [m for m in d if m.get('margin', 0) < -1000]
            print(f"{fname}: list of {len(d)}, {len(losses)} large losses")
            if losses:
                worst = sorted(losses, key=lambda x: x.get('margin', 0))[:5]
                print("  Worst:", [(m.get('seed'), m.get('margin', '?')) for m in worst])
    except Exception as e:
        pass
