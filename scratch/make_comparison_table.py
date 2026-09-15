import csv
import json

with open('experiments/EXP-DEV-001/EXP-DEV-001_SHOP_TRAJECTORY_AUDIT.csv', 'r') as f:
    traj = list(csv.DictReader(f))

with open('experiments/EXP-DEV-002/EXP-DEV-002_PAIRED_DELTAS.csv', 'r') as f:
    dev002 = list(csv.DictReader(f))

dev002_map = {int(r['seed']): r for r in dev002}

table_lines = []
table_lines.append("| Seed | EXP-DEV-001 | EXP-DEV-002 | Delta | Shop Pattern (Steps 72, 144) | Treatment Mode | Impact Category |")
table_lines.append("| :---: | :---: | :---: | :---: | :--- | :---: | :--- |")

for row in traj:
    s = int(row['seed'])
    m1 = float(row['paired_margin_vs_v2'])
    m2 = float(dev002_map[s]['margin_vs_v2'])
    delta = m2 - m1
    mode = dev002_map[s]['cand_mode']
    shops = f"{row['shop_step72']} + {row['shop_step144']}"
    
    if s == 50018:
        cat = "**CATASTROPHIC RISK ELIMINATED** (+$6,208 swing)"
    elif s == 50004:
        cat = "**UPSIDE SURRENDERED / TRUNCATED** (-$6,964)"
    elif mode == 'CARROT':
        cat = "Carrot gain retained (+0.00)"
    elif mode == 'WHEAT':
        cat = "Minor wheat loss retained (+0.00)"
    else:
        cat = "Bedrock tie preserved (+0.00)"
        
    table_lines.append(f"| **{s}** | {m1:+.2f} | {m2:+.2f} | {delta:+.2f} | `{shops}` | `{mode}` | {cat} |")

with open('scratch/comparison_table.md', 'w') as f:
    f.write("\n".join(table_lines))

print("Saved comparison table to scratch/comparison_table.md")
