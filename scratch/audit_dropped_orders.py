import sys, os, json
sys.path.insert(0, 'external_repos/kaggriculture-cppsim')
sys.path.insert(0, 'candidates/closed_loop_architecture')
sys.path.insert(0, 'extracted_agents/dmitrii_lb2800')
import kagsim
from closed_loop_v2 import ClosedLoopAgentV2
import importlib.util
from collections import Counter

spec = importlib.util.spec_from_file_location('dmitrii_agent', 'extracted_agents/dmitrii_lb2800/main.py')
dmitrii_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dmitrii_mod)

scan = json.load(open('scratch/v2_dmitrii_margin_scan.json'))
seeds_to_test = [r['seed'] for r in scan['discovery'] if r['v2_seat'] == 0]

dropped_orders_by_type = Counter()
dropped_steps = Counter()
divergences = []

for seed in seeds_to_test:
    g = kagsim.Game(seed)
    v2 = ClosedLoopAgentV2()
    step = 0
    diff_count = 0
    while not g.done:
        obs0 = g.observe(0)
        obs1 = g.observe(1)
        act_v2 = v2.act(obs0)
        act_dm = dmitrii_mod.agent(obs1)
        
        m0 = act_v2.get('market', [])
        m1 = act_dm.get('market', [])
        
        # Check if Dm had an order that V2 didn't have
        s0 = [tuple(x) for x in m0 if x]
        s1 = [tuple(x) for x in m1 if x]
        
        for ord1 in s1:
            if ord1 not in s0:
                dropped_orders_by_type[ord1[0]] += 1
                dropped_steps[step] += 1
        
        g.step(act_v2, act_dm)
        step += 1

print("Total seeds analyzed:", len(seeds_to_test))
print("\nDropped/Missing order types in V2 vs Dm:")
for op, cnt in dropped_orders_by_type.most_common():
    print(f"  {op:15s}: {cnt}")

print("\nMost common steps where orders differed:")
for s, cnt in dropped_steps.most_common(10):
    print(f"  Step {s:3d} (D{s//24:02d}H{s%24:02d}): {cnt} times")
