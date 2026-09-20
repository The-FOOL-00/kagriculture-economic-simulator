import sys
sys.path.insert(0, ".")
import kagsim
from aec.ir.economic_state import build_economic_state
from aec.opportunities.town_cycle import TownCycleSignalDetector
from aec.patches.generator import PatchGenerator
from aec.counterfactual.simulator import CounterfactualSimulator
from aec.integration.backbone_adapter import BackboneAdapter

game = kagsim.Game(249171)
adapter = BackboneAdapter()
opp_adapter = BackboneAdapter()

step = 0
while not game.done:
    obs = game.observe(0)
    opp_obs = game.observe(1)
    if step == 427:
        econ = build_economic_state(obs)
        base_res = adapter.query(obs)
        base_act = base_res.canonical_action_copy()
        n_hands = max(0, len(econ.workers.workers) - 1)
        base_cont = adapter.get_future_trajectory(step=step, horizon=18, player=econ.player, n_hands=n_hands)
        
        opps = TownCycleSignalDetector().detect(econ, base_act)
        gen = PatchGenerator(enabled_mechanisms={"TOWN_CYCLE"})
        patches = gen.generate_patches(opps, econ, base_act, baseline_continuation=base_cont)
        
        sim = CounterfactualSimulator()
        p = next(p for p in patches if "427" in p.patch_id)
        outcome = sim.simulate(p, econ, base_act, base_cont, horizon=18, trace=True)
        
        print("Candidate Final Money:", outcome.candidate_final_money)
        print("Baseline Final Money:", outcome.baseline_final_money)
        print("Delta Money:", outcome.delta_our_money)
        print("Candidate Rows:")
        for r in outcome.candidate_trace or []:
            print("  Cand Step:", r.get("step"), "Money:", r.get("cash"), "Shed:", r.get("shed"))
        print("Baseline Rows:")
        for r in outcome.baseline_trace or []:
            print("  Base Step:", r.get("step"), "Money:", r.get("cash"), "Shed:", r.get("shed"))
        break
        
    act0 = adapter.query(obs).action
    act1 = opp_adapter.query(opp_obs).action
    game.step(act0, act1)
    step += 1
