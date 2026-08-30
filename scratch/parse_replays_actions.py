import os, json, glob
from collections import defaultdict, Counter

replays = sorted(glob.glob('replays/*.json') + glob.glob('*replay*.json'))

parsed_games = []

for rpath in replays:
    try:
        with open(rpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        steps = data.get('steps', [])
        if not steps: continue
        
        p0_reward = steps[-1][0].get('reward', 0)
        p1_reward = steps[-1][1].get('reward', 0)
        
        def extract_agent_stats(player_idx):
            animals = Counter()
            seeds = Counter()
            hires = 0
            lands = 0
            sales = Counter()
            town_sales = Counter()
            opening_actions = []
            
            for t in range(len(steps)):
                step_p = steps[t][player_idx]
                act = step_p.get('action')
                if not act or not isinstance(act, dict):
                    continue
                
                if t <= 10:
                    opening_actions.append((t, act.get('farmer', []), act.get('market', [])))
                
                # Check market commands
                for m_cmd in act.get('market', []):
                    if isinstance(m_cmd, list) and len(m_cmd) > 0:
                        op = m_cmd[0]
                        if op == 'BUY_ANIMAL' and len(m_cmd) >= 2:
                            qty = m_cmd[2] if len(m_cmd) >= 3 else 1
                            animals[m_cmd[1]] += qty
                        elif op == 'BUY_SEED' and len(m_cmd) >= 2:
                            qty = m_cmd[2] if len(m_cmd) >= 3 else 1
                            seeds[m_cmd[1]] += qty
                        elif op == 'HIRE':
                            hires += 1
                        elif op == 'BUY_LAND' or op == 'EXPAND':
                            lands += 1
                        elif op == 'SELL' and len(m_cmd) >= 2:
                            qty = m_cmd[2] if len(m_cmd) >= 3 else 1
                            sales[m_cmd[1]] += qty
                            
                # Check farmer/hands for town sales or actions if any
                for cmd in [act.get('farmer', [])] + act.get('hands', []):
                    if isinstance(cmd, list) and len(cmd) > 0:
                        if cmd[0] == 'SELL_TOWN' or cmd[0] == 'TOWN_SELL':
                            item = cmd[1] if len(cmd) > 1 else 'UNKNOWN'
                            qty = cmd[2] if len(cmd) > 2 else 1
                            town_sales[item] += qty

            return {
                'reward': steps[-1][player_idx].get('reward', 0),
                'animals': dict(animals),
                'seeds': dict(seeds),
                'hires': hires,
                'lands': lands,
                'sales': dict(sales),
                'town_sales': dict(town_sales),
                'opening': opening_actions
            }

        p0_stats = extract_agent_stats(0)
        p1_stats = extract_agent_stats(1)
        
        parsed_games.append({
            'file': os.path.basename(rpath),
            'p0': p0_stats,
            'p1': p1_stats
        })
    except Exception as e:
        print(f"Error {rpath}: {e}")

print(f"Parsed {len(parsed_games)} replay games successfully.")

# Group by winner and analyze winning archetypes
print("\n=== TOP WINNING PERFORMANCES IN REPLAYS (>$50k) ===")
top_performers = []
for g in parsed_games:
    if g['p0']['reward'] > 45000:
        top_performers.append(('P0', g['file'], g['p0'], g['p1']['reward']))
    if g['p1']['reward'] > 45000:
        top_performers.append(('P1', g['file'], g['p1'], g['p0']['reward']))

top_performers.sort(key=lambda x: x[2]['reward'], reverse=True)
for side, fname, stats, opp_reward in top_performers[:15]:
    print(f"[{side}] ${stats['reward']:,.0f} vs ${opp_reward:,.0f} | {fname[:28]}")
    print(f"    Animals: {stats['animals']}")
    print(f"    Seeds: {stats['seeds']}")
    print(f"    Hires: {stats['hires']}, Lands: {stats['lands']}")
    print(f"    Sales summary: {stats['sales']}")
    print(f"    Town sales: {stats['town_sales']}")
    print()

# Check opening determinism across the top performers
print("=== CHECKING OPENING DETERMINISM OF TOP PERFORMERS ===")
openings = defaultdict(list)
for side, fname, stats, opp_reward in top_performers:
    op_summary = []
    for t, farmer, market in stats['opening'][:5]:
        m_str = ";".join([f"{c[0]}_{c[1] if len(c)>1 else ''}" for c in market])
        op_summary.append(f"T{t}:{m_str}")
    op_key = " | ".join(op_summary)
    openings[op_key].append(fname)

for op_key, fnames in sorted(openings.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"Pattern ({len(fnames)} games): {op_key[:100]}...")
