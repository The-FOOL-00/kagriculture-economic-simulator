import csv
import json

CSV_PATH = r"c:\Users\Sundareswaran\Kagriculture\experiments\EXP-DEV-002\qualification\QUALIFICATION_PAIRED_DELTAS.csv"

rows = []
with open(CSV_PATH, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for r in reader:
        rows.append(r)

print("### Table 1: All 50 Qualification Seeds")
print("| Seed | Cand Mean Cash | V2 Mean Cash | Paired Margin vs V2 | Match 0 (Cand/V2) | Match 1 (Cand/V2) | Margin vs Dmi | Mode | Unlocked Opening Shops |")
print("| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |")
for r in rows:
    shops = r['unlocked_shops'].split(';')[:3]
    print(f"| {r['seed']} | ${float(r['cand_mean_cash']):,.0f} | ${float(r['v2_mean_cash']):,.0f} | ${float(r['paired_margin_vs_v2']):+,.2f} | ${float(r['cand_m0_cash']):,.0f} / ${float(r['v2_m0_cash']):,.0f} | ${float(r['cand_m1_cash']):,.0f} / ${float(r['v2_m1_cash']):,.0f} | ${float(r['paired_margin_vs_dmi']):+,.2f} | `{r['cand_mode']}` | {', '.join(shops)} |")

print("\n### Table 2: Per-Seed Comparison with DEV-001")
print("| Seed | DEV-001 Delta | DEV-002 Delta | DEV-002 - DEV-001 | Cand Mode | Notes |")
print("| :---: | :---: | :---: | :---: | :---: | :--- |")
for r in rows:
    d1 = float(r['dev001_paired_margin_vs_v2'])
    d2 = float(r['paired_margin_vs_v2'])
    diff = float(r['dev002_minus_dev001'])
    note = "Identical action path" if diff == 0 else "Divergent"
    print(f"| {r['seed']} | ${d1:+,.2f} | ${d2:+,.2f} | ${diff:+,.2f} | `{r['cand_mode']}` | {note} |")
