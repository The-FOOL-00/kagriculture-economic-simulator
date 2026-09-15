import sys, os, json, copy
sys.path.insert(0, 'external_repos/kaggriculture-cppsim')
sys.path.insert(0, 'candidates/closed_loop_architecture')
sys.path.insert(0, 'extracted_agents/dmitrii_lb2800')
import kagsim
from closed_loop_v2 import ClosedLoopAgentV2
import importlib.util

spec = importlib.util.spec_from_file_location('dmitrii_agent', 'extracted_agents/dmitrii_lb2800/main.py')
dmitrii_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dmitrii_mod)

# Define Counterfactual Agent: exactly V2, but at Step 696 ensures SELL WHEAT 36 is not dropped
class V2Counterfactual(ClosedLoopAgentV2):
    def act(self, obs):
        action = super().act(obs)
        step = int(obs.get("step", 0))
        if step == 696:
            # Check if Dmitrii's tape had SELL WHEAT 36
            # In Dmitrii, order 0 was SELL WHEAT 36, and orders 1-9 were HIRE
            # If our market orders have HIRE and SELL STRAWBERRY, what if we keep SELL WHEAT 36?
            # E.g. replace SELL STRAWBERRY 4 with SELL WHEAT 36, or put SELL WHEAT 36 in slot 0 like Dmitrii?
            m = action.get("market", [])
            # Let's see: Dmitrii has [['SELL', 'WHEAT', 36], 9 HIREs]
            action["market"] = [['SELL', 'WHEAT', 36]] + [o for o in m if o[0] == 'HIRE'][:9]
        return action

# Test on the worst loss seeds
loss_seeds = [50081, 50078, 50022, 50040, 50036, 50108, 50058]
print(f"{'Seed':8s}  {'V2 Combined':>12s}  {'CF Combined':>12s}  {'Improvement':>12s}")
print("-" * 50)

for s in loss_seeds:
    # Standard V2 vs Dm (CRN paired)
    g0 = kagsim.Game(s)
    v2_0 = ClosedLoopAgentV2()
    while not g0.done:
        g0.step(v2_0.act(g0.observe(0)), dmitrii_mod.agent(g0.observe(1)))
    m0 = g0.observe(0)['farms'][0]['money'] - g0.observe(1)['farms'][1]['money']

    g1 = kagsim.Game(s)
    v2_1 = ClosedLoopAgentV2()
    while not g1.done:
        g1.step(dmitrii_mod.agent(g1.observe(0)), v2_1.act(g1.observe(1)))
    m1 = g1.observe(1)['farms'][1]['money'] - g1.observe(0)['farms'][0]['money']
    v2_comb = m0 + m1

    # Counterfactual V2 vs Dm (CRN paired)
    g0_cf = kagsim.Game(s)
    cf_0 = V2Counterfactual()
    while not g0_cf.done:
        g0_cf.step(cf_0.act(g0_cf.observe(0)), dmitrii_mod.agent(g0_cf.observe(1)))
    m0_cf = g0_cf.observe(0)['farms'][0]['money'] - g0_cf.observe(1)['farms'][1]['money']

    g1_cf = kagsim.Game(s)
    cf_1 = V2Counterfactual()
    while not g1_cf.done:
        g1_cf.step(dmitrii_mod.agent(g1_cf.observe(0)), cf_1.act(g1_cf.observe(1)))
    m1_cf = g1_cf.observe(1)['farms'][1]['money'] - g1_cf.observe(0)['farms'][0]['money']
    cf_comb = m0_cf + m1_cf

    diff = cf_comb - v2_comb
    print(f"{s:8d}  {v2_comb:>+12.0f}  {cf_comb:>+12.0f}  {diff:>+12.0f}")
