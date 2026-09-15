import sys, os
sys.path.insert(0, 'external_repos/kaggriculture-cppsim')
sys.path.insert(0, 'candidates/closed_loop_architecture')
sys.path.insert(0, 'extracted_agents/dmitrii_lb2800')
import kagsim
from closed_loop_v2 import ClosedLoopAgentV2
import importlib.util

spec = importlib.util.spec_from_file_location('dmitrii_agent', 'extracted_agents/dmitrii_lb2800/main.py')
dmitrii_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dmitrii_mod)

g = kagsim.Game(50081)
v2 = ClosedLoopAgentV2()
step = 0
while not g.done:
    obs0 = g.observe(0)
    obs1 = g.observe(1)
    act_v2 = v2.act(obs0)
    act_dm = dmitrii_mod.agent(obs1)
    
    if step >= 696:
        p0_cash = obs0['farms'][0]['money']
        p1_cash = obs1['farms'][1]['money']
        s0 = dict(obs0['private']['shed'])
        s1 = dict(obs1['private']['shed'])
        m0 = act_v2.get('market', [])
        m1 = act_dm.get('market', [])
        if m0 != m1 or step in [696, 717, 718]:
            print(f"Step {step} (D{step//24:02d}H{step%24:02d}): cash gap={p0_cash-p1_cash:+.0f}")
            print(f"  V2 cash={p0_cash:.0f} shed={s0} mkt={m0}")
            print(f"  Dm cash={p1_cash:.0f} shed={s1} mkt={m1}")
    
    g.step(act_v2, act_dm)
    step += 1

print("Final cash V2:", g.observe(0)['farms'][0]['money'])
print("Final cash Dm:", g.observe(1)['farms'][1]['money'])
