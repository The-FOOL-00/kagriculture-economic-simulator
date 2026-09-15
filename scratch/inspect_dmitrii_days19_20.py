import json

with open("extracted_agents/dmitrii_lb2800/actions.json") as f:
    tapes = json.load(f)

tape0 = tapes[0]

print("=== DMITRII TAPE 0 ACTIONS ON DAYS 19 & 20 ===")

for day in [19, 20]:
    start_step = day * 24
    end_step = start_step + 24
    
    op_counts = {}
    for s in range(start_step, end_step):
        act = tape0[s]
        units = [act.get("farmer", [])] + act.get("hands", [])
        for u_idx, u in enumerate(units):
            if not u: continue
            op = u[0]
            op_counts[op] = op_counts.get(op, 0) + 1
            
    print(f"\nDay {day} (Steps {start_step}..{end_step-1}) Op Counts:")
    for op, cnt in sorted(op_counts.items(), key=lambda x: -x[1]):
        print(f"  {op:<15}: {cnt} actions")
