import kagsim, os, sys
sys.path.insert(0, 'external_repos/kaggriculture-cppsim')
sys.path.insert(0, 'extracted_agents/dmitrii_lb2800')
sys.path.insert(0, 'candidates/closed_loop_architecture')
sys.path.insert(0, 'scratch')
from run_phase17_statistical_validation import ShopConditionedSpecialistAgent, ClosedLoopAgentV2
import router_parent as mod_r

for s in range(50050, 50100):
    g1 = kagsim.Game(s)
    sp1 = ShopConditionedSpecialistAgent()
    d1 = mod_r.Policy('extracted_agents/dmitrii_lb2800')
    while not g1.done:
        g1.step(sp1.act(g1.observe(0)), d1.act(g1.observe(1)))
    diff1 = g1.reward(0) - g1.reward(1)
    if diff1 < -2000 or diff1 > 2000:
        shops = g1.observe(0)["town"]["unlocked_shops"]
        print(f"Seed {s} Seat 0: diff={diff1:+,.0f} (A={g1.reward(0):,.0f}, B={g1.reward(1):,.0f}) | shops={shops}", flush=True)

    g2 = kagsim.Game(s)
    sp2 = ShopConditionedSpecialistAgent()
    d2 = mod_r.Policy('extracted_agents/dmitrii_lb2800')
    while not g2.done:
        g2.step(d2.act(g2.observe(0)), sp2.act(g2.observe(1)))
    diff2 = g2.reward(1) - g2.reward(0)
    if diff2 < -2000 or diff2 > 2000:
        shops = g2.observe(0)["town"]["unlocked_shops"]
        print(f"Seed {s} Seat 1: diff={diff2:+,.0f} (A={g2.reward(1):,.0f}, B={g2.reward(0):,.0f}) | shops={shops}", flush=True)
