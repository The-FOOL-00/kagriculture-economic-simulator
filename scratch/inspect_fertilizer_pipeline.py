from collections import Counter
from kaggle_environments import make

def inspect_fert(agent_path, seed=1000):
    cfg = {"episodeSteps": 720, "seed": seed}
    env = make("kaggriculture", configuration=cfg, debug=False)
    env.run([agent_path, "starter"])
    
    collects = 0
    ferts_applied = 0
    ferts_sold = 0
    fertilizer_left_on_tiles = 0
    fertilizer_in_shed = 0
    fertilizer_in_pockets = 0
    
    for s in env.steps:
        act = s[0].get("action", {}) or {}
        units = [act.get("farmer", [])] + act.get("hands", [])
        for u in units:
            if u:
                if u[0] == "COLLECT_FERTILIZER": collects += 1
                elif u[0] == "FERTILIZE": ferts_applied += 1
        for o in act.get("market", []):
            if o[0] == "SELL" and o[1] == "FERTILIZER":
                ferts_sold += int(o[2])
                
    last_step = env.steps[-1][0]
    farm = last_step["observation"]["farms"][0]
    priv = last_step["observation"]["private"]
    
    for row in farm.get("tiles", []):
        for t in row:
            if isinstance(t, dict) and t.get("fertilizer_available"):
                fertilizer_left_on_tiles += 1
                
    fertilizer_in_shed = priv.get("shed", {}).get("FERTILIZER", 0)
    fertilizer_in_pockets = sum(inv.get("FERTILIZER", 0) for inv in priv.get("inventories", []))
    
    return {
        "collects": collects,
        "applied": ferts_applied,
        "sold": ferts_sold,
        "uncollected_on_tiles": fertilizer_left_on_tiles,
        "left_in_shed": fertilizer_in_shed,
        "left_in_pockets": fertilizer_in_pockets
    }

f_v1 = inspect_fert("candidates/candidate_cl_economic_v1.py", 1000)
f_v2 = inspect_fert("candidates/candidate_cl_economic_v2.py", 1000)
f_frozen = inspect_fert("candidates/slot2_aethel_refined_v2.py", 1000)

print(f"{'Metric':25s} | {'CL-V1':8s} | {'CL-V2':8s} | {'Frozen V2':10s}")
print("-" * 58)
for k in f_v1:
    print(f"{k:25s} | {f_v1[k]:8d} | {f_v2[k]:8d} | {f_frozen[k]:10d}")
