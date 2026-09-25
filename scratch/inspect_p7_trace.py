import json

with open("results/v32_p7_trace_arm1.json") as f:
    t = json.load(f)

t_recs = t["teacher"]["recs"]
p_recs = t["policy"]["recs"]

print(f"{'Step':<4} | {'Teacher Act':<25} {'T_Pos':<8} {'T_Money':<8} | {'Policy Act':<25} {'P_Pos':<8} {'P_Money':<8}")
print("-" * 85)
for i in range(min(25, len(t_recs))):
    tr = t_recs[i]
    pr = p_recs[i]
    t_act = str(tr.get("farmer_act"))
    p_act = str(pr.get("farmer_act"))
    t_pos = str(tr.get("farmer_pos"))
    p_pos = str(pr.get("farmer_pos"))
    t_m = tr.get("money", 0)
    p_m = pr.get("money", 0)
    print(f"{i:<4} | {t_act:<25} {t_pos:<8} {t_m:<8.0f} | {p_act:<25} {p_pos:<8} {p_m:<8.0f}")
