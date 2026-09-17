import json

with open("experiments/EXP-AEC-001/RAW_RESULTS.json", "r") as f:
    raw_results = json.load(f)

lines = []
lines.append("| Seed | Match A AEC | Match A V3 | Delta A | Win A | Match B AEC | Match B V3 | Delta B | Win B | Paired Delta | Commits |")
lines.append("|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")

for seed in range(340000, 340050):
    s_data = raw_results[str(seed)]
    m_a = s_data["match_a"]
    m_b = s_data["match_b"]
    
    aec_a = int(m_a["aec_score"])
    v3_a = int(m_a["ctrl_score"])
    delta_a = aec_a - v3_a
    win_a = m_a["winner"]
    
    aec_b = int(m_b["aec_score"])
    v3_b = int(m_b["ctrl_score"])
    delta_b = aec_b - v3_b
    win_b = m_b["winner"]
    
    paired_d = (delta_a + delta_b) / 2.0
    commits = sum(m_a.get("commits_by_mechanism", {}).values()) + sum(m_b.get("commits_by_mechanism", {}).values())
    
    lines.append(f"| {seed} | {aec_a:,} | {v3_a:,} | {delta_a:+,} | {win_a} | {aec_b:,} | {v3_b:,} | {delta_b:+,} | {win_b} | {paired_d:+.2f} | {commits} |")

with open("scratch/per_seed_table.md", "w") as f:
    f.write("\n".join(lines))

print(f"Generated table with {len(lines)-2} seeds")
