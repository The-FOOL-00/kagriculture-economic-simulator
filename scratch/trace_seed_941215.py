import sys
import os
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))

from scratch.qualification_counterfactual_suite import BaseQ50Agent, L_MinimalAgent

def trace_seed_941215():
    seed = 941215
    print(f"Tracing turn-by-turn divergence on Seed {seed}...")

    # Run Q50
    q_agent = BaseQ50Agent(50)
    env_q = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    steps_q = env_q.run([q_agent, "starter"])

    # Run Candidate
    c_agent = L_MinimalAgent(50)
    env_c = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    steps_c = env_c.run([c_agent, "starter"])

    # Find first turn of divergence in actions or state
    div_step = None
    for s in range(len(steps_q)):
        act_q = steps_q[s][0]["action"]
        act_c = steps_c[s][0]["action"]
        if act_q != act_c:
            div_step = s
            print(f"\nFirst Action Divergence at Step {s} (Day {s // 24}, Hour {s % 24}):")
            print(f"  Q50 Action:       {act_q}")
            print(f"  Candidate Action: {act_c}")
            break

    # Look at crop tiles at divergence and later steps
    def get_farm_info(step_data):
        obs = step_data[0]["observation"]
        f = obs["farms"][0]
        tiles = f["tiles"]
        # count ripe crops and weeds
        straws = 0
        melons = 0
        wheats = 0
        weeds = 0
        straw_yields = []
        for r in range(len(tiles)):
            for c in range(len(tiles[r])):
                t = tiles[r][c]
                if isinstance(t, dict):
                    crop = t.get("crop")
                    yu = t.get("yield_units", 0)
                    if crop == "STRAWBERRY":
                        straws += 1
                        straw_yields.append(yu)
                    elif crop == "MELON":
                        melons += 1
                    elif crop == "WHEAT":
                        wheats += 1
                    elif t.get("kind") == "WEED":
                        weeds += 1
        return {
            "money": f["money"],
            "straws": straws,
            "straw_yields": straw_yields,
            "melons": melons,
            "wheats": wheats,
            "weeds": weeds,
            "shed": obs["private"]["shed"]
        }

    info_q_div = get_farm_info(steps_q[div_step])
    info_c_div = get_farm_info(steps_c[div_step])
    print(f"\nState at Step {div_step}:")
    print(f"  Q50: {info_q_div}")
    print(f"  Cand: {info_c_div}")

    # Trace strawberry harvests and plant lifecycle across all 720 steps
    for s in range(div_step, min(div_step + 100, 720)):
        act_q = steps_q[s][0]["action"]
        act_c = steps_c[s][0]["action"]
        if act_q != act_c:
            info_q = get_farm_info(steps_q[s])
            info_c = get_farm_info(steps_c[s])
            if s % 12 == 0 or info_q["shed"]["STRAWBERRY"] != info_c["shed"]["STRAWBERRY"]:
                print(f"Step {s} (D{s//24}H{s%24}): Q_shed_straw={info_q['shed']['STRAWBERRY']}, C_shed_straw={info_c['shed']['STRAWBERRY']} | Q_shed_melon={info_q['shed']['MELON']}, C_shed_melon={info_c['shed']['MELON']}")

    # Check terminal state
    final_q = get_farm_info(steps_q[-1])
    final_c = get_farm_info(steps_c[-1])
    print(f"\nFinal Step 719 State:")
    print(f"  Q50 Reward: ${steps_q[-1][0]['reward']:.2f}")
    print(f"  Cand Reward: ${steps_c[-1][0]['reward']:.2f}")
    print(f"  Q50 Shed: {final_q['shed']}")
    print(f"  Cand Shed: {final_c['shed']}")

if __name__ == "__main__":
    trace_seed_941215()
