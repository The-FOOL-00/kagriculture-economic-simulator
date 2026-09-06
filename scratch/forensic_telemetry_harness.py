"""
scratch/forensic_telemetry_harness.py
Step-by-step forensic telemetry recorder for V2 vs Closed-Loop Arch v1.
Records full state at every step (0 to 719) across matched seeds.
"""

import sys
sys.path.insert(0, ".")
import json
import kaggle_environments
import candidates.slot2_aethel_refined_v2 as v2
import scratch.closed_loop_arch_v1 as cl_arch

TURNS_PER_DAY = 24

def extract_step_snapshot(obs, private, action, player=0):
    farm = obs["farms"][player]
    day = obs["step"] // TURNS_PER_DAY
    hour = obs["step"] % TURNS_PER_DAY
    
    farmer_pos = tuple(farm.get("farmer", [4, 4]))
    hands_pos = [tuple(h) for h in farm.get("hands", [])]
    all_workers = [farmer_pos] + hands_pos
    
    # Extract crops
    crops = {}
    pastures = {}
    for y, row in enumerate(farm.get("tiles", [])):
        for x, t in enumerate(row):
            if isinstance(t, dict):
                kind = t.get("kind")
                pos_key = f"{x},{y}"
                if kind == "PLANT":
                    crops[pos_key] = {
                        "crop": t.get("crop"),
                        "planted_day": t.get("planted_day"),
                        "age": day - t.get("planted_day", day),
                        "watered_today": bool(t.get("watered_today")),
                        "yield_units": t.get("yield_units", 0),
                        "fertilized_until_day": t.get("fertilized_until_day", -1),
                        "consecutive_unwatered": t.get("consecutive_unwatered", 0)
                    }
                elif kind == "PASTURE":
                    pastures[pos_key] = {
                        "animal": t.get("animal"),
                        "placed_day": t.get("placed_day"),
                        "fed_today": bool(t.get("fed_today")),
                        "cared_today": bool(t.get("cared_today")),
                        "yield_units": t.get("yield_units", 0),
                        "fertilizer_available": bool(t.get("fertilizer_available")),
                        "consecutive_unfed": t.get("consecutive_unfed", 0)
                    }

    return {
        "step": obs["step"],
        "day": day,
        "hour": hour,
        "money": float(farm.get("money", 0)),
        "unlocked_quads": list(farm.get("unlocked_quadrants", [])),
        "worker_count": len(all_workers),
        "worker_positions": all_workers,
        "farmer_action": action.get("farmer", []),
        "hands_actions": action.get("hands", []),
        "market_orders": action.get("market", []),
        "inventories": private.get("inventories", []),
        "shed": private.get("shed", {}).copy(),
        "seeds": private.get("seeds", {}).copy(),
        "crops": crops,
        "pastures": pastures,
    }


def record_trajectory(agent_func, seed, player=0):
    env = kaggle_environments.make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env.reset()
    
    trajectory = []
    
    # We must instantiate a clean agent instance if class-based
    if agent_func == cl_arch.agent:
        active_agent = cl_arch.ClosedLoopArchAgent()
    else:
        active_agent = agent_func
        
    for step in range(719):
        obs0 = env.state[0].observation
        obs1 = env.state[1].observation
        
        if player == 0:
            act0 = active_agent(obs0)
            act1 = v2.agent(obs1) # baseline opponent
            snap = extract_step_snapshot(obs0, obs0["private"], act0, player=0)
        else:
            act0 = v2.agent(obs0)
            act1 = active_agent(obs1)
            snap = extract_step_snapshot(obs1, obs1["private"], act1, player=1)
            
        trajectory.append(snap)
        env.step([act0, act1])
        
    final_reward = env.steps[-1][player]["reward"]
    return trajectory, final_reward


def main():
    target_seeds = [215620170, 108, 201, 105]
    print(f"Starting forensic telemetry capture for seeds: {target_seeds}...")
    
    all_telemetry = {}
    
    for seed in target_seeds:
        print(f"\n--- Recording Seed {seed} ---")
        
        # 1. Record V2
        print("  Recording V2...")
        v2_traj, v2_reward = record_trajectory(v2.agent, seed=seed, player=0)
        print(f"  -> V2 Final Score: ${v2_reward:,.1f}")
        
        # 2. Record Closed-Loop Arch v1
        print("  Recording Closed-Loop Arch v1...")
        cl_traj, cl_reward = record_trajectory(cl_arch.agent, seed=seed, player=0)
        print(f"  -> CL Arch Final Score: ${cl_reward:,.1f}")
        
        all_telemetry[str(seed)] = {
            "v2": {
                "final_reward": v2_reward,
                "trajectory": v2_traj
            },
            "cl": {
                "final_reward": cl_reward,
                "trajectory": cl_traj
            }
        }
        
    out_file = "scratch/forensic_telemetry_dump.json"
    with open(out_file, "w") as f:
        json.dump(all_telemetry, f, indent=2)
        
    print(f"\nAll telemetry successfully saved to {out_file} ({len(json.dumps(all_telemetry))} bytes).")


if __name__ == "__main__":
    main()
