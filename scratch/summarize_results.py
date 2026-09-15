import os, json, sys
sys.stdout.reconfigure(encoding='utf-8')

results_dir = 'external_repos/lixingtao123-Kaggriculture/results'
summary = []
for f in sorted(os.listdir(results_dir)):
    if f.endswith('.json'):
        p = os.path.join(results_dir, f)
        try:
            with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                d = json.load(fp)
                if 'summary' in d:
                    s = d['summary']
                    cand = s.get('candidate', '').replace('\\', '/').split('/')[-2] if '/' in s.get('candidate', '').replace('\\', '/') else s.get('candidate', '')
                    summary.append((f, cand, s.get('games'), s.get('win_rate'), s.get('mean_margin')))
                elif 'aggregate' in d:
                    a = d['aggregate']
                    summary.append((f, 'replay_agg', a.get('games'), a.get('wins'), a.get('mean_margin')))
        except Exception as e:
            pass

print(f"Total results files parsed: {len(summary)}")
print(f"{'File':50s} | {'Cand/Type':25s} | {'Games':5s} | {'WR/Wins':10s} | {'Mean Margin':12s}")
print('-'*115)
for item in summary:
    f, cand, games, wr, margin = item
    wr_str = f"{wr:.1%}" if isinstance(wr, float) else str(wr)
    m_str = f"{margin:+.1f}" if isinstance(margin, (int, float)) else str(margin)
    print(f"{f:50s} | {str(cand)[-25:]:25s} | {str(games):5s} | {wr_str:10s} | {m_str:12s}")
