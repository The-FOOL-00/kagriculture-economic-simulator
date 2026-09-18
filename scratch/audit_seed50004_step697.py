import sys
import os
import json

base_dir = os.path.abspath(".")
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

import kagsim
from scripts.run_resource_microvalidation import MicroValidationTreatmentAgent, FrozenV3ControlAgent

def main():
    seed = 50004
    seat = 0
    treat_agent = MicroValidationTreatmentAgent(arm_name="EMERGENCY_FEED_ONLY")
    ctrl_agent = FrozenV3ControlAgent()
    game = kagsim.Game(seed)

    while not game.done:
        step = game.step_count
        obs0 = game.observe(0)
        obs1 = game.observe(1)

        act0 = treat_agent.act(obs0)
        act1 = ctrl_agent.act(obs1)

        telem = treat_agent.executor.latest_telemetry
        if telem is not None:
            td = telem.to_dict()
            cands = td.get("candidates", [])
            feed_cands = [c for c in cands if c.get("mechanism_family") == "EMERGENCY_FEED_PURCHASE"]
            if feed_cands or step >= 690:
                print(f"--- STEP {step} (Day {step // 24}, Hour {step % 24}) ---")
                print(f"Events: {td.get('events')}")
                print(f"Decision: {td.get('decision')}, Abstain reason: {td.get('abstain_reason')}")
                for fc in feed_cands:
                    print(f"Candidate: {fc.get('candidate_id')}")
                    print(f"  Safety pass: {fc.get('safety_pass')}, Reason: {fc.get('safety_fail_reason')}")
                    print(f"  Sim pass: {fc.get('simulation_pass')}, Delta money: {fc.get('delta_money')}")
                if step == 697 or feed_cands:
                    obs = obs0
                    print(f"Cash: {obs['farms'][0]['money']}")
                    print(f"Shed: {obs.get('private', {}).get('shed', {})}")
                    print(f"Market prices: {obs['market']['prices']}")
                    # Check tiles for animals
                    animals = []
                    for r_i, row in enumerate(obs['farms'][0]['tiles']):
                        for c_i, tile in enumerate(row):
                            if isinstance(tile, dict) and "animal" in tile:
                                animals.append((r_i, c_i, tile))
                    print(f"Animals: {animals}")

        game.step(act0, act1)

    r0 = game.reward(0)
    r1 = game.reward(1)
    print(f"Final: Treat={r0}, Ctrl={r1}, Delta={r0-r1}")

if __name__ == "__main__":
    main()
