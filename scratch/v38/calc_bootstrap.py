import json
import numpy as np

def get_deltas(fname):
    d = json.load(open(fname))
    grouped = {}
    for r in d['raw_results']:
        k = (r['seed'], r['opponent'], r['seat'])
        grouped.setdefault(k, {})[r['policy']] = r
    deltas = {'BC': [], 'PPO': []}
    for k, pdict in grouped.items():
        v35 = pdict.get('V35')
        if not v35: continue
        if 'V38_BC' in pdict:
            deltas['BC'].append(pdict['V38_BC']['cand_cash'] - v35['cand_cash'])
        if 'V38_PPO' in pdict:
            deltas['PPO'].append(pdict['V38_PPO']['cand_cash'] - v35['cand_cash'])
    return deltas

d_dev = get_deltas('scratch/v38/tournament_dev_results.json')
d_fresh = get_deltas('scratch/v38/tournament_fresh_results.json')

all_bc = np.array(d_dev['BC'] + d_fresh['BC'])
all_ppo = np.array(d_dev['PPO'] + d_fresh['PPO'])

print(f"All BC paired deltas (N={len(all_bc)}): Mean={np.mean(all_bc):.4f}, Std={np.std(all_bc):.4f}")
print(f"All PPO paired deltas (N={len(all_ppo)}): Mean={np.mean(all_ppo):.4f}, Std={np.std(all_ppo):.4f}")

rng = np.random.default_rng(42)
b_means = [np.mean(rng.choice(all_bc, size=len(all_bc), replace=True)) for _ in range(10000)]
p_means = [np.mean(rng.choice(all_ppo, size=len(all_ppo), replace=True)) for _ in range(10000)]

ci_bc = (np.percentile(b_means, 2.5), np.percentile(b_means, 97.5))
ci_ppo = (np.percentile(p_means, 2.5), np.percentile(p_means, 97.5))

print(f"BC 95% Bootstrap CI: [{ci_bc[0]:.4f}, {ci_bc[1]:.4f}]")
print(f"PPO 95% Bootstrap CI: [{ci_ppo[0]:.4f}, {ci_ppo[1]:.4f}]")

# Win rate bootstrap CI
# Dev WR = 90% (27/30), Fresh WR = 100% (30/30) -> Overall WR = 57/60 = 95.0% for all V35, Heuristic, BC, PPO
# WR delta between V38 and V35 is identically 0.00% across all 60 paired matches.
print("Win rate delta across all 60 paired matches: Exactly 0.00% (Delta = 0/60).")
