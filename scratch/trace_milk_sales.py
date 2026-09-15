from kaggle_environments import make

def trace_commodity_sales(agent_path, item="MILK"):
    cfg = {"episodeSteps": 720, "seed": 1004}
    env = make("kaggriculture", configuration=cfg, debug=False)
    env.run([agent_path, "starter"])
    steps = env.steps
    
    events = []
    for step_idx in range(len(steps)):
        act = steps[step_idx][0].get("action", {}) or {}
        obs = steps[step_idx][0].get("observation", {})
        m_state = obs.get("market", {})
        p = m_state.get("prices", {}).get(item, 0)
        inv = m_state.get("inventory", {}).get(item, 0)
        
        for o in act.get("market", []):
            if o[0] == "SELL" and o[1] == item:
                qty = int(o[2])
                events.append((step_idx, step_idx // 24, step_idx % 24, qty, p, inv))
    return events

e1 = trace_commodity_sales("candidates/candidate_cl_economic_v1.py", "MILK")
e2 = trace_commodity_sales("candidates/candidate_cl_economic_v2.py", "MILK")

print("--- CL-Economic-V1 MILK SALES (first 15) ---")
for ev in e1[:15]:
    print(f"Step {ev[0]:3d} (Day {ev[1]:2d}, Hr {ev[2]:2d}): Sold {ev[3]:2d} {ev[4]:.1f}$/u | MktInv={ev[5]}")

print("\n--- CL-Economic-V2 MILK SALES (remaining) ---")
for ev in e2[15:]:
    print(f"Step {ev[0]:3d} (Day {ev[1]:2d}, Hr {ev[2]:2d}): Sold {ev[3]:2d} {ev[4]:.1f}$/u | MktInv={ev[5]}")
