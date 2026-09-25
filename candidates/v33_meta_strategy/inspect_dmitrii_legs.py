import json

with open("route_matchup_matrix.json") as f:
    d = json.load(f)

print("Seed 249677 matches involving Dmitrii:")
for m in d["raw_matches"]:
    if m["seed"] == 249677 and ("R2_DMITRII" in (m["r_left"], m["r_right"])):
        r_l = m["r_left"]
        r_r = m["r_right"]
        p0 = m["p0_cash"]
        p1 = m["p1_cash"]
        w = m["winner"]
        print(f"  {r_l} (${p0:,.0f}) vs {r_r} (${p1:,.0f}) -> {w}")
