import os
import sys
import copy
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v35_a7_opening.main import V35OpeningController
from research.v40.env.fast_sim import FastKagricultureSim
from research.v40.policy.actions import StrategicMacroExecutor, ACTION_NAMES, NUM_MACRO_ACTIONS, get_macro_action_mask
from candidates.v32_rlx2.opponents import load_league_opponent

def run_match_with_forced_macro(action_id: int, trigger_step: int, seed: int = 249635, opp_id: str = "E8_DMITRII"):
    # Run clean baseline first
    sim_base = FastKagricultureSim(seed=seed)
    v35_base = V35OpeningController()
    opp_base = load_league_opponent(opp_id)
    obs0, obs1 = sim_base.reset(seed=seed)
    while not sim_base.done:
        act0 = v35_base.act(obs0)
        act1 = opp_base(obs1)
        [obs0, obs1], _, _, _ = sim_base.step([act0, act1])
    r0_base = float(sim_base.state[0].reward or 0.0)

    # Run with forced macro action
    sim_test = FastKagricultureSim(seed=seed)
    v35_test = V35OpeningController()
    executor = StrategicMacroExecutor()
    opp_test = load_league_opponent(opp_id)
    obs0, obs1 = sim_test.reset(seed=seed)
    applied = False
    actual_step = -1

    while not sim_test.done:
        step = int(obs0.get("step", 0) or 0)
        base_act = v35_test.act(obs0)
        act1 = opp_test(obs1)

        mask = get_macro_action_mask(obs0, player=0)
        if not applied and step >= trigger_step and mask[action_id]:
            act0 = executor.execute(action_id, base_act, obs0, player=0)
            applied = True
            actual_step = step
        else:
            act0 = base_act

        [obs0, obs1], _, _, _ = sim_test.step([act0, act1])

    r0_test = float(sim_test.state[0].reward or 0.0)
    delta = r0_test - r0_base
    return {
        "action_id": action_id,
        "name": ACTION_NAMES[action_id],
        "applied": applied,
        "step": actual_step,
        "r0_base": r0_base,
        "r0_test": r0_test,
        "delta": delta
    }

if __name__ == "__main__":
    print(f"{'ID':<3} | {'Action Name':<28} | {'Applied':<7} | {'Step':<5} | {'Base $':<9} | {'Test $':<9} | {'Delta $':<10}")
    print("-" * 85)
    for aid in range(1, NUM_MACRO_ACTIONS):
        # find typical step for each
        step_target = 200
        if "TERMINAL" in ACTION_NAMES[aid] or "EARLY_SHED" in ACTION_NAMES[aid]:
            step_target = 680
        elif "EXPAND" in ACTION_NAMES[aid]:
            step_target = 280
        elif "HIRE" in ACTION_NAMES[aid] or "FREEZE" in ACTION_NAMES[aid]:
            step_target = 240
        elif "LIVESTOCK" in ACTION_NAMES[aid]:
            step_target = 250
        elif "MELON" in ACTION_NAMES[aid]:
            step_target = 250

        res = run_match_with_forced_macro(aid, step_target)
        print(f"{res['action_id']:<3} | {res['name']:<28} | {str(res['applied']):<7} | {res['step']:<5} | ${res['r0_base']:<8.0f} | ${res['r0_test']:<8.0f} | ${res['delta']:<9.0f}")
