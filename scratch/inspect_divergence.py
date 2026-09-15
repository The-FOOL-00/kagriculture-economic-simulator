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
v2_agent = ClosedLoopAgentV2()

target_steps = [164, 165, 177, 178, 429, 430, 696, 718]
step = 0
while not g.done:
    obs0 = g.observe(0)
    obs1 = g.observe(1)
    act_v2 = v2_agent.act(obs0)
    act_dm = dmitrii_mod.agent(obs1)
    
    if step in target_steps:
        p0_cash = obs0['farms'][0]['money']
        p1_cash = obs1['farms'][1]['money']
        pr = obs0['market']['prices']
        print(f"Step {step:3d} (D{step//24:02d}H{step%24:02d}):")
        print(f"  Prices: WOOL={pr.get('WOOL')} WHEAT={pr.get('WHEAT')} STRAW={pr.get('STRAWBERRY')}")
        print(f"  V2 cash={p0_cash:.0f} shed={dict(obs0['private']['shed'])} mkt={act_v2.get('market')}")
        print(f"  Dm cash={p1_cash:.0f} shed={dict(obs1['private']['shed'])} mkt={act_dm.get('market')}")
    
    g.step(act_v2, act_dm)
    step += 1
