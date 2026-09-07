import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
from candidates.candidate_closed_loop_execution_v1 import agent as v1_agent

def find_pass_reasons(seed=42):
    pass_details = []
    
    # We can inspect the internal agent state by calling ClosedLoopExecutionV1 methods
    from candidates.candidate_closed_loop_execution_v1 import _AGENT, BOARD, TPD, _nearest_shed, _dist, _quad
    
    def wrapped_agent(obs, config=None):
        step = int(obs.get("step", 0) or 0)
        day = step // TPD
        hour = step % TPD
        p = int(obs.get("player", 0) or 0)
        farm = obs["farms"][p]
        tiles = farm["tiles"]
        priv = obs.get("private", {})
        shed = priv.get("shed", {})
        seeds = priv.get("seeds", {})
        invs = priv.get("inventories", [])
        quads = farm.get("unlocked_quadrants", ["NW"])
        
        workers = [tuple(farm["farmer"])] + [tuple(h) for h in (farm.get("hands") or [])]
        
        # Run scan
        scan = _AGENT._scan_field(tiles, quads, seeds, shed, invs, day)
        
        # Run agent
        act = v1_agent(obs)
        all_ops = [act.get("farmer", ["PASS"])] + (act.get("hands", []) or [])
        
        for w_i, a in enumerate(all_ops):
            if a and a[0] == "PASS":
                # Worker is passing! Why?
                w_pos = workers[w_i]
                pass_details.append({
                    "step": step, "day": day, "hour": hour, "worker": w_i, "pos": w_pos,
                    "unwatered_total": len(scan["unwatered"]),
                    "hungry_total": len(scan["hungry"]),
                    "ripe_crops": len(scan["ripe_crops"]),
                    "ripe_a": len(scan["ripe_a"]),
                    "fert": len(scan["fert"]),
                    "weeds": len(scan["weeds"]),
                    "unbuilt": len(scan["unbuilt_p"]),
                    "plant_s": len(scan["plant_s"]),
                })
        return act

    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.run([wrapped_agent, "starter"])
    
    print(f"Total passes recorded: {len(pass_details)}")
    print("\nSample 10 passes:")
    for pd in pass_details[100:110]:
        print(f"  Step {pd['step']:3d} (D{pd['day']:02d}:H{pd['hour']:02d}) W{pd['worker']} at {pd['pos']}: "
              f"unwatered={pd['unwatered_total']}, hungry={pd['hungry_total']}, ripe_crops={pd['ripe_crops']}, weeds={pd['weeds']}")

if __name__ == "__main__":
    find_pass_reasons()
